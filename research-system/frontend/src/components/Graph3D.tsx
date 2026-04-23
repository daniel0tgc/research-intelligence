import { useEffect, useRef, useCallback } from 'react'
import ForceGraph3D from '3d-force-graph'
import type { ForceGraph3DInstance } from '3d-force-graph'
import { useGraphStore } from '../store/graph'
import { useAgentStore } from '../store/agent'
import { useUiStore } from '../store/ui'
import type { GraphNode, GraphEdge } from '../types'

const CLUSTER_COLORS = [
  '#6366f1', '#22d3ee', '#f59e0b', '#22c55e',
  '#f43f5e', '#a78bfa', '#fb923c', '#34d399',
  '#60a5fa', '#e879f9', '#fbbf24', '#4ade80',
]

const LINK_COLORS: Record<string, string> = {
  CITES: '#94a3b8',
  SIMILAR_TO: '#22d3ee',
  MENTIONS: '#f59e0b',
  RELATED_TO: '#a78bfa',
}

const LINK_WIDTHS: Record<string, number> = {
  CITES: 1.2,
  SIMILAR_TO: 0.9,
  MENTIONS: 0.5,
  RELATED_TO: 0.5,
}

function nodeColor(node: GraphNode, traversalPath: string[]): string {
  if (traversalPath.includes(node.id)) return '#22d3ee'
  if (node.__type === 'entity') return '#64748b'
  const paper = node as GraphNode & { community_id: number | null }
  const cid = paper.community_id
  if (cid !== null && cid !== undefined) return CLUSTER_COLORS[cid % 12]
  return '#6366f1'
}

function nodeOpacity(node: GraphNode): number {
  if (node.__type === 'entity') return 0.6
  const paper = node as GraphNode & { year: number | null }
  const cutoff = new Date().getFullYear() - 1
  return (paper.year ?? 0) >= cutoff ? 1.0 : 0.5
}

function nodeVal(node: GraphNode): number {
  const degree = (node as GraphNode & { degree?: number }).degree ?? 0
  return 3 + Math.log1p(degree) * 2
}

function nodeLabel(node: GraphNode): string {
  if (node.__type === 'paper') {
    const p = node as GraphNode & { title: string; year: number | null }
    return `${p.title}${p.year ? ` (${p.year})` : ''}`
  }
  const e = node as GraphNode & { name: string; type: string }
  return `${e.name} [${e.type}]`
}

export default function Graph3D() {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<ForceGraph3DInstance | null>(null)

  const { data, selectedNodeId, filteredNodeIds, visibleEdgeTypes, showGraph } = useGraphStore()
  const { traversalPath } = useAgentStore()
  const { setSidePanelOpen } = useUiStore()
  const selectNode = useGraphStore((s) => s.selectNode)

  const handleNodeClick = useCallback(
    (node: object) => {
      const n = node as GraphNode
      selectNode(n.id)
      setSidePanelOpen(true)
    },
    [selectNode, setSidePanelOpen],
  )

  // Initialise graph once on mount
  useEffect(() => {
    if (!containerRef.current) return
    // Must use `new` — ForceGraph3D is a Kapsule constructor, not a factory function
    const graph = new ForceGraph3D(containerRef.current, { controlType: 'orbit' })
      .backgroundColor('#0a0a0f')
      .showNavInfo(false)
      .nodeLabel((n) => nodeLabel(n as GraphNode))
      .nodeColor((n) => nodeColor(n as GraphNode, []))
      .nodeVal((n) => nodeVal(n as GraphNode))
      .nodeOpacity(0.85)
      .linkColor((l) => {
        const edge = l as GraphEdge
        return LINK_COLORS[edge.type] ?? '#475569'
      })
      .linkWidth((l) => {
        const edge = l as GraphEdge
        return LINK_WIDTHS[edge.type] ?? 0.5
      })
      .linkOpacity(0.6)
      .enableNodeDrag(false)
      .onNodeClick(handleNodeClick)

    graphRef.current = graph

    return () => {
      graph._destructor()
      graphRef.current = null
    }
  }, [handleNodeClick])

  // Update graph data and filters when store changes
  useEffect(() => {
    const graph = graphRef.current
    if (!graph) return

    const visibleNodes = filteredNodeIds
      ? data.nodes.filter((n) => filteredNodeIds.has(n.id))
      : data.nodes

    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id))
    const visibleEdges = data.edges.filter(
      (e) =>
        visibleEdgeTypes.has(e.type) &&
        visibleNodeIds.has(e.source) &&
        visibleNodeIds.has(e.target),
    )

    // Compute degree from visible edges
    const degreeMap = new Map<string, number>()
    for (const e of visibleEdges) {
      degreeMap.set(e.source, (degreeMap.get(e.source) ?? 0) + 1)
      degreeMap.set(e.target, (degreeMap.get(e.target) ?? 0) + 1)
    }
    const nodesWithDegree = visibleNodes.map((n) => ({
      ...n,
      degree: degreeMap.get(n.id) ?? 0,
    }))

    graph.graphData({
      nodes: nodesWithDegree as object[],
      links: visibleEdges.map((e) => ({ ...e, source: e.source, target: e.target })),
    })

    graph
      .nodeColor((n) => nodeColor(n as GraphNode, traversalPath))
      .nodeVal((n) => nodeVal(n as GraphNode))
  }, [data, filteredNodeIds, visibleEdgeTypes, traversalPath])

  // Update selected node highlight
  useEffect(() => {
    const graph = graphRef.current
    if (!graph) return
    graph.nodeColor((n) => {
      const node = n as GraphNode
      if (node.id === selectedNodeId) return '#ffffff'
      return nodeColor(node, traversalPath)
    })
  }, [selectedNodeId, traversalPath])

  return (
    <div
      ref={containerRef}
      style={{
        position: 'absolute',
        inset: 0,
        display: showGraph ? 'block' : 'none',
      }}
    />
  )
}

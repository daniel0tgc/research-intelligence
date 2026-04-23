import { create } from 'zustand'
import type { GraphData } from '../types'

interface GraphStore {
  data: GraphData
  selectedNodeId: string | null
  filteredNodeIds: Set<string> | null // null = show all
  visibleEdgeTypes: Set<string>
  yearRange: [number, number]
  showGraph: boolean
  setData: (data: GraphData) => void
  selectNode: (id: string | null) => void
  setFilter: (nodeIds: Set<string> | null) => void
  toggleEdgeType: (type: string) => void
  setYearRange: (range: [number, number]) => void
  toggleGraph: () => void
}

export const useGraphStore = create<GraphStore>((set) => ({
  data: { nodes: [], edges: [] },
  selectedNodeId: null,
  filteredNodeIds: null,
  visibleEdgeTypes: new Set(['CITES', 'SIMILAR_TO', 'MENTIONS', 'RELATED_TO']),
  yearRange: [1990, new Date().getFullYear()],
  showGraph: true,
  setData: (data) => set({ data }),
  selectNode: (id) => set({ selectedNodeId: id }),
  setFilter: (nodeIds) => set({ filteredNodeIds: nodeIds }),
  toggleEdgeType: (type) =>
    set((s) => {
      const next = new Set(s.visibleEdgeTypes)
      next.has(type) ? next.delete(type) : next.add(type)
      return { visibleEdgeTypes: next }
    }),
  setYearRange: (range) => set({ yearRange: range }),
  toggleGraph: () => set((s) => ({ showGraph: !s.showGraph })),
}))

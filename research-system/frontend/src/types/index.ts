export interface PaperNode {
  id: string
  title: string
  year: number | null
  is_read: boolean
  community_id: number | null
  degree?: number // computed client-side from edges
}

export interface EntityNode {
  id: string
  name: string
  type: 'Method' | 'Dataset' | 'Claim' | 'Concept' | 'Architecture'
}

export type GraphNode = (PaperNode | EntityNode) & {
  __type: 'paper' | 'entity'
  x?: number
  y?: number
  z?: number // set by force layout
}

export interface GraphEdge {
  source: string
  target: string
  type: 'CITES' | 'SIMILAR_TO' | 'MENTIONS' | 'RELATED_TO'
  weight: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface PaperDetail extends PaperNode {
  abstract: string
  authors: string[]
}

export interface ConceptMapping {
  id: string
  term_a: string
  term_b: string
  status: 'pending' | 'approved' | 'rejected'
}

export interface PaperCard {
  id: string
  title: string
  authors: string[]
  year: number | null
  abstract: string
  is_read: boolean
  arxiv_url: string | null
  semantic_scholar_url: string | null
  top_connections: Array<{ title: string }>
  community_label: string | null
}

export interface AgentEvent {
  type: string
  agent?: string
  paper_id?: string
  step?: string
  report_path?: string
}

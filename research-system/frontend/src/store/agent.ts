import { create } from 'zustand'
import type { AgentEvent } from '../types'

interface AgentStore {
  isRunning: boolean
  currentAgent: string | null
  traversalPath: string[] // node IDs being visited
  lastEvent: AgentEvent | null
  graphRefreshToken: number // bumped when graph data should be reloaded
  handleEvent: (event: AgentEvent) => void
}

export const useAgentStore = create<AgentStore>((set) => ({
  isRunning: false,
  currentAgent: null,
  traversalPath: [],
  lastEvent: null,
  graphRefreshToken: 0,
  handleEvent: (event) =>
    set((s) => {
      if (event.type === 'agent_start') {
        return { isRunning: true, currentAgent: event.agent ?? null, traversalPath: [] }
      }
      if (event.type === 'agent_done') {
        return { isRunning: false, currentAgent: null, traversalPath: [] }
      }
      if (event.type === 'agent_step' && event.paper_id) {
        return { traversalPath: [...s.traversalPath, event.paper_id] }
      }
      // Bump token whenever a paper finishes ingesting so App.tsx reloads the graph
      if (event.type === 'paper_ingested') {
        return { lastEvent: event, graphRefreshToken: s.graphRefreshToken + 1 }
      }
      return { lastEvent: event }
    }),
}))

import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useGraphStore } from './store/graph'
import { useUiStore } from './store/ui'
import { useAgentStore } from './store/agent'
import { initSocket } from './lib/socket'
import { getFullGraph, getLatestGapReport, triggerGapAgent } from './lib/api'
import Graph3D from './components/Graph3D'
import SearchBar from './components/SearchBar'
import FilterPanel from './components/FilterPanel'
import SidePanel from './components/SidePanel'
import ChatDrawer from './components/ChatDrawer'
import AgendaView from './components/AgendaView'
import ConceptQueue from './components/ConceptQueue'
import IngestBar from './components/IngestBar'

const NAV_ITEMS = [
  { id: 'graph', label: 'Graph' },
  { id: 'agenda', label: 'Agenda' },
  { id: 'gaps', label: 'Gaps' },
  { id: 'concepts', label: 'Concepts' },
] as const

type ActiveView = 'graph' | 'agenda' | 'gaps' | 'concepts'

function GapsView() {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)

  useEffect(() => {
    getLatestGapReport()
      .then((c) => {
        setContent(c)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const handleTrigger = async () => {
    setTriggering(true)
    try {
      await triggerGapAgent()
    } finally {
      setTriggering(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-textPrimary text-lg font-semibold">Research Gap Report</h1>
        <button
          onClick={() => void handleTrigger()}
          disabled={triggering}
          className="text-xs bg-primary text-white rounded-card px-3 py-1.5
                     hover:bg-primary/80 transition-colors disabled:opacity-40"
        >
          {triggering ? 'Running…' : 'Run Gap Agent'}
        </button>
      </div>
      {loading && <p className="text-textMuted text-sm">Loading…</p>}
      {!loading && !content && (
        <p className="text-textMuted text-sm">
          No gap report yet. Run the gap agent to generate one.
        </p>
      )}
      {!loading && content && (
        <div
          className="bg-surface border border-border rounded-card p-4 prose prose-invert max-w-none
                     [&_h2]:text-primary [&_h2]:text-base [&_h3]:text-accent [&_h3]:text-sm
                     [&_p]:text-textPrimary [&_p]:text-sm [&_li]:text-sm"
        >
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const setData = useGraphStore((s) => s.setData)
  const { activeView, setActiveView } = useUiStore()
  const graphRefreshToken = useAgentStore((s) => s.graphRefreshToken)

  // Initial load + re-fetch whenever a paper_ingested event fires
  useEffect(() => {
    initSocket()

    let cancelled = false
    const load = (attempt: number) => {
      getFullGraph()
        .then((data) => { if (!cancelled) setData(data) })
        .catch((err: unknown) => {
          console.error(`[App] getFullGraph attempt ${attempt} failed:`, err)
          if (!cancelled && attempt < 5) {
            setTimeout(() => load(attempt + 1), 3000)
          }
        })
    }
    load(1)

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setData, graphRefreshToken])

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-background text-textPrimary">
      {/* 3D graph — always mounted, hidden via showGraph state when needed */}
      <Graph3D />

      {/* IngestBar — always mounted so the ingestion timer persists across views */}
      <IngestBar />

      {/* Remaining graph-only overlays */}
      {activeView === 'graph' && (
        <>
          <SearchBar />
          <FilterPanel />
          <SidePanel />
          <ChatDrawer />
        </>
      )}

      {/* Non-graph full-screen views */}
      {activeView !== 'graph' && (
        <div className="absolute inset-0 pt-12 bg-background overflow-hidden">
          {activeView === 'agenda' && <AgendaView />}
          {activeView === 'concepts' && <ConceptQueue />}
          {activeView === 'gaps' && <GapsView />}
        </div>
      )}

      {/* Navigation tabs — top right */}
      <nav className="absolute top-4 right-4 z-40 flex items-center gap-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id as ActiveView)}
            className={`px-3 py-1.5 rounded-card text-xs font-medium transition-colors
                        ${
                          activeView === item.id
                            ? 'bg-primary text-white'
                            : 'bg-surface text-textMuted hover:text-textPrimary border border-border'
                        }`}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

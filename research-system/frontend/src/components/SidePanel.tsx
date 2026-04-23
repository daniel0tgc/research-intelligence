import { useEffect, useState } from 'react'
import { useGraphStore } from '../store/graph'
import { useUiStore } from '../store/ui'
import { getPaperCard, markAsRead, getConnectionReport } from '../lib/api'
import type { PaperCard } from '../types'

export default function SidePanel() {
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId)
  const { sidePanelOpen, setSidePanelOpen, setChatOpen } = useUiStore()

  const [card, setCard] = useState<PaperCard | null>(null)
  const [loading, setLoading] = useState(false)
  const [isRead, setIsRead] = useState(false)
  const [reportExpanded, setReportExpanded] = useState(false)
  const [report, setReport] = useState<string | null>(null)
  const [loadingReport, setLoadingReport] = useState(false)

  const close = () => setSidePanelOpen(false)

  useEffect(() => {
    if (!selectedNodeId || !sidePanelOpen) return
    setCard(null)
    setReport(null)
    setReportExpanded(false)
    setLoading(true)

    getPaperCard(selectedNodeId)
      .then((c) => {
        setCard(c)
        setIsRead(c.is_read)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [selectedNodeId, sidePanelOpen])

  const handleMarkRead = async () => {
    if (!selectedNodeId) return
    try {
      await markAsRead(selectedNodeId)
      setIsRead(true)
    } catch {
      // non-fatal
    }
  }

  const handleExpandReport = async () => {
    if (report !== null) {
      setReportExpanded((v) => !v)
      return
    }
    setReportExpanded(true)
    setLoadingReport(true)
    try {
      const r = await getConnectionReport(selectedNodeId!)
      setReport(r)
    } catch {
      setReport('')
    } finally {
      setLoadingReport(false)
    }
  }

  if (!sidePanelOpen) return null

  return (
    <>
      <div className="absolute inset-0 z-10" onClick={close} aria-label="Close panel" />

      <div className="absolute right-0 top-0 bottom-0 w-80 bg-surface border-l border-border z-20 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <span className="text-xs text-textMuted uppercase tracking-wider font-medium">Paper</span>
          <button
            onClick={close}
            title="Close"
            className="flex items-center justify-center w-7 h-7 rounded bg-elevated hover:bg-border text-textMuted hover:text-textPrimary transition-colors text-sm font-bold leading-none"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading && <p className="text-textMuted text-sm">Loading…</p>}
          {!loading && !card && <p className="text-textMuted text-sm">Select a paper node.</p>}

          {card && (
            <>
              {/* Title */}
              <div>
                <h2 className="text-textPrimary font-semibold text-sm leading-snug">{card.title}</h2>
                <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
                  {card.year && <span className="text-textMuted text-xs">{card.year}</span>}
                  {card.authors.length > 0 && (
                    <span className="text-textMuted text-xs truncate max-w-[220px]">
                      {card.authors.slice(0, 3).join(', ')}
                      {card.authors.length > 3 ? ' et al.' : ''}
                    </span>
                  )}
                </div>
              </div>

              {/* Badges row */}
              <div className="flex flex-wrap items-center gap-2">
                {card.community_label && (
                  <span className="text-xs bg-accent/10 text-accent rounded-full px-2 py-0.5">
                    {card.community_label}
                  </span>
                )}
                {isRead ? (
                  <span className="text-xs text-green-400 bg-green-400/10 rounded-full px-2 py-0.5">
                    ✓ Read
                  </span>
                ) : (
                  <button
                    onClick={handleMarkRead}
                    className="text-xs bg-primary/10 text-primary hover:bg-primary/20 rounded-full px-2 py-0.5 transition-colors"
                  >
                    Mark as read
                  </button>
                )}
              </div>

              {/* External links */}
              {(card.arxiv_url || card.semantic_scholar_url) && (
                <div className="flex flex-wrap gap-2">
                  {card.arxiv_url && (
                    <a
                      href={card.arxiv_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-accent hover:underline"
                    >
                      ArXiv / DOI ↗
                    </a>
                  )}
                  {card.semantic_scholar_url && (
                    <a
                      href={card.semantic_scholar_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-textMuted hover:text-textPrimary hover:underline"
                    >
                      Semantic Scholar ↗
                    </a>
                  )}
                </div>
              )}

              {/* Abstract — 3 lines clamped */}
              {card.abstract && (
                <div>
                  <h3 className="text-xs text-textMuted uppercase tracking-wider mb-1">Summary</h3>
                  <p className="text-textPrimary text-xs leading-relaxed line-clamp-4">
                    {card.abstract}
                  </p>
                </div>
              )}

              {/* Top connections */}
              {card.top_connections.length > 0 && (
                <div>
                  <h3 className="text-xs text-textMuted uppercase tracking-wider mb-2">
                    Related Papers
                  </h3>
                  <ul className="space-y-1.5">
                    {card.top_connections.map((c, i) => (
                      <li key={i} className="text-xs text-textPrimary leading-snug pl-2 border-l border-border">
                        {c.title}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Ask agent */}
              <button
                onClick={() => setChatOpen(true)}
                className="w-full py-2 rounded-card bg-primary text-white text-sm font-medium hover:bg-primary/80 transition-colors"
              >
                Ask agent about this paper
              </button>

              {/* Full analysis — collapsible */}
              <div>
                <button
                  onClick={() => void handleExpandReport()}
                  className="w-full flex items-center justify-between text-xs text-textMuted hover:text-textPrimary transition-colors py-1"
                >
                  <span className="uppercase tracking-wider">Full Analysis</span>
                  <span>{reportExpanded ? '▲' : '▼'}</span>
                </button>
                {reportExpanded && (
                  <div className="mt-2 border-t border-border pt-2">
                    {loadingReport && <p className="text-textMuted text-xs">Loading…</p>}
                    {!loadingReport && !report && (
                      <p className="text-textMuted text-xs">No report yet.</p>
                    )}
                    {!loadingReport && report && (
                      <pre className="text-xs text-textPrimary whitespace-pre-wrap leading-relaxed font-sans">
                        {report}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}

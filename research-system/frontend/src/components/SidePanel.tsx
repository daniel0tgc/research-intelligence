import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useGraphStore } from '../store/graph'
import { useUiStore } from '../store/ui'
import { getPaper, getConnectionReport, markAsRead } from '../lib/api'
import type { PaperDetail } from '../types'

export default function SidePanel() {
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId)
  const { sidePanelOpen, setSidePanelOpen, setChatOpen } = useUiStore()

  const [paper, setPaper] = useState<PaperDetail | null>(null)
  const [report, setReport] = useState<string | null>(null)
  const [loadingPaper, setLoadingPaper] = useState(false)
  const [loadingReport, setLoadingReport] = useState(false)
  const [isRead, setIsRead] = useState(false)

  const close = () => setSidePanelOpen(false)

  useEffect(() => {
    if (!selectedNodeId || !sidePanelOpen) return
    setPaper(null)
    setReport(null)
    setLoadingPaper(true)

    getPaper(selectedNodeId)
      .then((p) => {
        setPaper(p)
        setIsRead(p.is_read)
        setLoadingPaper(false)
        setLoadingReport(true)
        return getConnectionReport(selectedNodeId)
      })
      .then((r) => {
        setReport(r)
        setLoadingReport(false)
      })
      .catch(() => {
        setLoadingPaper(false)
        setLoadingReport(false)
      })
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

  if (!sidePanelOpen) return null

  return (
    <>
      {/* Clickable backdrop — click anywhere outside the panel to close */}
      <div
        className="absolute inset-0 z-10"
        onClick={close}
        aria-label="Close panel"
      />

      {/* Panel */}
      <div
        className="absolute right-0 top-0 bottom-0 w-80 bg-surface border-l border-border
                   z-20 flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <span className="text-xs text-textMuted uppercase tracking-wider font-medium">
            Paper Details
          </span>
          <button
            onClick={close}
            title="Close"
            className="flex items-center justify-center w-7 h-7 rounded
                       bg-elevated hover:bg-border text-textMuted hover:text-textPrimary
                       transition-colors text-sm font-bold leading-none"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loadingPaper && (
            <p className="text-textMuted text-sm">Loading…</p>
          )}

          {!loadingPaper && !paper && (
            <p className="text-textMuted text-sm">Select a paper node.</p>
          )}

          {paper && (
            <>
              {/* Title + meta */}
              <div>
                <h2 className="text-textPrimary font-semibold text-sm leading-snug">
                  {paper.title}
                </h2>
                {paper.authors?.length > 0 && (
                  <p className="text-textMuted text-xs mt-1">{paper.authors.join(', ')}</p>
                )}
                {paper.year && (
                  <p className="text-textMuted text-xs">{paper.year}</p>
                )}
                <div className="mt-2 flex items-center gap-2">
                  {isRead ? (
                    <span className="inline-flex items-center gap-1 text-xs text-green-400 bg-green-400/10 rounded px-2 py-0.5">
                      ✓ Read
                    </span>
                  ) : (
                    <button
                      onClick={handleMarkRead}
                      className="text-xs bg-primary/10 text-primary hover:bg-primary/20 rounded px-2 py-0.5 transition-colors"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </div>

              {/* Abstract */}
              {paper.abstract && (
                <div>
                  <h3 className="text-xs text-textMuted uppercase tracking-wider mb-1">Abstract</h3>
                  <p className="text-textPrimary text-xs leading-relaxed line-clamp-6">
                    {paper.abstract}
                  </p>
                </div>
              )}

              {/* Ask agent */}
              <button
                onClick={() => setChatOpen(true)}
                className="w-full py-2 rounded-card bg-primary text-white text-sm font-medium
                           hover:bg-primary/80 transition-colors"
              >
                Ask agent about this paper
              </button>

              {/* Connection report */}
              <div>
                <h3 className="text-xs text-textMuted uppercase tracking-wider mb-2">
                  Connection Report
                </h3>
                {loadingReport && (
                  <p className="text-textMuted text-xs">Loading report…</p>
                )}
                {!loadingReport && !report && (
                  <p className="text-textMuted text-xs">
                    No report yet — report is generated after ingestion completes.
                  </p>
                )}
                {!loadingReport && report && (
                  <div className="prose prose-invert prose-xs max-w-none text-textPrimary
                                  [&_h2]:text-sm [&_h3]:text-xs [&_p]:text-xs [&_li]:text-xs
                                  [&_h2]:text-primary [&_h3]:text-accent">
                    <ReactMarkdown>{report}</ReactMarkdown>
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

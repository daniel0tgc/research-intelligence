import { useEffect, useState } from 'react'
import { getPendingConcepts, approveConcept, rejectConcept } from '../lib/api'
import type { ConceptMapping } from '../types'

export default function ConceptQueue() {
  const [concepts, setConcepts] = useState<ConceptMapping[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [processing, setProcessing] = useState<string | null>(null)
  const [toast, setToast] = useState<{ id: string; msg: string } | null>(null)

  useEffect(() => {
    getPendingConcepts()
      .then((data) => { setConcepts(data); setLoading(false) })
      .catch(() => { setError(true); setLoading(false) })
  }, [])

  const showToast = (msg: string) => {
    const id = Math.random().toString(36).slice(2)
    setToast({ id, msg })
    setTimeout(() => setToast((t) => (t?.id === id ? null : t)), 3500)
  }

  const handleApprove = async (id: string, termA: string, termB: string) => {
    setProcessing(id)
    setActionError(null)
    try {
      await approveConcept(id)
      setConcepts((prev) => prev.filter((c) => c.id !== id))
      showToast(`Merged "${termB}" → "${termA}" in knowledge graph`)
    } catch (e) {
      setActionError(`Failed to approve: ${e instanceof Error ? e.message : 'Unknown error'}`)
    } finally {
      setProcessing(null)
    }
  }

  const handleReject = async (id: string) => {
    setProcessing(id)
    setActionError(null)
    try {
      await rejectConcept(id)
      setConcepts((prev) => prev.filter((c) => c.id !== id))
    } catch (e) {
      setActionError(`Failed to reject: ${e instanceof Error ? e.message : 'Unknown error'}`)
    } finally {
      setProcessing(null)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-textPrimary text-lg font-semibold">Concept Normalization Queue</h1>
        {concepts.length > 0 && (
          <span className="text-xs text-textMuted bg-surface border border-border rounded px-2 py-0.5">
            {concepts.length} pending
          </span>
        )}
      </div>
      <p className="text-textMuted text-sm">
        Synonym pairs suggested during ingestion. Approving merges the right-hand entity into the
        left-hand entity across the entire knowledge graph.
      </p>

      {actionError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-card p-3 text-red-400 text-sm">
          {actionError}
        </div>
      )}

      {loading && <p className="text-textMuted text-sm">Loading…</p>}
      {error && <p className="text-red-400 text-sm">Failed to load concepts — is the backend running?</p>}

      {!loading && !error && concepts.length === 0 && (
        <div className="bg-surface border border-border rounded-card p-6 text-center">
          <p className="text-textMuted text-sm">No pending concept mappings.</p>
        </div>
      )}

      {concepts.map((c) => (
        <div
          key={c.id}
          className="bg-surface border border-border rounded-card p-4 flex items-center justify-between gap-4"
        >
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-textPrimary text-sm font-medium truncate">{c.term_a}</span>
            <span className="text-accent text-xs shrink-0">←</span>
            <span className="text-textMuted text-sm truncate line-through decoration-textMuted/40">{c.term_b}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              disabled={processing === c.id}
              onClick={() => void handleApprove(c.id, c.term_a, c.term_b)}
              className="text-xs bg-green-500/10 text-green-400 hover:bg-green-500/20
                         disabled:opacity-40 disabled:cursor-not-allowed
                         rounded px-2.5 py-1 transition-colors"
            >
              {processing === c.id ? '…' : 'Merge'}
            </button>
            <button
              disabled={processing === c.id}
              onClick={() => void handleReject(c.id)}
              className="text-xs bg-surface text-textMuted hover:text-textPrimary hover:bg-elevated
                         disabled:opacity-40 disabled:cursor-not-allowed
                         rounded px-2.5 py-1 transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      ))}

      {toast && (
        <div className="fixed bottom-6 right-6 bg-elevated border border-border rounded-card
                        px-4 py-2.5 text-sm text-textPrimary shadow-lg z-50 animate-pulse-once">
          {toast.msg}
        </div>
      )}
    </div>
  )
}

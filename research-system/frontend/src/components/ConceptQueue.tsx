import { useEffect, useState } from 'react'
import { getPendingConcepts, approveConcept, rejectConcept } from '../lib/api'
import type { ConceptMapping } from '../types'

export default function ConceptQueue() {
  const [concepts, setConcepts] = useState<ConceptMapping[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    getPendingConcepts()
      .then((data) => {
        setConcepts(data)
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }, [])

  const handleApprove = async (id: string) => {
    try {
      await approveConcept(id)
      setConcepts((prev) => prev.filter((c) => c.id !== id))
    } catch {
      // non-fatal
    }
  }

  const handleReject = async (id: string) => {
    try {
      await rejectConcept(id)
      setConcepts((prev) => prev.filter((c) => c.id !== id))
    } catch {
      // non-fatal
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto space-y-4">
      <h1 className="text-textPrimary text-lg font-semibold">Concept Normalization Queue</h1>
      <p className="text-textMuted text-sm">
        These synonym pairs were suggested by the AI during ingestion. Approve to merge them in the
        knowledge graph, reject to dismiss.
      </p>

      {loading && <p className="text-textMuted text-sm">Loading…</p>}
      {error && <p className="text-textMuted text-sm">Failed to load concepts.</p>}

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
            <span className="text-accent text-xs shrink-0">↔</span>
            <span className="text-textPrimary text-sm font-medium truncate">{c.term_b}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => void handleApprove(c.id)}
              className="text-xs bg-green-500/10 text-green-400 hover:bg-green-500/20
                         rounded px-2.5 py-1 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => void handleReject(c.id)}
              className="text-xs bg-red-500/10 text-red-400 hover:bg-red-500/20
                         rounded px-2.5 py-1 transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { getAgenda, updatePriorities } from '../lib/api'

export default function AgendaView() {
  const [agenda, setAgenda] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [priorities, setPriorities] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setLoading(true)
    getAgenda()
      .then((a) => {
        setAgenda(a)
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }, [])

  const handleSavePriorities = async () => {
    if (!priorities.trim()) return
    setSaving(true)
    try {
      await updatePriorities(priorities)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      // non-fatal
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-textPrimary text-lg font-semibold">Weekly Research Agenda</h1>

      {/* Update priorities */}
      <div className="bg-surface border border-border rounded-card p-4 space-y-2">
        <label className="text-xs text-textMuted uppercase tracking-wider">
          Current Research Priorities
        </label>
        <textarea
          value={priorities}
          onChange={(e) => setPriorities(e.target.value)}
          rows={3}
          placeholder="Describe your current research focus..."
          className="w-full bg-elevated border border-border rounded-card px-3 py-2 text-sm
                     text-textPrimary placeholder-textMuted outline-none resize-none
                     focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
        />
        <button
          onClick={() => void handleSavePriorities()}
          disabled={saving || !priorities.trim()}
          className="text-xs bg-primary text-white rounded-card px-3 py-1.5
                     hover:bg-primary/80 transition-colors disabled:opacity-40"
        >
          {saved ? 'Saved ✓' : saving ? 'Saving…' : 'Save Priorities'}
        </button>
      </div>

      {/* Agenda */}
      <div className="bg-surface border border-border rounded-card p-4">
        {loading && <p className="text-textMuted text-sm">Generating agenda…</p>}
        {error && <p className="text-textMuted text-sm">Failed to load agenda.</p>}
        {!loading && !error && agenda && (
          <div className="prose prose-invert max-w-none
                         [&_h2]:text-primary [&_h2]:text-base
                         [&_h3]:text-accent [&_h3]:text-sm
                         [&_p]:text-textPrimary [&_p]:text-sm
                         [&_li]:text-textPrimary [&_li]:text-sm">
            <ReactMarkdown>{agenda}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

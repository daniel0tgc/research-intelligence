import { useState, useRef, useCallback } from 'react'
import { searchGraph } from '../lib/api'
import { useGraphStore } from '../store/graph'

export default function SearchBar() {
  const [query, setQuery] = useState('')
  const [resultCount, setResultCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchError, setSearchError] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const setFilter = useGraphStore((s) => s.setFilter)

  const runSearch = useCallback(
    async (q: string) => {
      if (!q.trim()) {
        setFilter(null)
        setResultCount(null)
        return
      }
    setLoading(true)
    setSearchError(false)
    try {
      const results = await searchGraph(q)
      const ids = new Set(results.map((p) => p.id))
      setFilter(ids)
      setResultCount(results.length)
    } catch {
      setSearchError(true)
      setResultCount(null)
    } finally {
      setLoading(false)
    }
    },
    [setFilter],
  )

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setQuery(val)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => runSearch(val), 300)
  }

  const handleClear = () => {
    setQuery('')
    setFilter(null)
    setResultCount(null)
    setSearchError(false)
    if (debounceRef.current) clearTimeout(debounceRef.current)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (debounceRef.current) clearTimeout(debounceRef.current)
    void runSearch(query)
  }

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 w-[480px] z-10">
      <form onSubmit={handleSubmit}>
        <div className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={handleChange}
            placeholder="Search papers, concepts, methods..."
            className="w-full bg-surface border border-border rounded-card px-4 py-2.5 pr-10
                       text-textPrimary placeholder-textMuted text-sm outline-none
                       focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 text-textMuted hover:text-textPrimary transition-colors"
            >
              ✕
            </button>
          )}
        </div>
      </form>

      {loading && (
        <p className="mt-1 text-xs text-textMuted text-center">Searching…</p>
      )}
      {!loading && searchError && (
        <p className="mt-1 text-xs text-red-400 text-center">
          Search unavailable — embedding rate-limited, try again in 20s
        </p>
      )}
      {!loading && !searchError && resultCount !== null && (
        <p className="mt-1 text-xs text-textMuted text-center">
          {resultCount} paper{resultCount !== 1 ? 's' : ''} match
        </p>
      )}
    </div>
  )
}

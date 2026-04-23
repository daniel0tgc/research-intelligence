import { useState, useRef, useEffect } from 'react'
import { ingestArxiv, ingestUrl, ingestGithub, ingestPdf } from '../lib/api'
import { useAgentStore } from '../store/agent'

type IngestMode = 'arxiv' | 'url' | 'github' | 'pdf'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error'
}

const PLACEHOLDERS: Record<IngestMode, string> = {
  arxiv: 'e.g. 1706.03762',
  url: 'https://example.com/paper.pdf',
  github: 'https://github.com/org/repo',
  pdf: '',
}

const STEP_LABELS: Record<string, string> = {
  extracting: 'Extracting text…',
  embedding: 'Embedding chunks…',
  extracting_entities: 'Extracting entities…',
  complete: 'Complete!',
}

let toastCounter = 0

function useElapsedTimer(running: boolean) {
  const [elapsed, setElapsed] = useState(0)
  const startRef = useRef<number | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (running) {
      startRef.current = Date.now()
      setElapsed(0)
      intervalRef.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - (startRef.current ?? Date.now())) / 1000))
      }, 1000)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [running])

  return elapsed
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`
}

export default function IngestBar() {
  const [mode, setMode] = useState<IngestMode>('arxiv')
  const [input, setInput] = useState('')
  const [queuing, setQueuing] = useState(false)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)
  const [ingesting, setIngesting] = useState(false)
  const [currentStep, setCurrentStep] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const lastEvent = useAgentStore((s) => s.lastEvent)
  const elapsed = useElapsedTimer(ingesting)

  // Watch WebSocket events for ingestion progress
  useEffect(() => {
    if (!lastEvent) return
    if (lastEvent.type === 'ingestion_step') {
      const step = (lastEvent as { step?: string }).step ?? null
      setCurrentStep(step)
      setIngesting(true)
    } else if (lastEvent.type === 'paper_ingested') {
      setCurrentStep('complete')
      // Keep ingesting=true briefly to show "Complete!" then clear
      setTimeout(() => {
        setIngesting(false)
        setCurrentStep(null)
      }, 3000)
    }
  }, [lastEvent])

  const addToast = (message: string, type: 'success' | 'error') => {
    const id = ++toastCounter
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000)
  }

  const handleIngest = async () => {
    if (queuing) return
    setQueuing(true)
    setIngesting(false)
    setCurrentStep(null)
    try {
      if (mode === 'arxiv') {
        await ingestArxiv(input.trim())
        addToast(`ArXiv ${input.trim()} queued`, 'success')
        setInput('')
        setIngesting(true)
      } else if (mode === 'url') {
        await ingestUrl(input.trim())
        addToast('URL queued for ingestion', 'success')
        setInput('')
        setIngesting(true)
      } else if (mode === 'github') {
        await ingestGithub(input.trim())
        addToast('GitHub repo queued', 'success')
        setInput('')
        setIngesting(true)
      } else if (mode === 'pdf') {
        const file = fileRef.current?.files?.[0]
        if (!file) {
          addToast('No file selected', 'error')
          return
        }
        await ingestPdf(file)
        addToast(`${file.name} queued`, 'success')
        setSelectedFileName(null)
        if (fileRef.current) fileRef.current.value = ''
        setIngesting(true)
      }
    } catch {
      addToast('Ingestion failed — check console', 'error')
      setIngesting(false)
    } finally {
      setQueuing(false)
    }
  }

  const canSubmit = mode === 'pdf' ? !!selectedFileName : !!input.trim()

  return (
    <>
      {/* Ingest bar — top left */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          {/* Mode selector */}
          <select
            value={mode}
            onChange={(e) => {
              setMode(e.target.value as IngestMode)
              setInput('')
              setSelectedFileName(null)
            }}
            className="bg-surface border border-border rounded-card px-2 py-2 text-xs
                       text-textPrimary outline-none focus:ring-2 focus:ring-primary shrink-0"
          >
            <option value="arxiv">ArXiv ID</option>
            <option value="url">PDF URL</option>
            <option value="github">GitHub</option>
            <option value="pdf">PDF Upload</option>
          </select>

          {/* Text input (arxiv / url / github) */}
          {mode !== 'pdf' && (
            <input
              key="text-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={PLACEHOLDERS[mode]}
              onKeyDown={(e) => { if (e.key === 'Enter' && canSubmit) void handleIngest() }}
              className="bg-surface border border-border rounded-card px-3 py-2 text-xs w-48
                         text-textPrimary placeholder-textMuted outline-none
                         focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
            />
          )}

          {/* PDF file input — hidden native input + styled label */}
          {mode === 'pdf' && (
            <div key="file-input" className="flex items-center gap-1.5">
              <label
                htmlFor="pdf-upload"
                className="cursor-pointer bg-surface border border-border rounded-card
                           px-3 py-2 text-xs text-textMuted hover:text-textPrimary
                           hover:border-primary transition-colors whitespace-nowrap"
              >
                {selectedFileName ? (
                  <span className="text-accent truncate max-w-32 block">{selectedFileName}</span>
                ) : (
                  'Choose PDF…'
                )}
              </label>
              <input
                id="pdf-upload"
                ref={fileRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  setSelectedFileName(file?.name ?? null)
                }}
              />
            </div>
          )}

          <button
            onClick={() => void handleIngest()}
            disabled={queuing || !canSubmit}
            className="bg-primary text-white rounded-card px-3 py-2 text-xs font-medium
                       hover:bg-primary/80 transition-colors disabled:opacity-40
                       disabled:cursor-not-allowed shrink-0"
          >
            {queuing ? '…' : 'Ingest'}
          </button>
        </div>

        {/* Ingestion progress timer */}
        {ingesting && (
          <div className="bg-surface border border-border rounded-card px-3 py-2
                          flex items-center gap-3 text-xs">
            {currentStep === 'complete' ? (
              <>
                <span className="w-2 h-2 rounded-full bg-green-400 shrink-0" />
                <span className="text-green-400 font-medium">Complete!</span>
                <span className="text-textMuted ml-auto">{formatTime(elapsed)}</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-accent animate-pulse shrink-0" />
                <span className="text-accent">
                  {currentStep ? (STEP_LABELS[currentStep] ?? currentStep) : 'Queued…'}
                </span>
                <span className="text-textMuted font-mono ml-auto tabular-nums">
                  {formatTime(elapsed)}
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Toast container — bottom right */}
      <div className="absolute bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-4 py-2.5 rounded-card text-xs font-medium shadow-lg
                        ${t.type === 'success'
                          ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                          : 'bg-red-500/10 text-red-400 border border-red-500/20'
                        }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </>
  )
}

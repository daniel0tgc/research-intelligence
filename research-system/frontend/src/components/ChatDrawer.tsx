import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { useUiStore } from '../store/ui'
import { useGraphStore } from '../store/graph'
import { streamChat } from '../lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatDrawer() {
  const { chatOpen, setChatOpen } = useUiStore()
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId)

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const accRef = useRef('')
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const flushAccumulator = () => {
    const text = accRef.current
    if (!text) return
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (last?.role === 'assistant') {
        return [...prev.slice(0, -1), { role: 'assistant', content: text }]
      }
      return [...prev, { role: 'assistant', content: text }]
    })
  }

  const handleSend = async () => {
    const q = input.trim()
    if (!q || streaming) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: q }])
    setStreaming(true)
    accRef.current = ''

    // Flush accumulated text every 50ms to avoid per-chunk re-renders
    timerRef.current = setInterval(flushAccumulator, 50)

    try {
      for await (const chunk of streamChat(selectedNodeId, q)) {
        accRef.current += chunk
      }
    } catch {
      accRef.current += '\n\n[Error: could not reach agent]'
    } finally {
      if (timerRef.current) clearInterval(timerRef.current)
      flushAccumulator()
      setStreaming(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  const handleClear = () => {
    setMessages([])
    accRef.current = ''
  }

  if (!chatOpen) return null

  return (
    <div
      className="absolute right-80 top-0 bottom-0 w-[400px] bg-elevated border-l border-border
                 z-30 flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
        <span className="text-xs text-textMuted uppercase tracking-wider">Research Agent</span>
        <div className="flex items-center gap-3">
          <button
            onClick={handleClear}
            className="text-xs text-textMuted hover:text-textPrimary transition-colors"
          >
            Clear
          </button>
          <button
            onClick={() => setChatOpen(false)}
            className="text-textMuted hover:text-textPrimary transition-colors text-lg leading-none"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-textMuted text-xs text-center mt-8">
            Ask anything about this paper or the knowledge graph.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-card px-3 py-2 text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary text-white'
                  : 'bg-surface text-textPrimary'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div className="prose prose-invert prose-xs max-w-none
                               [&_p]:text-xs [&_li]:text-xs [&_h3]:text-xs">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                  {streaming && i === messages.length - 1 && (
                    <span className="inline-block w-1.5 h-3 bg-accent animate-pulse ml-0.5" />
                  )}
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-border shrink-0">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this paper…"
            disabled={streaming}
            className="flex-1 bg-surface border border-border rounded-card px-3 py-2 text-sm
                       text-textPrimary placeholder-textMuted outline-none
                       focus:ring-2 focus:ring-primary focus:border-primary transition-colors
                       disabled:opacity-50"
          />
          <button
            onClick={() => void handleSend()}
            disabled={!input.trim() || streaming}
            className="bg-primary text-white rounded-card px-3 py-2 text-sm font-medium
                       hover:bg-primary/80 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

'use client'

import { useState, useRef, useId, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2 } from 'lucide-react'
import { streamChat, ConfidenceResult, ContradictionResult, SourceRef } from '@/lib/api'
import { ConfidenceBar } from './ConfidenceBar'
import { ContradictionBadge } from './ContradictionBadge'
import { SourceCard } from './SourceCard'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  done?: boolean
  confidence?: ConfidenceResult
  contradiction?: ContradictionResult
  sources?: SourceRef[]
}

interface Props {
  onContradiction?: () => void
  isDemoMode?: boolean
}

const DEMO_SUGGESTIONS = [
  {
    label: 'Remote work policy',
    question: 'What is the remote work policy and how many days per week are allowed?',
    badge: '⚡ Contradiction',
    badgeClass: 'text-red-400 bg-red-400/10 border-red-400/20',
  },
  {
    label: 'Q3 marketing budget',
    question: 'What was the Q3 2023 marketing budget?',
    badge: '⚡ Contradiction',
    badgeClass: 'text-red-400 bg-red-400/10 border-red-400/20',
  },
  {
    label: 'Project Atlas status',
    question: 'What is the current status of Project Atlas?',
    badge: '🕳 Knowledge gap',
    badgeClass: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
  },
  {
    label: '2024 product roadmap',
    question: 'What are the key product priorities in the 2024 roadmap?',
    badge: '📄 Sources',
    badgeClass: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20',
  },
]

export function ChatWindow({ onContradiction, isDemoMode }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const sessionId = useRef(crypto.randomUUID())
  const queryCount = useRef(0)
  const idPrefix = useId()
  const bottomRef = useRef<HTMLDivElement>(null)

  const submitQuestion = useCallback(async (question: string) => {
    if (!question.trim() || streaming || queryCount.current >= 20) return

    setInput('')
    queryCount.current++

    const uid = `${idPrefix}-u-${queryCount.current}`
    const aid = `${idPrefix}-a-${queryCount.current}`

    setMessages(prev => [
      ...prev,
      { id: uid, role: 'user', content: question },
      { id: aid, role: 'assistant', content: '' },
    ])
    setStreaming(true)

    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)

    try {
      for await (const event of streamChat(question, sessionId.current)) {
        if (event.type === 'token') {
          setMessages(prev =>
            prev.map(m =>
              m.id === aid
                ? { ...m, content: m.content + (event.data.text as string) }
                : m
            )
          )
          setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 10)
        } else if (event.type === 'transparency') {
          const t = event.data as unknown as {
            confidence: string
            confidence_score: number
            reasoning: string
            sources: SourceRef[]
          }
          setMessages(prev =>
            prev.map(m =>
              m.id === aid
                ? {
                    ...m,
                    confidence: {
                      score: t.confidence_score,
                      label: t.confidence as 'high' | 'moderate' | 'low',
                      reasoning: t.reasoning,
                      sources: t.sources ?? [],
                    },
                    sources: t.sources ?? [],
                  }
                : m
            )
          )
        } else if (event.type === 'contradiction') {
          const c = event.data as unknown as ContradictionResult
          setMessages(prev =>
            prev.map(m =>
              m.id === aid ? { ...m, contradiction: c } : m
            )
          )
          onContradiction?.()
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Something went wrong.'
      setMessages(prev =>
        prev.map(m => (m.id === aid ? { ...m, content: msg, done: true } : m))
      )
    } finally {
      setMessages(prev =>
        prev.map(m => (m.id === aid ? { ...m, done: true } : m))
      )
      setStreaming(false)
    }
  }, [streaming, idPrefix, onContradiction])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    await submitQuestion(input.trim())
  }

  const atLimit = queryCount.current >= 20

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.length === 0 && (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              className="flex flex-col items-center justify-center mt-8 px-4"
            >
              {isDemoMode ? (
                <>
                  <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium mb-4">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Demo corpus loaded · 5 documents
                    </div>
                    <h2 className="text-slate-200 text-base font-semibold mb-1">
                      Ask anything — or pick a question below
                    </h2>
                    <p className="text-slate-500 text-sm max-w-md">
                      Each question is designed to show a different NEXUS capability.
                      Watch for the contradiction badge, confidence bar, and source cards.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
                    {DEMO_SUGGESTIONS.map((s) => (
                      <button
                        key={s.label}
                        onClick={() => submitQuestion(s.question)}
                        disabled={streaming}
                        className="group text-left rounded-xl p-4 bg-slate-800/60 border border-slate-700/60 hover:border-indigo-500/50 hover:bg-slate-800 transition-all duration-200 disabled:opacity-50 cursor-pointer"
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <span className="text-slate-200 text-sm font-medium group-hover:text-indigo-300 transition-colors">
                            {s.label}
                          </span>
                          <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border ${s.badgeClass}`}>
                            {s.badge}
                          </span>
                        </div>
                        <p className="text-slate-500 text-xs leading-relaxed">
                          {s.question}
                        </p>
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-slate-500 text-center mt-16 text-sm">
                  Ask anything about your documents.
                </p>
              )}
            </motion.div>
          )}

          {messages.map(msg => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'user' ? (
                <div className="max-w-2xl w-full rounded-2xl px-4 py-3 bg-indigo-600 text-white ml-8">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                </div>
              ) : (
                <div
                  className="max-w-2xl w-full rounded-2xl px-4 py-3 mr-8 bg-slate-800/80 space-y-4"
                  style={{
                    border: '1px solid rgba(99,102,241,0.45)',
                    boxShadow: '0 0 12px rgba(99,102,241,0.12)',
                  }}
                >
                  {/* Answer text */}
                  <p className="text-sm leading-relaxed whitespace-pre-wrap text-slate-100">
                    {msg.content}
                    {streaming && !msg.done && msg.content === '' && (
                      <span className="inline-block w-1.5 h-4 bg-slate-400 animate-pulse ml-0.5 align-middle" />
                    )}
                    {streaming && !msg.done && msg.content !== '' && (
                      <span className="inline-block w-0.5 h-3.5 bg-indigo-400 animate-pulse ml-0.5 align-middle" />
                    )}
                  </p>

                  {/* Confidence bar — only after we have the data */}
                  {msg.confidence && (
                    <ConfidenceBar
                      score={msg.confidence.score}
                      label={msg.confidence.label}
                      reasoning={msg.confidence.reasoning}
                    />
                  )}

                  {/* Source cards */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="space-y-1">
                      {msg.sources.map((src, i) => (
                        <SourceCard key={i} source={src} />
                      ))}
                    </div>
                  )}

                  {/* Contradiction badge — always shown once stream is done */}
                  {msg.done && (
                    <ContradictionBadge contradiction={msg.contradiction} />
                  )}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-800 p-4">
        {atLimit && (
          <p className="text-xs text-amber-400 mb-2">
            Session limit reached (20 queries). Refresh to start a new session.
          </p>
        )}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about your documents..."
            disabled={streaming || atLimit}
            className="flex-1 bg-slate-800 text-slate-100 placeholder-slate-500 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/60 disabled:opacity-50 transition"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim() || atLimit}
            className="px-4 py-2.5 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-40 text-white rounded-xl transition-colors"
          >
            {streaming ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

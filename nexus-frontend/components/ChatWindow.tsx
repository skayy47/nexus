'use client'

import { useState, useRef, useId, useCallback } from 'react'
import { useTranslations, useLocale } from 'next-intl'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, UploadCloud } from 'lucide-react'
import { streamChat, GroundingResult, ContradictionResult, SourceRef } from '@/lib/api'
import { GroundingPanel } from './GroundingPanel'
import { ContradictionBadge } from './ContradictionBadge'
import { SourceCard } from './SourceCard'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  done?: boolean
  grounding?: GroundingResult
  contradiction?: ContradictionResult
  sources?: SourceRef[]
  isError?: boolean
}

interface Props {
  onContradiction?: () => void
  isDemoMode?: boolean
  documentCount?: number
  onRequestUpload?: () => void
}

// Styling per demo suggestion; the copy lives in messages (chatWindow.s{n}*).
const SUGGESTION_META = [
  { key: 's1', badgeClass: 'text-red-400 bg-red-400/10 border-red-400/20', dotClass: 'bg-red-400' },
  { key: 's2', badgeClass: 'text-red-400 bg-red-400/10 border-red-400/20', dotClass: 'bg-red-400' },
  { key: 's3', badgeClass: 'text-amber-400 bg-amber-400/10 border-amber-400/20', dotClass: 'bg-amber-400' },
  { key: 's4', badgeClass: 'text-[#C9973B] bg-[#C9973B]/10 border-[#C9973B]/20', dotClass: 'bg-[#C9973B]' },
] as const

const WORKSPACE_SUGGESTION_META = [
  { key: 'workspaceS1', badgeClass: 'text-[#C9973B] bg-[#C9973B]/10 border-[#C9973B]/20', dotClass: 'bg-[#C9973B]' },
  { key: 'workspaceS2', badgeClass: 'text-red-400 bg-red-400/10 border-red-400/20', dotClass: 'bg-red-400' },
  { key: 'workspaceS3', badgeClass: 'text-[#8A7A62] bg-[#8A7A62]/10 border-[#8A7A62]/20', dotClass: 'bg-[#8A7A62]' },
] as const

export function ChatWindow({ onContradiction, isDemoMode, documentCount = 0, onRequestUpload }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const sessionId = useRef(crypto.randomUUID())
  const queryCount = useRef(0)
  const idPrefix = useId()
  const bottomRef = useRef<HTMLDivElement>(null)
  const t = useTranslations('chatWindow')
  const locale = useLocale()

  const demoSuggestions = SUGGESTION_META.map((m) => ({
    label: t(`${m.key}Label`),
    question: t(`${m.key}Question`),
    badge: t(`${m.key}Badge`),
    badgeClass: m.badgeClass,
    dotClass: m.dotClass,
  }))

  const workspaceSuggestions = WORKSPACE_SUGGESTION_META.map((m) => ({
    label: t(`${m.key}Label`),
    question: t(`${m.key}Question`),
    badge: '',
    badgeClass: m.badgeClass,
    dotClass: m.dotClass,
  }))

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
      for await (const event of streamChat(question, sessionId.current, locale)) {
        if (event.type === 'token') {
          setMessages(prev =>
            prev.map(m =>
              m.id === aid
                ? { ...m, content: m.content + (event.data.text as string) }
                : m
            )
          )
          setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 10)
        } else if (event.type === 'grounding') {
          const g = event.data as unknown as GroundingResult
          setMessages(prev =>
            prev.map(m =>
              m.id === aid
                ? { ...m, grounding: g, sources: g.sources ?? [] }
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
        } else if (event.type === 'error') {
          const msg = (event.data.message as string) || 'Something went wrong.'
          setMessages(prev =>
            prev.map(m => (m.id === aid ? { ...m, content: msg, done: true, isError: true } : m))
          )
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Something went wrong.'
      setMessages(prev =>
        prev.map(m => (m.id === aid ? { ...m, content: msg, done: true, isError: true } : m))
      )
    } finally {
      setMessages(prev =>
        prev.map(m => (m.id === aid ? { ...m, done: true } : m))
      )
      setStreaming(false)
    }
  }, [streaming, idPrefix, onContradiction, locale])

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
                /* ── Demo empty state ─────────────────── */
                <>
                  <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#D4A843]/10 border border-[#D4A843]/25 text-[#D4A843] text-xs font-medium mb-4">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#D4A843] animate-pulse" />
                      {t('demoLoaded')}
                    </div>
                    <h2 className="text-[#EDE4D0] text-base font-semibold mb-1">
                      {t('askOrPick')}
                    </h2>
                    <p className="text-[#6A5A42] text-sm max-w-md">
                      {t('eachQuestion')}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
                    {demoSuggestions.map((s) => (
                      <button
                        key={s.label}
                        onClick={() => submitQuestion(s.question)}
                        disabled={streaming}
                        className="group text-left rounded-xl p-4 bg-[#1A1208]/80 border border-[#C9973B]/20 hover:border-[#C9973B]/50 hover:bg-[#1A1208] transition-all duration-200 disabled:opacity-50 cursor-pointer"
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <span className="text-[#DDD0BB] text-sm font-medium group-hover:text-[#D4A843] transition-colors">
                            {s.label}
                          </span>
                          <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border ${s.badgeClass}`}>
                            {s.badge}
                          </span>
                        </div>
                        <p className="text-[#6A5A42] text-xs leading-relaxed">
                          {s.question}
                        </p>
                      </button>
                    ))}
                  </div>
                </>

              ) : documentCount === 0 ? (
                /* ── Upload empty state ───────────────── */
                <div className="flex flex-col items-center text-center max-w-sm mt-4">
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.1, duration: 0.4 }}
                    className="w-20 h-20 rounded-2xl bg-[#C9973B]/10 border border-[#C9973B]/20 grid place-items-center mb-6"
                    style={{ boxShadow: '0 0 40px rgba(201,151,59,0.15)' }}
                  >
                    <UploadCloud size={32} className="text-[#C9973B]" />
                  </motion.div>
                  <h2 className="text-[#EDE4D0] text-base font-semibold mb-2">
                    {t('uploadTitle')}
                  </h2>
                  <p className="text-[#6A5A42] text-sm leading-relaxed mb-6">
                    {t('uploadDesc')}
                  </p>
                  <button
                    onClick={onRequestUpload}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#C9973B] hover:bg-[#B8882A] text-[#0E0A05] text-sm font-semibold rounded-xl transition-colors"
                  >
                    <UploadCloud size={15} />
                    {t('uploadAction')}
                  </button>
                </div>

              ) : (
                /* ── Workspace ready state ────────────── */
                <>
                  <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#C9973B]/10 border border-[#C9973B]/20 text-[#C9973B] text-xs font-medium mb-4">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#C9973B]" />
                      {t('workspaceReadyTitle')}
                    </div>
                    <p className="text-[#6A5A42] text-sm max-w-md">
                      {t('workspaceReadyDesc', { count: documentCount })}
                    </p>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-2xl">
                    {workspaceSuggestions.map((s) => (
                      <button
                        key={s.label}
                        onClick={() => submitQuestion(s.question)}
                        disabled={streaming}
                        className="group text-left rounded-xl p-4 bg-[#1A1208]/80 border border-[#C9973B]/20 hover:border-[#C9973B]/50 hover:bg-[#1A1208] transition-all duration-200 disabled:opacity-50 cursor-pointer"
                      >
                        <div className="flex items-center gap-1.5 mb-2">
                          <span className={`w-1.5 h-1.5 rounded-full ${s.dotClass}`} />
                          <span className="text-[#DDD0BB] text-sm font-medium group-hover:text-[#D4A843] transition-colors">
                            {s.label}
                          </span>
                        </div>
                        <p className="text-[#6A5A42] text-xs leading-relaxed">
                          {s.question}
                        </p>
                      </button>
                    ))}
                  </div>
                </>
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
                <div className="max-w-2xl w-full rounded-2xl px-4 py-3 bg-gradient-to-br from-[#C9973B] to-[#9B6B3A] text-[#0E0A05] ml-8">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                </div>
              ) : (
                <div
                  className="max-w-2xl w-full rounded-2xl px-4 py-3 mr-8 bg-[#1A1208]/90 space-y-4"
                  style={{
                    border: msg.isError
                      ? '1px solid rgba(239,68,68,0.35)'
                      : '1px solid rgba(201,151,59,0.30)',
                    boxShadow: msg.isError
                      ? '0 0 12px rgba(239,68,68,0.08)'
                      : '0 0 12px rgba(201,151,59,0.08)',
                  }}
                >
                  {/* Answer text */}
                  <p className={`text-sm leading-relaxed whitespace-pre-wrap ${msg.isError ? 'text-red-400' : 'text-slate-100'}`}>
                    {msg.content}
                    {streaming && !msg.done && msg.content === '' && (
                      <span className="inline-block w-1.5 h-4 bg-slate-400 animate-pulse ml-0.5 align-middle" />
                    )}
                    {streaming && !msg.done && msg.content !== '' && (
                      <span className="inline-block w-0.5 h-3.5 bg-[#C9973B] animate-pulse ml-0.5 align-middle" />
                    )}
                  </p>

                  {/* Grounding — source verification of the answer */}
                  {msg.grounding && <GroundingPanel grounding={msg.grounding} />}

                  {/* Source cards */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="space-y-1">
                      {msg.sources.map((src, i) => (
                        <SourceCard key={i} source={src} />
                      ))}
                    </div>
                  )}

                  {/* Contradiction badge — only shown once stream is done and no error */}
                  {msg.done && !msg.isError && (
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
      <div className="border-t border-[#C9973B]/15 p-4">
        {/* Persistent suggestion chips — demo mode only, after first question */}
        {isDemoMode && messages.length > 0 && !atLimit && (
          <div className="flex gap-2 mb-3 overflow-x-auto pb-1 -mx-1 px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            <span className="shrink-0 text-[11px] text-[#6A5A42] self-center pr-1">{t('tryLabel')}</span>
            {demoSuggestions.map((s) => (
              <button
                key={s.label}
                onClick={() => submitQuestion(s.question)}
                disabled={streaming}
                title={s.question}
                className="shrink-0 inline-flex items-center gap-1.5 text-xs text-[#C4B49A] bg-[#1A1208]/80 border border-[#C9973B]/20 hover:border-[#C9973B]/50 hover:text-[#EDE4D0] rounded-full px-3 py-1.5 transition-all disabled:opacity-40 cursor-pointer"
              >
                <span className={`w-1.5 h-1.5 rounded-full ${s.dotClass}`} />
                {s.label}
              </button>
            ))}
          </div>
        )}
        {atLimit && (
          <p className="text-xs text-amber-400 mb-2">
            {t('sessionLimit')}
          </p>
        )}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={t('placeholder')}
            disabled={streaming || atLimit}
            className="flex-1 bg-[#1A1208] text-[#EDE4D0] placeholder-[#5E5040] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C9973B]/40 border border-[#C9973B]/15 disabled:opacity-50 transition"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim() || atLimit}
            className="px-4 py-2.5 bg-[#C9973B] hover:bg-[#B8882A] disabled:opacity-40 text-[#0E0A05] rounded-xl transition-colors"
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

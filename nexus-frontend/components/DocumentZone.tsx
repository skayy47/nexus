'use client'

import { useState, useRef } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, CheckCircle, XCircle, Trash2 } from 'lucide-react'
import { uploadDocument, clearDocuments } from '@/lib/api'
import { blobStore } from '@/lib/blobStore'

type ZoneState = 'idle' | 'clearing' | 'processing' | 'done' | 'error'

interface FileResult {
  name: string
  chunks?: number
  error?: string
}

interface SummaryData {
  filename: string
  summary: string
  bullets: string[]
  questions: string[]
}

interface Props {
  onClear?: () => void
  onUpload?: () => void
  onSummaryReady?: (data: SummaryData) => void
}

export function DocumentZone({ onClear, onUpload, onSummaryReady }: Props) {
  const t = useTranslations('documentZone')
  const locale = useLocale()
  const [state, setState] = useState<ZoneState>('idle')
  const [progressText, setProgressText] = useState('')
  const [results, setResults] = useState<FileResult[]>([])
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const clearedThisSession = useRef(false)

  async function handleFiles(files: File[]) {
    if (!files.length) return

    // Auto-clear demo docs on first upload of the session
    if (!clearedThisSession.current) {
      setState('clearing')
      setProgressText('')
      try {
        await clearDocuments()
        blobStore.clear()
        clearedThisSession.current = true
        onClear?.()
      } catch {
        // non-fatal — continue
      }
    }

    setState('processing')
    const newResults: FileResult[] = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setProgressText(t('processing', { current: i + 1, total: files.length, name: file.name }))

      try {
        const result = await uploadDocument(file, locale)
        blobStore.set(file.name, file)
        newResults.push({ name: file.name, chunks: result.chunk_count })
        onUpload?.()
        if (result.summary || (result.bullets && result.bullets.length > 0)) {
          onSummaryReady?.({
            filename: file.name,
            summary: result.summary || '',
            bullets: result.bullets || [],
            questions: result.suggested_questions || [],
          })
        }
      } catch (err) {
        newResults.push({
          name: file.name,
          error: err instanceof Error ? err.message : t('uploadFailed'),
        })
      }
    }

    setResults(newResults)
    setState('done')
  }

  async function handleClearAll(e: React.MouseEvent) {
    e.stopPropagation()
    setState('clearing')
    try {
      await clearDocuments()
      blobStore.clear()
      clearedThisSession.current = true
      onClear?.()
      setState('idle')
      setResults([])
    } catch (err) {
      setState('error')
      setProgressText(err instanceof Error ? err.message : t('clearFailed'))
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length) handleFiles(files)
  }

  const successCount = results.filter(r => !r.error).length
  const errorCount = results.filter(r => r.error).length

  const borderColor = dragging
    ? 'border-[#C9973B]'
    : state === 'error'
    ? 'border-red-500/60'
    : state === 'done' && errorCount === 0
    ? 'border-emerald-500/60'
    : state === 'done' && errorCount > 0
    ? 'border-amber-500/60'
    : 'border-[#C9973B]/20 hover:border-[#C9973B]/50'

  const clickable = state === 'idle' || state === 'done' || state === 'error'

  return (
    <div className="space-y-2">
      <div
        role={clickable ? 'button' : undefined}
        tabIndex={clickable ? 0 : undefined}
        aria-label="Upload documents — click or drag files here"
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${clickable ? 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#C9973B]/60' : ''} ${borderColor}`}
        onClick={() => clickable && inputRef.current?.click()}
        onKeyDown={e => { if (clickable && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); inputRef.current?.click() } }}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.csv,.rtf,.json,.eml,.txt,.md,.markdown,.html,.htm"
          multiple
          className="hidden"
          onChange={e => {
            const files = Array.from(e.target.files ?? [])
            if (files.length) handleFiles(files)
            e.target.value = ''
          }}
        />

        <AnimatePresence mode="wait">
          {state === 'idle' && (
            <motion.div key="idle"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-2"
            >
              <UploadCloud size={24} className="text-[#C9973B]/60" />
              <p className="text-sm text-[#8A7A62]">
                {t('dropFiles')} <span className="text-[#C9973B]">{t('browse')}</span>
              </p>
              <p className="text-xs text-[#5E5040]">{t('formats')}</p>
            </motion.div>
          )}

          {state === 'clearing' && (
            <motion.div key="clearing"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-2"
            >
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                <Trash2 size={24} className="text-amber-400" />
              </motion.div>
              <p className="text-sm text-slate-400">{t('clearing')}</p>
            </motion.div>
          )}

          {state === 'processing' && (
            <motion.div key="processing"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-2"
            >
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                <UploadCloud size={24} className="text-[#C9973B]" />
              </motion.div>
              <p className="text-sm text-[#8A7A62]">{progressText}</p>
              {/* Mini progress bar */}
              <div className="w-48 h-1 bg-[#C9973B]/15 rounded-full overflow-hidden mt-1">
                <motion.div
                  className="h-full bg-[#C9973B] rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 0.8, ease: 'easeInOut' }}
                />
              </div>
            </motion.div>
          )}

          {state === 'done' && (
            <motion.div key="done"
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-2"
            >
              <CheckCircle size={24} className={errorCount === 0 ? 'text-emerald-400' : 'text-amber-400'} />
              <p className={`text-sm font-medium ${errorCount === 0 ? 'text-emerald-300' : 'text-amber-300'}`}>
                {t('loaded', { count: successCount })}
                {errorCount > 0 && t('failed', { count: errorCount })}
              </p>
              {/* Per-file results */}
              <ul className="w-full max-w-xs text-left space-y-1 mt-1">
                {results.map(r => (
                  <li key={r.name} className="flex flex-col gap-0.5 text-xs">
                    <div className="flex items-center gap-1.5">
                      {r.error
                        ? <XCircle size={11} className="text-red-400 shrink-0" />
                        : <CheckCircle size={11} className="text-emerald-400 shrink-0" />}
                      <span className={`truncate ${r.error ? 'text-red-400' : 'text-[#8A7A62]'}`} title={r.error || r.name}>
                        {r.name}
                      </span>
                      {r.chunks !== undefined && (
                        <span className="text-[#5E5040] shrink-0">{t('chunks', { count: r.chunks })}</span>
                      )}
                    </div>
                    {r.error && (
                      <p className="text-[10px] text-red-400/70 pl-[19px] leading-tight">{r.error}</p>
                    )}
                  </li>
                ))}
              </ul>
              <button
                onClick={e => { e.stopPropagation(); setState('idle'); setResults([]) }}
                className="text-xs text-slate-500 hover:text-slate-300 underline mt-1"
              >
                {t('uploadMore')}
              </button>
            </motion.div>
          )}

          {state === 'error' && (
            <motion.div key="error"
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-2"
            >
              <XCircle size={24} className="text-red-400" />
              <p className="text-sm text-red-300">{progressText}</p>
              <button
                onClick={e => { e.stopPropagation(); setState('idle') }}
                className="text-xs text-slate-500 hover:text-slate-300 underline mt-1"
              >
                {t('tryAgain')}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {(state === 'idle' || state === 'done') && (
        <motion.button
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          onClick={handleClearAll}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-red-400 transition-colors"
        >
          <Trash2 size={12} />
          {t('clearAll')}
        </motion.button>
      )}
    </div>
  )
}

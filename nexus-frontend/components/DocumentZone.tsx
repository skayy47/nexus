'use client'

import { useState, useRef } from 'react'
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

interface Props {
  onClear?: () => void
  onUpload?: () => void
}

export function DocumentZone({ onClear, onUpload }: Props) {
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
      setProgressText(`Processing ${i + 1}/${files.length}: ${file.name}`)

      try {
        const result = await uploadDocument(file)
        blobStore.set(file.name, file)
        newResults.push({ name: file.name, chunks: result.chunk_count })
        onUpload?.()
      } catch (err) {
        newResults.push({
          name: file.name,
          error: err instanceof Error ? err.message : 'Upload failed',
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
      setProgressText(err instanceof Error ? err.message : 'Clear failed.')
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length) handleFiles(files)
  }

  const successCount = results.filter(r => !r.error).length
  const errorCount   = results.filter(r =>  r.error).length

  const borderColor = dragging
    ? 'border-indigo-500'
    : state === 'error'
    ? 'border-red-500/60'
    : state === 'done' && errorCount === 0
    ? 'border-emerald-500/60'
    : state === 'done' && errorCount > 0
    ? 'border-amber-500/60'
    : 'border-slate-600 hover:border-indigo-500/60'

  const clickable = state === 'idle' || state === 'done' || state === 'error'

  return (
    <div className="space-y-2">
      <div
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${clickable ? 'cursor-pointer' : ''} ${borderColor}`}
        onClick={() => clickable && inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
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
              <UploadCloud size={24} className="text-slate-500" />
              <p className="text-sm text-slate-400">
                Drop files or <span className="text-indigo-400">browse</span>
              </p>
              <p className="text-xs text-slate-600">PDF, DOCX, TXT, MD — max 20 MB · multiple files supported</p>
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
              <p className="text-sm text-slate-400">Clearing previous documents...</p>
            </motion.div>
          )}

          {state === 'processing' && (
            <motion.div key="processing"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-2"
            >
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                <UploadCloud size={24} className="text-indigo-400" />
              </motion.div>
              <p className="text-sm text-slate-400">{progressText}</p>
              {/* Mini progress bar */}
              <div className="w-48 h-1 bg-slate-700 rounded-full overflow-hidden mt-1">
                <motion.div
                  className="h-full bg-indigo-500 rounded-full"
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
                {successCount} document{successCount !== 1 ? 's' : ''} loaded
                {errorCount > 0 && `, ${errorCount} failed`}
              </p>
              {/* Per-file results */}
              <ul className="w-full max-w-xs text-left space-y-0.5 mt-1">
                {results.map(r => (
                  <li key={r.name} className="flex items-center gap-1.5 text-xs">
                    {r.error
                      ? <XCircle size={11} className="text-red-400 shrink-0" />
                      : <CheckCircle size={11} className="text-emerald-400 shrink-0" />}
                    <span className={`truncate ${r.error ? 'text-red-400' : 'text-slate-400'}`} title={r.name}>
                      {r.name}
                    </span>
                    {r.chunks !== undefined && (
                      <span className="text-slate-600 shrink-0">{r.chunks} chunks</span>
                    )}
                  </li>
                ))}
              </ul>
              <button
                onClick={e => { e.stopPropagation(); setState('idle'); setResults([]) }}
                className="text-xs text-slate-500 hover:text-slate-300 underline mt-1"
              >
                Upload more
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
                Try again
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
          Clear all documents
        </motion.button>
      )}
    </div>
  )
}

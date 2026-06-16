'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'framer-motion'
import { Zap, Search, FileText, ChevronDown, ChevronRight, ExternalLink, X } from 'lucide-react'
import { deleteDocument } from '@/lib/api'
import { blobStore } from '@/lib/blobStore'
import type { DocumentEntry } from '@/lib/api'

interface Props {
  contradictionCount?: number
  gapCount?: number
  documentCount?: number
  documents?: DocumentEntry[]
  onDeleteDocument?: () => void
  isDemoMode?: boolean
}

export function InsightSidebar({
  contradictionCount = 0,
  gapCount = 0,
  documentCount = 0,
  documents = [],
  onDeleteDocument,
  isDemoMode = false,
}: Props) {
  const t = useTranslations('sidebar')
  const tw = useTranslations('chatWindow')
  const [docsOpen, setDocsOpen] = useState(true)
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null)

  async function handleDelete(e: React.MouseEvent, name: string) {
    e.stopPropagation()
    setDeletingDoc(name)
    try {
      await deleteDocument(name)
      blobStore.revoke(name)
      onDeleteDocument?.()
    } catch {
      // ignore — sidebar will refresh on next poll
    } finally {
      setDeletingDoc(null)
    }
  }

  function handleOpenDoc(name: string) {
    const url = blobStore.get(name)
    if (url) {
      window.open(url, '_blank')
    }
  }

  return (
    <div className="p-4 h-full flex flex-col overflow-y-auto">
      {/* Mode badge */}
      <div className="mb-4 flex items-center gap-1.5">
        {isDemoMode ? (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/12 border border-emerald-500/25 text-emerald-400">
            <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
            {tw('modeBadgeDemo')}
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#C9973B]/12 border border-[#C9973B]/25 text-[#C9973B]">
            <span className="w-1 h-1 rounded-full bg-[#C9973B]" />
            {tw('modeBadgeWorkspace')}
          </span>
        )}
      </div>

      <h2 className="text-xs font-semibold uppercase tracking-widest text-[#6A5A42] mb-4">
        {t('insights')}
      </h2>

      <div className="space-y-1">
        <StatRow
          icon={<Zap size={14} />}
          label={t('contradictions')}
          value={contradictionCount}
          accent="text-red-400"
          bg="bg-red-500/10"
          animate={contradictionCount > 0}
        />
        <StatRow
          icon={<Search size={14} />}
          label={t('gaps')}
          value={gapCount}
          accent="text-amber-400"
          bg="bg-amber-500/10"
          animate={gapCount > 0}
        />
        <StatRow
          icon={<FileText size={14} />}
          label={t('documents')}
          value={documentCount}
          accent="text-[#C9973B]"
          bg="bg-[#C9973B]/10"
        />
      </div>

      {/* Collapsible document list */}
      {documents.length > 0 && (
        <div className="mt-4">
          <button
            onClick={() => setDocsOpen(o => !o)}
            aria-expanded={docsOpen}
            className="flex items-center gap-1 text-xs text-[#6A5A42] hover:text-slate-300 transition-colors w-full mb-2"
          >
            {docsOpen ? <ChevronDown size={12} aria-hidden /> : <ChevronRight size={12} aria-hidden />}
            {t('loadedDocuments')}
          </button>

          <AnimatePresence initial={false}>
            {docsOpen && (
              <motion.ul
                key="doc-list"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-1 overflow-hidden"
              >
                {documents.map(doc => {
                  const hasBlob = !!blobStore.get(doc.name)
                  const isDeleting = deletingDoc === doc.name
                  return (
                    <li
                      key={doc.name}
                      className="group flex items-center gap-1 rounded-md px-1.5 py-1 transition-colors hover:bg-[#C9973B]/10"
                    >
                      <button
                        onClick={() => handleOpenDoc(doc.name)}
                        className={`flex items-center gap-1 flex-1 min-w-0 text-left ${hasBlob ? 'cursor-pointer' : 'cursor-default'}`}
                        title={hasBlob ? `Open ${doc.name}` : doc.name}
                      >
                        <span className="text-xs text-[#8A7A62] truncate leading-tight">
                          {doc.name}
                        </span>
                        {hasBlob && (
                          <ExternalLink
                            size={10}
                            className="shrink-0 text-slate-600 group-hover:text-[#C9973B] transition-colors"
                          />
                        )}
                      </button>

                      <span className="shrink-0 px-1.5 py-0.5 rounded-full bg-[#C9973B]/10 text-[#C9973B] text-[10px] tabular-nums">
                        {doc.chunk_count}
                      </span>

                      {/* Delete only in workspace mode */}
                      {!isDemoMode && (
                        <button
                          onClick={e => handleDelete(e, doc.name)}
                          disabled={isDeleting}
                          aria-label={`Remove ${doc.name}`}
                          className="shrink-0 opacity-0 group-hover:opacity-100 focus:opacity-100 text-slate-600 hover:text-red-400 transition-all disabled:opacity-30"
                        >
                          {isDeleting
                            ? <span className="inline-block w-3 h-3 border border-slate-500 border-t-transparent rounded-full animate-spin" aria-label="Deleting…" />
                            : <X size={11} aria-hidden />}
                        </button>
                      )}
                    </li>
                  )
                })}
              </motion.ul>
            )}
          </AnimatePresence>
        </div>
      )}

      {contradictionCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20"
        >
          <p className="text-xs text-red-400 leading-relaxed">
            {t('contradictionMsg', { count: contradictionCount })}
          </p>
        </motion.div>
      )}
    </div>
  )
}

function StatRow({
  icon, label, value, accent, bg, animate = false,
}: {
  icon: React.ReactNode
  label: string
  value: number
  accent: string
  bg: string
  animate?: boolean
}) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-[#C9973B]/10">
      <span className="flex items-center gap-2 text-sm text-[#8A7A62]">
        <span className={`p-1 rounded ${bg} ${accent}`}>{icon}</span>
        {label}
      </span>
      <motion.span
        key={value}
        initial={animate && value > 0 ? { scale: 1.4, color: '#ef4444' } : {}}
        animate={{ scale: 1, color: 'inherit' }}
        className={`text-base font-bold tabular-nums ${accent}`}
      >
        {value}
      </motion.span>
    </div>
  )
}

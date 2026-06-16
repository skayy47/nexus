'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Upload, X } from 'lucide-react'
import { ChatWindow } from '@/components/ChatWindow'
import { InsightSidebar } from '@/components/InsightSidebar'
import { DocumentZone } from '@/components/DocumentZone'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { getInsights, getDocuments } from '@/lib/api'
import type { DocumentEntry } from '@/lib/api'

function ChatPage() {
  const t = useTranslations('chat')
  const tw = useTranslations('chatWindow')
  const params = useSearchParams()
  const mode = params.get('mode')
  const isDemoMode = mode === 'demo'
  const [contradictionCount, setContradictionCount] = useState(0)
  const [gapCount, setGapCount] = useState(0)
  const [documentCount, setDocumentCount] = useState(0)
  const [documents, setDocuments] = useState<DocumentEntry[]>([])
  const [showUpload, setShowUpload] = useState(mode === 'upload')

  const refreshDocuments = useCallback(() => {
    getInsights()
      .then(d => {
        setDocumentCount(d.document_count ?? 0)
        setGapCount(d.gap_count ?? 0)
      })
      .catch(() => null)
    getDocuments()
      .then(d => setDocuments(d.documents))
      .catch(() => null)
  }, [])

  useEffect(() => {
    refreshDocuments()
  }, [refreshDocuments])

  return (
    <div className="h-dvh overflow-hidden bg-[#0E0A05] text-[#EDE4D0] flex">
      {/* Sticky sidebar */}
      <aside className="fixed left-0 top-0 h-screen z-40 w-56 border-r border-[#C9973B]/15 hidden lg:flex flex-col bg-[#0E0A05]">
        <InsightSidebar
          contradictionCount={contradictionCount}
          gapCount={gapCount}
          documentCount={documentCount}
          documents={documents}
          onDeleteDocument={refreshDocuments}
          isDemoMode={isDemoMode}
        />
      </aside>

      {/* Main — offset by sidebar width on large screens */}
      <main className="flex-1 flex flex-col min-w-0 lg:ml-56 overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-[#C9973B]/15 bg-[#0E0A05]/80 backdrop-blur-sm">
          <div className="flex items-center gap-2.5">
            {/* Mode badge */}
            {isDemoMode ? (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-[#D4A843]/12 border border-[#D4A843]/30 text-[#D4A843]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#D4A843] animate-pulse" />
                {tw('modeBadgeDemo')}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-[#C9973B]/12 border border-[#C9973B]/25 text-[#C9973B]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#C9973B]" />
                {tw('modeBadgeWorkspace')}
              </span>
            )}
            <span className="text-xs text-[#6A5A42]">
              {documentCount > 0 ? t('docsInContext', { count: documentCount }) : t('noDocuments')}
            </span>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setShowUpload(v => !v)}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-[#C4B49A] hover:text-[#EDE4D0] border border-[#C9973B]/20 hover:border-[#C9973B]/50 rounded-lg px-3 py-1.5 transition-colors cursor-pointer"
            >
              {showUpload ? <X size={14} /> : <Upload size={14} />}
              {showUpload ? t('close') : t('upload')}
            </button>
            <LanguageSwitcher />
          </div>
        </div>

        {/* Mobile insight stats — only visible on small screens where sidebar is hidden */}
        <div className="lg:hidden flex items-center gap-4 px-4 py-2 border-b border-[#C9973B]/15 bg-[#0E0A05]/60 text-xs text-[#8A7A62]">
          {contradictionCount > 0 && (
            <span className="flex items-center gap-1 text-red-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
              {contradictionCount} contradiction{contradictionCount !== 1 ? 's' : ''}
            </span>
          )}
          {gapCount > 0 && (
            <span className="flex items-center gap-1 text-amber-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              {gapCount} gap{gapCount !== 1 ? 's' : ''}
            </span>
          )}
          {contradictionCount === 0 && gapCount === 0 && documentCount > 0 && (
            <span className="text-[#5E5040]">No issues detected</span>
          )}
        </div>

        {showUpload && (
          <div className="p-4 border-b border-[#C9973B]/15 bg-[#1A1208]/30">
            <DocumentZone
              onClear={refreshDocuments}
              onUpload={refreshDocuments}
            />
          </div>
        )}

        <ChatWindow
          onContradiction={() => setContradictionCount(n => n + 1)}
          isDemoMode={isDemoMode}
          documentCount={documentCount}
          onRequestUpload={() => setShowUpload(true)}
        />
      </main>
    </div>
  )
}

export default function ChatPageWrapper() {
  return (
    <Suspense>
      <ChatPage />
    </Suspense>
  )
}

'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Upload, X } from 'lucide-react'
import { ChatWindow } from '@/components/ChatWindow'
import { InsightSidebar } from '@/components/InsightSidebar'
import { DocumentZone } from '@/components/DocumentZone'
import { getInsights, getDocuments } from '@/lib/api'
import type { DocumentEntry } from '@/lib/api'

function ChatPage() {
  const params = useSearchParams()
  const mode = params.get('mode')
  const [contradictionCount, setContradictionCount] = useState(0)
  const [documentCount, setDocumentCount] = useState(0)
  const [documents, setDocuments] = useState<DocumentEntry[]>([])
  // Upload zone is always reachable now — open by default when arriving via ?mode=upload
  const [showUpload, setShowUpload] = useState(mode === 'upload')

  const refreshDocuments = useCallback(() => {
    getInsights()
      .then(d => setDocumentCount(d.document_count ?? 0))
      .catch(() => null)
    getDocuments()
      .then(d => setDocuments(d.documents))
      .catch(() => null)
  }, [])

  useEffect(() => {
    refreshDocuments()
  }, [refreshDocuments])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Sticky sidebar */}
      <aside className="fixed left-0 top-0 h-screen z-40 w-56 border-r border-slate-800 hidden lg:flex flex-col bg-slate-950">
        <InsightSidebar
          contradictionCount={contradictionCount}
          documentCount={documentCount}
          documents={documents}
          onDeleteDocument={refreshDocuments}
        />
      </aside>

      {/* Main — offset by sidebar width on large screens */}
      <main className="flex-1 flex flex-col min-w-0 lg:ml-56">
        {/* Top bar — always-available upload toggle */}
        <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm">
          <span className="text-xs text-slate-500">
            {documentCount > 0 ? `${documentCount} documents in context` : 'No documents loaded'}
          </span>
          <button
            onClick={() => setShowUpload(v => !v)}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white border border-slate-700 hover:border-indigo-500/60 rounded-lg px-3 py-1.5 transition-colors cursor-pointer"
          >
            {showUpload ? <X size={14} /> : <Upload size={14} />}
            {showUpload ? 'Close' : 'Upload documents'}
          </button>
        </div>

        {showUpload && (
          <div className="p-4 border-b border-slate-800 bg-slate-900/30">
            <DocumentZone
              onClear={refreshDocuments}
              onUpload={refreshDocuments}
            />
          </div>
        )}

        <ChatWindow
          onContradiction={() => setContradictionCount(n => n + 1)}
          isDemoMode={mode === 'demo'}
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

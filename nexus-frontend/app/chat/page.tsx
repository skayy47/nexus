'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
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
        {mode === 'upload' && (
          <div className="p-4 border-b border-slate-800">
            <DocumentZone
              onClear={refreshDocuments}
              onUpload={refreshDocuments}
            />
          </div>
        )}
        <ChatWindow onContradiction={() => setContradictionCount(n => n + 1)} />
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

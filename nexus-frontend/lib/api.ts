const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Types ──────────────────────────────────────────────────────────────────

export interface SourceRef {
  document_name: string
  page_number: number
  excerpt: string
}

export interface ConfidenceResult {
  score: number
  label: 'high' | 'moderate' | 'low'
  reasoning: string
  sources: SourceRef[]
}

export interface ContradictionResult {
  excerpt_a: string
  excerpt_b: string
  source_a: string
  source_b: string
  explanation: string
}

export interface ChatEvent {
  type: 'token' | 'transparency' | 'contradiction' | 'done' | 'error'
  data: Record<string, unknown>
}

export interface InsightsResponse {
  contradiction_count: number
  gap_count: number
  document_count: number
  top_topics: string[]
}

export interface DocumentEntry {
  name: string
  chunk_count: number
}

export interface DocumentListResponse {
  documents: DocumentEntry[]
}

// ── API calls ──────────────────────────────────────────────────────────────

export async function loadDemo(): Promise<void> {
  const res = await fetch(`${API_URL}/demo`, { method: 'POST' })
  if (!res.ok) throw new Error(`Demo load failed: ${res.statusText}`)
}

export async function uploadDocument(file: File): Promise<{ document_id: string; chunk_count: number }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_URL}/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`)
  return res.json()
}

export async function getInsights(): Promise<InsightsResponse> {
  const res = await fetch(`${API_URL}/insights`)
  if (!res.ok) throw new Error('Failed to load insights')
  return res.json()
}

export async function getDocuments(): Promise<DocumentListResponse> {
  const res = await fetch(`${API_URL}/documents`)
  if (!res.ok) throw new Error('Failed to load document list')
  return res.json()
}

export async function deleteDocument(name: string): Promise<{ status: string; deleted: number }> {
  const res = await fetch(`${API_URL}/documents/${encodeURIComponent(name)}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Failed to delete document: ${name}`)
  return res.json()
}

export async function clearDocuments(): Promise<{ status: string; deleted: number }> {
  const res = await fetch(`${API_URL}/documents`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to clear documents')
  return res.json()
}

export async function* streamChat(
  question: string,
  sessionId: string
): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Chat request failed')
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      const eventLine = part.match(/^event: (.+)/)
      const dataLine = part.match(/^data: (.+)/m)
      if (eventLine && dataLine) {
        yield {
          type: eventLine[1] as ChatEvent['type'],
          data: JSON.parse(dataLine[1]),
        }
      }
    }
  }
}

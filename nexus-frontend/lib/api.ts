const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Cold-start handling ──────────────────────────────────────────────────────
// The backend runs on a free HF Space that sleeps after ~48h idle. The first
// request after sleep must wait for the container to wake (~30–60s). We poll
// /health with backoff so the demo never fails just because the box was asleep.

async function fetchWithTimeout(url: string, opts: RequestInit = {}, ms = 10000) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), ms)
  try {
    return await fetch(url, { ...opts, signal: ctrl.signal })
  } finally {
    clearTimeout(timer)
  }
}

/**
 * Poll /health until the backend is awake (or maxWaitMs elapses).
 * onWaking() fires once we detect the box was actually asleep, so the UI can
 * switch to a "waking up" message.
 */
export async function warmupBackend(
  onWaking?: () => void,
  maxWaitMs = 75000
): Promise<void> {
  const start = Date.now()
  let delay = 1500
  let firstTry = true

  while (Date.now() - start < maxWaitMs) {
    try {
      const res = await fetchWithTimeout(`${API_URL}/health`, {}, 8000)
      if (res.ok) return
    } catch {
      // network error / abort → backend is asleep, keep polling
    }
    if (firstTry) {
      onWaking?.()
      firstTry = false
    }
    await new Promise(r => setTimeout(r, delay))
    delay = Math.min(delay * 1.4, 5000)
  }
  throw new Error('Backend did not wake up in time.')
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface SourceRef {
  document_name: string
  page_number: number
  excerpt: string
}

export interface GroundedClaim {
  text: string
  supported: boolean
  source_index: number | null
  similarity: number
}

export interface GroundingResult {
  verdict: 'grounded' | 'partial' | 'ungrounded'
  coverage: number
  supported_count: number
  claim_count: number
  claims: GroundedClaim[]
  sources: SourceRef[]
  single_source: boolean
}

export interface ContradictionResult {
  excerpt_a: string
  excerpt_b: string
  source_a: string
  source_b: string
  explanation: string
}

export interface ChatEvent {
  type: 'token' | 'grounding' | 'contradiction' | 'gap' | 'done' | 'error'
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
  // Generous timeout: cold CPU embeds 52 chunks + builds BM25 + scans contradictions.
  const res = await fetchWithTimeout(`${API_URL}/demo`, { method: 'POST' }, 120000)
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
  sessionId: string,
  locale = 'en'
): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId, language: locale }),
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

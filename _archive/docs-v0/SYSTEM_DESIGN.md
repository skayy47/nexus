# NEXUS — System Design Document
**Version**: 1.0 | **Date**: 2026-04-15 | **Status**: Approved

---

## 1. Requirements

### Functional Requirements
- Upload documents (PDF, DOCX) and index them
- Chat interface to query institutional knowledge
- Contradiction Radar — detects document conflicts
- Knowledge Gap Detective — flags missing information
- Cross-Document Insight Engine — surfaces hidden connections
- Radical Transparency Mode — confidence scores + reasoning
- Source attribution on every answer

### Non-Functional Requirements
| Dimension | Target |
|-----------|--------|
| Latency (query) | < 3 seconds end-to-end |
| Uptime | 99% (free tier acceptable) |
| Cost | $0 during portfolio phase |
| Document size | Up to 50 PDFs / 500 pages |
| Concurrent users | 1-20 (demo/portfolio scale) |
| Deployment | Accessible via public URL |

### Constraints
- Free tech stack only
- 4-week timeline
- Solo developer
- Must look polished for client demos

---

## 2. Deployment Decision

### Options Evaluated

| Platform | Cost | Persistence | Cold Start | RAG Friendly | Verdict |
|----------|------|-------------|------------|--------------|---------|
| HF Spaces (Gradio) | Free | Via HF Datasets | ~30s | ✅ Good | ⚠️ OK |
| HF Spaces (Docker) | Free | Via HF Datasets | ~40s | ✅ Good | ⚠️ OK |
| Vercel (frontend) | Free | ❌ None | None | ❌ No Python | ✅ Frontend only |
| Railway (backend) | $5 credit/mo | ✅ Persistent disk | None | ✅ Excellent | ✅ Backend |
| Render | Free 750h/mo | $0.25/GB | ~30s (cold) | ✅ Good | ⚠️ Cold starts |
| Fly.io | 3 free VMs | ✅ Persistent | None | ✅ Good | ⚠️ Complex |

### ✅ CHOSEN ARCHITECTURE: Split Deployment

```
                    USER
                     │
              ┌──────▼──────┐
              │   Vercel     │  ← Next.js frontend (free, global CDN)
              │  (Frontend)  │
              └──────┬──────┘
                     │ REST API
              ┌──────▼──────┐
              │   Railway    │  ← FastAPI backend (free $5/mo credit)
              │  (Backend)   │    + Chroma vector DB
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  Groq API    │  ← Llama 3.3 70B (free tier, 700 tokens/sec)
              │  (Inference) │    14,400 req/day
              └─────────────┘
```

**Why this wins:**
- Vercel → best-in-class frontend hosting, zero config, instant deploys
- Railway → persistent disk (Chroma needs this), always-on, Python-friendly
- Groq → fastest free LLM inference, production-grade quality
- No cold starts on Railway paid ($5/mo credit = effectively free for portfolio)
- Globally accessible public URL from day 1

### Trade-offs
| Decision | What We Gain | What We Lose |
|----------|-------------|--------------|
| Vercel + Railway (split) | Speed, scalability, cool UI | Slightly more setup complexity |
| Groq over Ollama in prod | 70B model quality, zero GPU cost | External API dependency |
| Railway over Render | Always-on, persistent disk | Uses $5/mo free credit |

---

## 3. UI Decision

### Options Evaluated

| Framework | Interactivity | Visual Quality | Dev Speed | Verdict |
|-----------|---------------|----------------|-----------|---------|
| Streamlit | Low-Medium | OK | ⚡ Fast | MVP only |
| Gradio | Low | ML-focused | ⚡ Fast | ML demo, limited |
| Next.js + Tailwind | High | ✅ Excellent | Medium | ✅ Final UI |
| Next.js + shadcn/ui | High | ✅ Professional | Medium | ✅ Final UI |

### ✅ CHOSEN: Two-Phase UI Strategy

**Phase 1 (MVP — Week 1-2): Streamlit**
- Fast to build, ship in days
- Focus on RAG logic, not UI
- Custom CSS for visual polish
- Good enough for first testers

**Phase 2 (Polish — Week 3-4): Next.js + TailwindCSS + shadcn/ui**
- Full custom UI experience
- Framer Motion for smooth animations
- Real-time streaming responses (token streaming)
- Interactive confidence score visualizations
- Animated Contradiction Radar
- Knowledge Graph view (optional)
- Dark mode (NEXUS aesthetic)

### UI Feature Breakdown

```
┌─────────────────────────────────────────────────────┐
│  NEXUS — The Institutional Memory Engine             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                       │
│  📁 Document Zone          💬 Chat Interface          │
│  ┌─────────────────┐      ┌─────────────────────┐   │
│  │ Drop PDFs here  │      │ Ask anything...      │   │
│  │                 │      │                      │   │
│  │ ✅ Q4_Report.pdf│      │ [User] What does     │   │
│  │ ✅ Policy_v2.doc│      │ our policy say about │   │
│  │ ⚠️  HR_2022.pdf │      │ remote work?         │   │
│  └─────────────────┘      │                      │   │
│                            │ [NEXUS] Based on 3   │   │
│  🎯 Insights Panel         │ documents, I found   │   │
│  ┌─────────────────┐      │ 2 conflicting rules: │   │
│  │ ⚡ 2 Contradictions│    │                      │   │
│  │ 🔍 3 Gaps Found  │     │ 🔴 CONTRADICTION     │   │
│  │ 🔗 5 Connections │     │ Doc A says X         │   │
│  └─────────────────┘      │ Doc B says Y         │   │
│                            │                      │   │
│  📊 Confidence: 87%        │ Confidence: 87% ████ │   │
└─────────────────────────────────────────────────────┘
```

### Interactive UI Features
- **Token streaming** — answers appear word by word (ChatGPT feel)
- **Confidence bar** — animated progress bar on every response
- **Contradiction badge** — pulsing red badge when conflicts detected
- **Source cards** — clickable expandable source attribution
- **Gap alert** — animated yellow warning when knowledge gap detected
- **Dark mode** — deep navy/slate (NEXUS institutional feel)
- **Document upload** — drag-and-drop with processing animation
- **Insight sidebar** — live-updating panel with contradictions and connections

---

## 4. Full System Architecture

```
┌─────────────────── NEXUS System ─────────────────────┐
│                                                        │
│  FRONTEND (Vercel - Next.js)                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │  pages/                                          │  │
│  │    index.tsx         → Landing + Upload          │  │
│  │    chat.tsx          → Chat Interface            │  │
│  │    insights.tsx      → Contradiction/Gap Panel   │  │
│  │  components/                                     │  │
│  │    DocumentZone      → Drag-drop upload          │  │
│  │    ChatWindow        → Streaming chat            │  │
│  │    ConfidenceBar     → Animated score            │  │
│  │    ContradictionCard → Conflict display          │  │
│  │    SourceCard        → Expandable citations      │  │
│  │    InsightSidebar    → Live insights panel       │  │
│  └─────────────────────────────────────────────────┘  │
│                          │ HTTP / SSE streaming        │
│  BACKEND (Railway - FastAPI)                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │  api/                                            │  │
│  │    POST /upload      → Ingest documents          │  │
│  │    POST /chat        → RAG query (streaming)     │  │
│  │    GET  /insights    → Contradictions + gaps     │  │
│  │    GET  /health      → Health check              │  │
│  │                                                  │  │
│  │  core/                                           │  │
│  │    ingestion.py      → PDF/DOCX → chunks         │  │
│  │    embeddings.py     → all-MiniLM-L6-v2          │  │
│  │    retrieval.py      → BM25 + semantic hybrid    │  │
│  │    contradiction.py  → Conflict detection        │  │
│  │    gap_detection.py  → Missing info detection    │  │
│  │    insights.py       → Cross-doc connections     │  │
│  │    transparency.py   → Confidence scoring        │  │
│  │                                                  │  │
│  │  db/                                             │  │
│  │    chroma_store.py   → Vector DB (persistent)   │  │
│  └─────────────────────────────────────────────────┘  │
│                          │                             │
│  INFERENCE (Groq API)                                 │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Model: Llama 3.3 70B                            │  │
│  │  Speed: 700+ tokens/sec                          │  │
│  │  Limit: 14,400 req/day (free)                    │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  STORAGE (Railway Persistent Disk)                    │
│  ┌─────────────────────────────────────────────────┐  │
│  │  /data/chroma/       → Vector embeddings         │  │
│  │  /data/raw/          → Original documents        │  │
│  │  /data/processed/    → Chunked text cache        │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow

### Document Ingestion Flow
```
User uploads PDF/DOCX
        │
        ▼
FastAPI POST /upload
        │
        ▼
Unstructured → Extract text, tables, metadata
        │
        ▼
LangChain TextSplitter → Chunks (512 tokens, 50 overlap)
        │
        ▼
all-MiniLM-L6-v2 → 384-dim embeddings
        │
        ├──→ Chroma (vector store)
        └──→ BM25 index (keyword retrieval)
```

### Query / Chat Flow
```
User asks question
        │
        ▼
FastAPI POST /chat (streaming)
        │
        ▼
Hybrid Retrieval
  ├── BM25 search (keyword match)
  └── Semantic search (Chroma cosine similarity)
        │ Re-rank + merge (top-k=5)
        ▼
Contradiction Radar
  └── Check retrieved chunks for conflicts
        │
        ▼
Knowledge Gap Detector
  └── Does context fully answer the question?
        │
        ▼
Build RAG prompt with context + transparency instructions
        │
        ▼
Groq API (Llama 3.3 70B) → Stream tokens back
        │
        ▼
SSE stream to Next.js frontend
  └── Token-by-token display
  └── Confidence score extracted
  └── Sources displayed
  └── Contradiction badge triggered if needed
```

---

## 6. API Design

### Endpoints

```
POST /upload
  Body: multipart/form-data { files: File[] }
  Response: { 
    document_ids: string[], 
    chunks_indexed: number, 
    processing_time_ms: number 
  }

POST /chat (Server-Sent Events)
  Body: { 
    question: string, 
    session_id: string,
    transparency_mode: boolean
  }
  Stream: {
    type: "token" | "metadata" | "done"
    content: string
    sources?: Source[]
    confidence?: number
    contradictions?: Contradiction[]
    gaps?: Gap[]
  }

GET /insights
  Response: {
    contradictions: Contradiction[],
    gaps: Gap[],
    connections: Connection[],
    document_count: number
  }

GET /health
  Response: { status: "ok", chroma_docs: number }
```

---

## 7. Deployment Steps

### Backend (Railway)
```bash
# 1. Create Railway project
railway init

# 2. Add persistent volume at /data

# 3. Set environment variables
GROQ_API_KEY=...
CHROMA_PATH=/data/chroma
ALLOWED_ORIGINS=https://your-app.vercel.app

# 4. Deploy
railway up

# Result: https://nexus-backend.railway.app
```

### Frontend (Vercel)
```bash
# 1. Create Next.js app
npx create-next-app@latest nexus-frontend

# 2. Set env
NEXT_PUBLIC_API_URL=https://nexus-backend.railway.app

# 3. Deploy
vercel --prod

# Result: https://nexus.vercel.app
```

---

## 8. Tech Stack Summary

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 14 + TypeScript | Best UI, App Router, SSE support |
| Styling | TailwindCSS + shadcn/ui | Fast, professional, dark mode |
| Animations | Framer Motion | Smooth interactions |
| Backend | FastAPI + Python | Async, fast, LangChain compatible |
| RAG Framework | LangChain | Industry standard, all integrations |
| Document parsing | Unstructured | Best PDF/DOCX extraction |
| Embeddings | all-MiniLM-L6-v2 | Free, fast, 384-dim, runs on CPU |
| Vector DB | Chroma | Free, local, persistent |
| Keyword search | BM25 (rank_bm25) | Hybrid retrieval accuracy |
| LLM | Groq → Llama 3.3 70B | Free, fastest inference |
| Frontend deploy | Vercel | Free, best DX, global CDN |
| Backend deploy | Railway | $5 credit, persistent disk, always-on |

**Total cost: $0** (Railway $5/mo credit > usage for demo scale)

---

## 9. Trade-off Analysis

| Decision | Alternatives | Why We Chose This |
|----------|-------------|-------------------|
| Railway over Render | Render free tier | Render has 30s cold starts; Railway always-on |
| Groq over OpenAI | OpenAI API | Groq is free, 10x faster for demos |
| Next.js over Streamlit | Keep Streamlit | Streamlit can't do real streaming UI, limited animations |
| Chroma over Pinecone | Pinecone free tier | Chroma runs locally, no API limits, $0 |
| all-MiniLM over OpenAI embeddings | OpenAI text-embedding | All-MiniLM is free, runs on CPU, great quality |

---

## 10. What To Revisit As NEXUS Grows

| When | What to revisit |
|------|-----------------|
| >100 users/day | Upgrade Railway to paid, add Redis caching |
| >10k documents | Switch Chroma → Weaviate or Qdrant for scale |
| >500 req/day | Groq rate limits → add LiteLLM router + fallback |
| First paying client | Add auth (Clerk) + multi-tenant document isolation |
| V2 features | Add PostgreSQL for session memory + user history |

---

## 11. Week-by-Week Build Plan (Updated)

| Week | Focus | Output |
|------|-------|--------|
| 1 | FastAPI backend + Chroma + ingestion pipeline | `/upload` works locally |
| 2 | RAG query + Contradiction Radar + Gap Detection | Full local demo working |
| 3 | Next.js frontend + streaming + deploy to Railway+Vercel | Live URL online |
| 4 | Polish UI (animations, dark mode, insight sidebar) + README | Portfolio-ready |

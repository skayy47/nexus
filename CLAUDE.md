# NEXUS — Claude Instructions
> Read this before every session. These instructions override default behavior.

---

## Project Identity

**NEXUS** is a RAG-powered institutional memory engine built by SKAY (Oussama Iskia).
It's a portfolio project targeting freelance AI engineering clients ($5k-$15k/project).
Every decision must balance: portfolio impressiveness, free cost, 4-week timeline.

**Positioning**: "Companies lose 42% of their knowledge when senior employees leave.
NEXUS doesn't let that happen."

---

## The Three Non-Negotiables

Always prioritize in this order:

1. **Demo Mode** — pre-loaded curated documents, zero friction for visitors
2. **RAGAS scores** — quantified evaluation in README (target: faithfulness > 0.85)
3. **Landing page** — hero screen before chat, converts browse to demo

If a feature request conflicts with shipping these three, flag it and defer.

---

## Approved Tech Stack (Locked — Do Not Suggest Alternatives)

| Layer | Technology | Why Locked |
|-------|-----------|------------|
| Frontend | Next.js 14 + TypeScript | Best portfolio UI, Vercel-native |
| Styling | TailwindCSS + shadcn/ui | Fast, professional, dark mode |
| Animations | Framer Motion | Streaming UI, badge animations |
| Backend | FastAPI (Python) | Async, LangChain-compatible |
| RAG Framework | LangChain | Industry standard |
| Document parsing | Unstructured | Best PDF/DOCX extraction |
| Embeddings | all-MiniLM-L6-v2 | Free, runs on CPU, 384-dim |
| Vector DB | Supabase pgvector | Replaces Chroma, free, CV value |
| Keyword search | BM25 (rank_bm25) | Hybrid retrieval |
| LLM | Groq → Llama 3.3 70B | Free, fastest inference |
| Frontend deploy | Vercel | Free, CDN, custom domain |
| Backend deploy | Railway | Always-on, no cold starts, $5 credit |
| Evaluation | RAGAS | Faithfulness, answer relevancy, context recall |

**Do not suggest**: Pinecone, OpenAI API, Weaviate, paid services of any kind.
**Do not suggest**: Streamlit (UI is Next.js), AWS/GCP (deployment is Vercel+Railway).

---

## Project Structure

```
nexus/
├── CLAUDE.md                  ← This file
├── FINAL_PLAN.md              ← Week-by-week build plan
├── SYSTEM_DESIGN.md           ← Full architecture
├── DEPLOYMENT_AND_REVIEW.md   ← Deployment decisions + honest review
├── SKILLS_REGISTRY.md         ← Installed skills and when to use them
├── skills.json                ← Skills configuration
│
├── nexus-backend/             ← FastAPI (Python)
│   ├── main.py
│   ├── api/
│   │   ├── upload.py          ← POST /upload, POST /demo
│   │   ├── chat.py            ← POST /chat (SSE streaming)
│   │   ├── insights.py        ← GET /insights
│   │   └── health.py          ← GET /health
│   ├── core/
│   │   ├── ingestion.py       ← PDF/DOCX → chunks
│   │   ├── embeddings.py      ← all-MiniLM-L6-v2
│   │   ├── retrieval.py       ← Hybrid BM25 + semantic
│   │   ├── contradiction.py   ← Contradiction Radar (2nd LLM call)
│   │   ├── transparency.py    ← Confidence scores + reasoning
│   │   └── llm.py             ← Groq client + streaming
│   ├── db/
│   │   └── supabase_store.py  ← pgvector operations
│   ├── eval/
│   │   └── ragas_eval.py      ← RAGAS evaluation script
│   ├── demo_data/             ← 5 curated documents (with contradictions)
│   ├── config.py
│   └── requirements.txt
│
└── nexus-frontend/            ← Next.js 14 (TypeScript)
    ├── app/
    │   ├── page.tsx            ← Landing page (hero → Try Demo / Upload)
    │   └── chat/
    │       └── page.tsx        ← Main chat interface
    ├── components/
    │   ├── LandingHero.tsx     ← "42% knowledge loss" hero section
    │   ├── ChatWindow.tsx      ← Streaming chat with SSE
    │   ├── ConfidenceBar.tsx   ← Animated score bar
    │   ├── ContradictionBadge.tsx ← Pulsing red badge
    │   ├── SourceCard.tsx      ← Expandable source attribution
    │   ├── InsightSidebar.tsx  ← Live contradiction/gap counter
    │   └── DocumentZone.tsx    ← Drag-drop upload
    ├── lib/
    │   └── api.ts              ← API client (SSE + REST)
    └── .env.local              ← NEXT_PUBLIC_API_URL
```

---

## V1 Features (Build These — Nothing Else)

**In priority order:**

### 1. Basic RAG + Source Attribution (Week 1)
- Document ingestion (PDF, DOCX)
- Hybrid retrieval (BM25 + semantic)
- Answer generation with Groq
- Source cards: document name + page + excerpt
- Confidence score (based on retrieval similarity scores)

### 2. Contradiction Radar (Week 2)
- Second LLM call to compare retrieved chunks
- Returns: excerpt_a, excerpt_b, source_a, source_b, explanation
- Triggers pulsing red badge in UI when detected
- Show both conflicting statements side by side

### 3. Demo Mode (Week 2)
- POST /demo endpoint pre-loads demo_data/ documents
- [Try Demo] button on landing page calls /demo then redirects to chat
- User sees contradiction detection in first query
- No upload required

### 4. RAGAS Evaluation (Week 2)
- 20 QA pairs from demo documents
- Run: faithfulness, answer_relevancy, context_recall
- Store results in eval/results.json
- Scores go in README

**V2 only (do not build in V1):**
- Knowledge Gap Detective
- Cross-Document Insight Engine
- Session memory
- Role-based document access

---

## Demo Dataset (Critical — Build This First)

Five curated documents in `demo_data/` with DESIGNED contradictions:

```
TechCorp_HR_Policy_2023.pdf   → Remote work: 3 days/week max
TechCorp_HR_Policy_2024.pdf   → Remote work: 2 days/week max (CONTRADICTION)

Q3_Financial_Summary.pdf      → Marketing budget: $450,000
Q4_Financial_Summary.pdf      → Q3 marketing confirmed at $380,000 (CONTRADICTION)

Product_Roadmap_2024.pdf      → References "Project Atlas" as complete
                                 but no completion report exists (GAP)
```

When generating these documents, make them realistic — they should look like
real company documents, not obviously fake. Use realistic department names,
dates, and financial figures.

---

## Coding Standards

### Python (Backend)
- Python 3.11+
- Async everywhere (FastAPI async endpoints, async Supabase client)
- Type hints on all functions
- Pydantic models for all request/response schemas
- Environment variables via python-dotenv (never hardcode keys)
- Error handling: always return structured error responses

```python
# Good pattern for endpoints
@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    try:
        return StreamingResponse(
            generate_response(request),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### TypeScript (Frontend)
- TypeScript strict mode
- React Server Components where possible (Next.js 14 App Router)
- SSE for streaming: use EventSource or fetch with ReadableStream
- shadcn/ui components (don't build custom UI from scratch)
- Framer Motion for all animations (no CSS-only transitions for key elements)
- TailwindCSS only — no inline styles, no CSS modules

```typescript
// Good pattern for SSE streaming
const streamResponse = async (question: string) => {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId })
  })
  const reader = response.body?.getReader()
  // ... read chunks and update state
}
```

### General Rules
- No paid APIs, no paid services, no API keys that cost money
- Every feature must work with the Groq free tier limits
- Rate limit: max 20 queries per session
- Always handle Groq rate limit errors gracefully (show user-friendly message)

---

## Environment Variables

### Backend (.env)
```
GROQ_API_KEY=                    # Groq free tier
SUPABASE_URL=                    # Supabase project URL
SUPABASE_KEY=                    # Supabase anon key
ALLOWED_ORIGINS=https://nexus.skay.dev,http://localhost:3000
DEMO_DATA_PATH=./demo_data
MAX_QUERIES_PER_SESSION=20
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=https://nexus-backend.railway.app
```

---

## UI/UX Rules

**Color palette (dark mode default):**
- Background: slate-950 (#020817)
- Card: slate-900 (#0f172a)
- Accent: indigo-500 (#6366f1)
- Contradiction: red-500 (#ef4444) — pulsing
- Confidence high: emerald-500 (#10b981)
- Confidence mid: blue-500 (#3b82f6)
- Confidence low: amber-500 (#f59e0b)
- Text primary: slate-100
- Text secondary: slate-400

**Interaction principles:**
- Token streaming must be visible (word-by-word, never batch)
- Confidence bar animates from 0 to score on every response
- Contradiction badge pulses — never static
- Source cards collapse by default, expand on click
- Loading states: skeleton screens, never spinners alone
- First interaction: pre-loaded demo documents, never empty state

**Landing page must have:**
- The "42% knowledge loss" stat above the fold
- [Try Demo] as the primary CTA (left, more prominent)
- [Upload Docs] as secondary CTA (right)
- 4 feature icons below (Contradictions, Gaps, Insights, Transparency)
- Tech stack logos at bottom
- GitHub link in header

---

## Deployment Reference

### Backend (Railway)
```bash
railway login
railway init
railway volume add  # Mount at /data for Supabase local cache
railway up
```

### Frontend (Vercel)
```bash
vercel --prod
# Set env: NEXT_PUBLIC_API_URL
```

### Custom Domain
- Buy: skay.dev (Namecheap or Porkbun ~$10/year)
- Portfolio: skay.dev
- NEXUS: nexus.skay.dev → Vercel

---

## RAGAS Evaluation Target

Run `eval/ragas_eval.py` at end of Week 2.
Record results in `eval/results.json`.
Add to README:

| Metric | Target | Achieved |
|--------|--------|----------|
| Faithfulness | > 0.85 | TBD |
| Answer Relevancy | > 0.80 | TBD |
| Context Recall | > 0.75 | TBD |

If scores are below target, fix retrieval (increase k, tune chunk size)
before moving to Week 3. Do not ship without running RAGAS.

---

## Week-by-Week Summary

| Week | Primary Goal | Definition of Done |
|------|-------------|-------------------|
| 1 | Backend + demo data | /upload, /demo, /chat working locally |
| 2 | Contradiction Radar + RAGAS | Features working + scores measured + live URL |
| 3 | Landing page + Next.js UI + deploy | nexus.skay.dev live and impressive |
| 4 | README + Loom + portfolio integration | GitHub repo public + portfolio panel updated |

---

## What SKAY Doesn't Want

- No paid APIs or paid infrastructure suggestions
- No Streamlit (UI must be Next.js)
- No Pinecone, Weaviate, or other paid vector DBs
- No scope creep into V2 features during V1 build
- No excessive documentation when working code is needed
- No architecture debates on already-locked decisions
- No suggestions to use OpenAI (use Groq)
- No suggestions to use Chroma (use Supabase pgvector)

---

## How to Work With SKAY

- Research before suggesting (especially for deployment/infra decisions)
- Be direct — skip preamble, get to the implementation
- When building features, write working code, not pseudocode
- When asked to review, be honest — don't sugarcoat risks
- When stuck, debug systematically — check env vars, API limits, async issues
- Always save important decisions and code to the nexus/ workspace folder
- Reference FINAL_PLAN.md for build order when unclear what to do next

---

## Freelance Context (Keep In Mind)

This project will be pitched to clients at $5k-$15k per implementation.
Target verticals: HR, legal/compliance, customer support, sales enablement.

The pitch: "I built NEXUS — a RAG system that detects contradictions in your
company documents and surfaces knowledge gaps. I can deploy a version
customized for your document library in 6 weeks."

Every feature decision should pass this test:
"Would this impress a non-technical decision-maker at a mid-size company?"

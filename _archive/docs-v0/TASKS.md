# NEXUS — Task Board
**Project**: RAG-powered Institutional Memory Engine  
**Owner**: SKAY (Oussama Iskia)  
**Timeline**: 4 weeks | **Started**: 2026-04-15 | **Target**: 2026-05-13

---

## Legend
- `[ ]` — todo
- `[x]` — done
- `[~]` — in progress
- `[!]` — blocked

---

## WEEK 1 — Foundation + Demo Dataset
**Goal**: Backend working locally with demo data

### Day 1–2: Demo Dataset
- [ ] Create `nexus-backend/demo_data/` folder
- [ ] Generate `TechCorp_HR_Policy_2023.pdf` (remote: 3 days/week max)
- [ ] Generate `TechCorp_HR_Policy_2024.pdf` (remote: 2 days/week max — CONTRADICTION)
- [ ] Generate `Q3_Financial_Summary.pdf` (marketing budget: $450,000)
- [ ] Generate `Q4_Financial_Summary.pdf` (Q3 spend confirmed at $380,000 — CONTRADICTION)
- [ ] Generate `Product_Roadmap_2024.pdf` (references "Project Atlas" as complete — GAP)
- [ ] Verify contradictions are obvious enough for Llama 3.3 to detect reliably

### Day 3–4: FastAPI Backend Skeleton
- [ ] Init `nexus-backend/` with virtualenv + `requirements.txt`
- [ ] Set up `config.py` with env var loading (python-dotenv)
- [ ] Write `main.py` — FastAPI app with CORS + lifespan
- [ ] Write `api/health.py` — GET /health
- [ ] Write `api/upload.py` — POST /upload, POST /demo
- [ ] Write `api/chat.py` — POST /chat (SSE streaming stub)
- [ ] Write `api/insights.py` — GET /insights (stub)
- [ ] Write `db/supabase_store.py` — pgvector upsert + similarity search
- [ ] Create Supabase project + enable pgvector extension
- [ ] Run migration: `CREATE TABLE documents (id, content, embedding vector(384), metadata jsonb)`

### Day 5: Basic RAG Pipeline
- [ ] Write `core/ingestion.py` — PDF/DOCX → LangChain chunks (512 tokens, 50 overlap)
- [ ] Write `core/embeddings.py` — all-MiniLM-L6-v2 loader (singleton)
- [ ] Write `core/retrieval.py` — BM25 + semantic hybrid (RRF fusion)
- [ ] Write `core/llm.py` — Groq client with SSE streaming
- [ ] Wire full pipeline: upload → chunk → embed → store → retrieve → answer
- [ ] Smoke test: upload a PDF, ask a question, get sourced answer

### Week 1 Gate
- [ ] POST /upload works (PDF/DOCX → Supabase)
- [ ] POST /demo pre-loads demo_data/ in one call
- [ ] POST /chat returns SSE with answer + sources
- [ ] All endpoints return structured errors on failure

---

## WEEK 2 — Contradiction Radar + RAGAS
**Goal**: 2 features working + RAGAS scores measured

### Day 1–2: Contradiction Radar
- [ ] Write `core/contradiction.py` — second LLM call, chunk comparison
- [ ] Contradiction prompt: compare top-6 retrieved chunks
- [ ] Return schema: `{excerpt_a, excerpt_b, source_a, source_b, explanation}` or `null`
- [ ] Wire into `/chat` — contradiction metadata attached after streamed answer
- [ ] Test on HR policy query: confirm contradiction is detected

### Day 3: Radical Transparency
- [ ] Write `core/transparency.py` — confidence scoring from similarity scores
- [ ] Confidence schema: `{score: float, reasoning: str, sources: [{name, page, excerpt}]}`
- [ ] Wire into `/chat` response envelope
- [ ] Test: high-confidence query vs low-confidence query

### Day 4–5: RAGAS Evaluation
- [ ] Write `eval/ragas_eval.py` — evaluation harness
- [ ] Create `eval/test_cases.json` — 20 QA pairs from demo documents
- [ ] Run eval: faithfulness, answer_relevancy, context_recall
- [ ] Save results to `eval/results.json`
- [ ] If faithfulness < 0.85: tune chunk size and k, re-run
- [ ] Add scores to README table

### Week 2 Gate
- [ ] Contradiction Radar fires on HR policy / Q3 vs Q4 queries
- [ ] RAGAS: faithfulness > 0.85, relevancy > 0.80, recall > 0.75
- [ ] Live URL exists (Railway backend deployed, even with basic UI)

---

## WEEK 3 — Landing Page + Next.js Frontend
**Goal**: nexus.skay.dev live and impressive

### Day 1: Landing Page
- [ ] Init `nexus-frontend/` — Next.js 14, TypeScript, Tailwind, shadcn/ui
- [ ] Install Framer Motion
- [ ] Write `components/LandingHero.tsx` — "42% knowledge loss" stat above fold
- [ ] [Try Demo] CTA → POST /demo → redirect to /chat
- [ ] [Upload Docs] CTA → /chat with upload mode
- [ ] 4 feature icons: Contradictions, Gaps, Insights, Transparency
- [ ] Tech stack logos footer + GitHub link in header
- [ ] Dark mode default (slate-950 bg, indigo-500 accent)

### Day 2–3: Chat Interface
- [ ] Write `components/ChatWindow.tsx` — SSE streaming (word-by-word)
- [ ] Write `components/ConfidenceBar.tsx` — Framer Motion 0→score animation
- [ ] Write `components/ContradictionBadge.tsx` — pulsing red badge on conflict
- [ ] Write `components/SourceCard.tsx` — collapsible, expand on click
- [ ] Write `components/InsightSidebar.tsx` — live contradiction/gap counter
- [ ] Write `components/DocumentZone.tsx` — drag-drop upload (react-dropzone)
- [ ] Write `lib/api.ts` — typed API client (SSE + REST)
- [ ] Skeleton loading states (no bare spinners)
- [ ] Max 20 queries per session enforced in UI
- [ ] Graceful Groq rate-limit error message

### Day 4–5: Deployment
- [ ] Railway: deploy backend, set env vars, mount persistent disk
- [ ] Supabase: confirm pgvector works in prod (not just local)
- [ ] Vercel: deploy frontend, set NEXT_PUBLIC_API_URL
- [ ] Custom domain: point nexus.skay.dev to Vercel
- [ ] End-to-end smoke test on prod URL

### Week 3 Gate
- [ ] nexus.skay.dev loads and renders in < 3s
- [ ] [Try Demo] → contradiction visible in first query
- [ ] Token streaming visible (word-by-word, not batch)
- [ ] Confidence bar animated on every response
- [ ] All dark mode, no light mode bleed

---

## WEEK 4 — README + Polish + Launch
**Goal**: Portfolio-ready, pitch-ready, GitHub-ready

### Day 1–2: README
- [ ] Write top-level README.md — full structure per FINAL_PLAN.md
- [ ] Add 30s GIF of contradiction detection in action
- [ ] Embed RAGAS scores table (from eval/results.json)
- [ ] Add ASCII architecture diagram (from SYSTEM_DESIGN.md)
- [ ] Clear 5-step local setup instructions

### Day 3: Loom Video
- [ ] Record 2-min Loom: landing → demo → contradiction → sources → close
- [ ] Embed link in README

### Day 4: Rate Limiting + Error Handling
- [ ] Backend: 20 queries/session, 20MB max file size, Groq timeout handling
- [ ] Backend: Supabase connection error fallback (graceful degradation)
- [ ] Frontend: all error states have user-friendly messages, no raw errors shown

### Day 5: Portfolio Integration
- [ ] Update portfolio NEXUS panel: RAGAS score badge, tech stack, [Live Demo] + [GitHub]
- [ ] Make GitHub repo public
- [ ] Verify nexus.skay.dev stable and fast

### Week 4 Gate
- [ ] GitHub repo public with complete README
- [ ] Loom video embedded
- [ ] nexus.skay.dev live, stable, impressive
- [ ] Portfolio panel updated

---

## Icebox (V2 — Do Not Start Until V1 Ships)
- [ ] Knowledge Gap Detective
- [ ] Cross-Document Insight Engine
- [ ] Session memory / conversation history
- [ ] Role-based document access
- [ ] Multi-tenant support

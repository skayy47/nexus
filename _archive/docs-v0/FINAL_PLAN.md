# NEXUS — Final Plan Before Build
**Locked**: 2026-04-15 | **Status**: Ready to Execute

---

## The Three Non-Negotiables

Everything in this plan is built around these three things.
If a feature isn't serving one of them, it gets cut or delayed.

```
1. DEMO MODE      → Visitors experience magic in one click, zero effort
2. RAGAS SCORES   → Quantified proof your RAG pipeline is production-grade
3. LANDING PAGE   → First 5 seconds convert a browse into a demo
```

---

## WEEK 1 — Foundation + Demo Documents

### Goal: Backend working locally with demo data

**Day 1-2: Build the Demo Dataset (Do This First)**

Before writing a single line of RAG code, create the documents
that will make NEXUS look incredible in demos.

Create `demo_data/` folder with these 5 files:

```
demo_data/
  TechCorp_HR_Policy_2023.pdf    ← "Remote work allowed up to 3 days/week"
  TechCorp_HR_Policy_2024.pdf    ← "Remote work capped at 2 days/week"
                                    (CONTRADICTION with 2023 version)

  Q3_Financial_Summary.pdf       ← "Marketing budget: $450,000"
  Q4_Financial_Summary.pdf       ← "Q3 marketing spend confirmed at $380,000"
                                    (CONTRADICTION in reported numbers)

  Product_Roadmap_2024.pdf       ← References "Project Atlas" as complete
                                    but no completion report exists
                                    (KNOWLEDGE GAP — triggers Gap Detective)
```

These documents are DESIGNED to showcase NEXUS features.
Every demo, every client call, every portfolio visit uses these.

**Day 3-4: FastAPI Backend Skeleton**

```
nexus-backend/
  main.py              ← FastAPI app entry point
  api/
    upload.py          ← POST /upload, POST /demo (loads demo_data/)
    chat.py            ← POST /chat (SSE streaming)
    insights.py        ← GET /insights
    health.py          ← GET /health
  core/
    ingestion.py       ← PDF/DOCX → chunks (LangChain + Unstructured)
    embeddings.py      ← all-MiniLM-L6-v2 (sentence-transformers)
    retrieval.py       ← Hybrid BM25 + semantic search
    llm.py             ← Groq client (Llama 3.3 70B) with streaming
  db/
    supabase_store.py  ← pgvector operations (upsert, similarity search)
  config.py            ← Env vars (GROQ_API_KEY, SUPABASE_URL, etc.)
  requirements.txt
```

**Day 5: Basic RAG Pipeline Working**

Milestone: Can upload a PDF, ask a question, get an answer with sources.
This is the minimum before Week 2. Nothing fancy yet.

**End of Week 1 Checklist:**
- [ ] Demo dataset created (5 documents with built-in contradictions/gaps)
- [ ] /upload endpoint works (PDF/DOCX → Supabase pgvector)
- [ ] /demo endpoint pre-loads demo_data/ in one call
- [ ] /chat endpoint returns answers with source attribution
- [ ] Basic RAG pipeline tested on demo documents

---

## WEEK 2 — Contradiction Radar + RAGAS Evaluation

### Goal: 2 features working + RAGAS scores measured

**Day 1-2: Contradiction Radar**

This is the hardest feature. Here's the exact implementation approach:

```python
# contradiction.py — How it works

# Step 1: Retrieve top-k chunks for the query
chunks = hybrid_retrieve(query, k=6)

# Step 2: Second LLM call — compare chunks against each other
contradiction_prompt = """
You are analyzing document excerpts for contradictions.

Excerpts:
{chunks}

Are there any factual contradictions between these excerpts?
If yes, return:
  - excerpt_a: (the first conflicting statement)
  - excerpt_b: (the conflicting statement)
  - source_a: (document name)
  - source_b: (document name)
  - explanation: (why they conflict)

If no contradictions, return: null
"""

# Step 3: Stream answer first, attach contradiction metadata after
```

This costs 2 Groq calls per query. Still within free tier limits.

**Day 3: Radical Transparency (Source Attribution)**

Every answer must include:
- Confidence score (0.0 → 1.0) based on retrieval similarity scores
- Source documents used (filename + page number)
- Plain English explanation: "I based this on 3 documents. Confidence is
  high because multiple sources agree."

**Day 4-5: RAGAS Evaluation (Non-Negotiable)**

```python
# eval/ragas_eval.py

# Build 20 QA pairs from demo documents:
test_cases = [
  {
    "question": "What is TechCorp's remote work policy?",
    "ground_truth": "Policy changed from 3 days/week (2023) to 2 days/week (2024)"
  },
  {
    "question": "What was the Q3 marketing budget?",
    "ground_truth": "Q3 financial summary states $450,000 but Q4 report confirms $380,000"
  },
  # ... 18 more
]

# Metrics to measure:
# - faithfulness        (does answer match the docs?)
# - answer_relevancy    (does answer address the question?)
# - context_recall      (did retrieval find the right chunks?)
```

Target scores to aim for:
- Faithfulness: > 0.85
- Answer Relevancy: > 0.80
- Context Recall: > 0.75

**End of Week 2 Checklist:**
- [ ] Contradiction Radar working on demo documents
- [ ] Source attribution on every response
- [ ] Confidence score calculated and returned
- [ ] RAGAS evaluation script written
- [ ] 20 QA test pairs created from demo documents
- [ ] RAGAS scores measured and recorded
- [ ] Live URL deployed (even just Railway backend + basic Streamlit)

**Week 2 Milestone: Live URL exists.**
Even if it's ugly. Ship it.

---

## WEEK 3 — Landing Page + Next.js Frontend

### Goal: Beautiful UI that converts portfolio visitors

**Day 1: Landing Page (This Is The First Thing Visitors See)**

When someone clicks the NEXUS panel on your portfolio, they land here:

```
┌────────────────────────────────────────────────┐
│                                                  │
│  ████  NEXUS                          [GitHub]  │
│                                                  │
│     Companies lose 42% of their                 │
│     knowledge when senior employees leave.       │
│                                                  │
│     NEXUS doesn't let that happen.              │
│                                                  │
│         [  Try Demo  ]  [  Upload Docs  ]       │
│                                                  │
│  ─────────────────────────────────────────────  │
│                                                  │
│  🔴 Contradictions   🔍 Knowledge Gaps          │
│  🔗 Hidden Insights  ✅ Source Attribution       │
│                                                  │
│  Powered by Llama 3.3 70B · Built by SKAY       │
│                                                  │
└────────────────────────────────────────────────┘
```

[Try Demo] → loads demo_data/ automatically → goes to chat
[Upload Docs] → goes to chat with upload mode

**Day 2-3: Chat Interface (The Main App)**

Key interactive UI elements:

```
STREAMING: Token-by-token response (SSE from FastAPI → Next.js)
           Users see words appear in real time — feels alive

CONFIDENCE BAR: Animated bar under every response
                < 60%  →  yellow "Low confidence"
                60-85% →  blue  "Moderate confidence"
                > 85%  →  green "High confidence"

CONTRADICTION BADGE: Pulsing red badge appears when conflict detected
                     Click to expand and see both conflicting excerpts

SOURCE CARDS: Collapsible cards under every answer
              Shows document name, page, and the exact excerpt used

INSIGHT SIDEBAR: Updates live as conversation progresses
                 Shows count of contradictions, gaps, connections found
```

**Day 4-5: Deployment**

```bash
# Frontend → Vercel
cd nexus-frontend
vercel --prod
# Set: NEXT_PUBLIC_API_URL = https://nexus-backend.railway.app

# Backend → Railway
railway up
# Set: GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY, ALLOWED_ORIGINS

# Custom domain
# nexus.skay.dev → point to Vercel deployment
```

**End of Week 3 Checklist:**
- [ ] Landing page live at nexus.skay.dev
- [ ] [Try Demo] loads demo docs and takes user to chat
- [ ] Token streaming working (real-time word-by-word)
- [ ] Confidence bar animated and accurate
- [ ] Contradiction badge appears on relevant queries
- [ ] Source cards expandable
- [ ] Dark mode default
- [ ] Backend deployed on Railway (persistent disk)
- [ ] Frontend deployed on Vercel
- [ ] Supabase pgvector connected and working in prod

---

## WEEK 4 — README + Polish + Launch

### Goal: Portfolio-ready, pitch-ready, GitHub-ready

**Day 1-2: The README (Your Real CV)**

The GitHub README is what engineers at top AI companies read.
It must have all of these:

```markdown
# NEXUS — Institutional Memory Engine

> Companies lose 42% of their knowledge when senior employees leave.
> NEXUS doesn't let that happen.

[Live Demo](https://nexus.skay.dev) · [Video Walkthrough](loom-link) · [Built by SKAY](portfolio-link)

## What Makes NEXUS Different
[2-paragraph explanation of Contradiction Radar + Source Attribution]

## Demo
[30-second GIF showing contradiction detection in action]

## RAGAS Evaluation Results
| Metric | Score |
|--------|-------|
| Faithfulness | 0.87 |
| Answer Relevancy | 0.83 |
| Context Recall | 0.79 |

## Architecture
[ASCII diagram from SYSTEM_DESIGN.md]

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + TailwindCSS + shadcn/ui |
| Backend | FastAPI + LangChain + Unstructured |
| Vector DB | Supabase pgvector |
| LLM | Groq → Llama 3.3 70B |
| Embeddings | all-MiniLM-L6-v2 |
| Frontend Deploy | Vercel |
| Backend Deploy | Railway |

## Running Locally
[Clear 5-step instructions]
```

**Day 3: Loom Demo Video (2 Minutes)**

Script:
- 0:00-0:20: "NEXUS solves the institutional memory problem..."
- 0:20-0:40: Click [Try Demo] — show the landing page
- 0:40-1:20: Ask "What is our remote work policy?" → watch contradiction detected
- 1:20-1:50: Show source cards, confidence score, contradiction details
- 1:50-2:00: "Built with Groq, Supabase pgvector, deployed on Vercel + Railway"

**Day 4: Rate Limiting + Error Handling**

```python
# Must have before public launch:
- Max 20 queries per session (prevent abuse)
- Graceful "Daily limit reached" message
- Document size limit (20MB max per file)
- Timeout handling (if Groq is slow, show progress indicator)
- Supabase connection error fallback
```

**Day 5: Portfolio Integration**

On your portfolio site, the NEXUS panel should show:
- Project name + one-line description
- Tech stack badges (Next.js, FastAPI, Supabase, Groq)
- RAGAS score ("0.87 faithfulness")
- [Live Demo] and [GitHub] buttons
- A thumbnail of the contradiction detection feature

**End of Week 4 Checklist:**
- [ ] README complete with all sections above
- [ ] Loom demo video recorded and embedded
- [ ] RAGAS scores in README
- [ ] Rate limiting added
- [ ] Error handling complete
- [ ] Portfolio panel updated with NEXUS
- [ ] nexus.skay.dev live and stable
- [ ] GitHub repo public

---

## Priority Order Summary

If time runs short, build in this exact order:

```
1. Demo dataset (5 curated documents)      ← Week 1, Day 1
2. Basic RAG + source attribution          ← Week 1, Day 3-5
3. Contradiction Radar                     ← Week 2, Day 1-2
4. RAGAS evaluation script + scores        ← Week 2, Day 4-5
5. Live URL (even ugly)                    ← End of Week 2
6. Landing page                            ← Week 3, Day 1
7. Streaming chat UI                       ← Week 3, Day 2-3
8. Custom domain (nexus.skay.dev)          ← Week 3, Day 4-5
9. README + Loom video                     ← Week 4, Day 1-3
10. Portfolio integration                  ← Week 4, Day 5
```

Stop at any point where the app is live and impressive.
That's already better than 90% of AI portfolios.

---

## What Success Looks Like

**Week 2 end**: Someone can visit a URL and use basic NEXUS
**Week 3 end**: Someone visits nexus.skay.dev and is genuinely impressed
**Week 4 end**: A hiring manager reads the GitHub README and sends you a message

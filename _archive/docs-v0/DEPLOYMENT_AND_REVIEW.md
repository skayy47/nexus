# NEXUS — Deployment Decision + Honest Strategic Review
**Date**: 2026-04-15 | **Status**: Final

---

## PART 1: DEPLOYMENT DECISION

### Your Context (Important)
Portfolio site → Project panel → Click → NEXUS app opens

This means the FIRST second of the app experience is everything.
A cold start on click = bad first impression = client/hiring manager bounces.

### ✅ Final Deployment Stack

```
Portfolio Site (your domain)
        │
        │ Click on NEXUS panel
        ▼
┌─────────────────────────────┐
│   Vercel (Next.js frontend)  │  ← Loads in <1 second, global CDN
│   nexus.yourdomain.com       │  ← Custom domain (not .vercel.app)
└──────────────┬──────────────┘
               │ API calls (no cold start)
┌──────────────▼──────────────┐
│   Railway (FastAPI backend)  │  ← Always-on container, no cold start
│   Persistent disk for data   │  ← $5/mo free credit covers demo scale
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   Supabase (pgvector)        │  ← Replaces Chroma, always-on, free 1GB
│   PostgreSQL + vector search │  ← Production-grade, massive CV value
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   Groq API (Llama 3.3 70B)  │  ← Free, 700 tokens/sec, no cold start
└─────────────────────────────┘
```

### Why This Wins for Your Portfolio Context

| Criteria | Result |
|----------|--------|
| Click → UI appears | <1 second (Vercel CDN) |
| First API call | No cold start (Railway always-on) |
| Custom domain | nexus.yourdomain.com (professional) |
| Total cost | $0 ($5 Railway credit > demo traffic) |
| CV stack | Next.js + FastAPI + Supabase + Groq + Vercel + Railway |

### On the Custom Domain
Buy a $10/year domain (Namecheap or Porkbun): `skay.dev`

Then:
- Portfolio: `skay.dev`
- NEXUS: `nexus.skay.dev`
- Future projects: `project2.skay.dev`, etc.

This makes every panel click look like a real product launch, not a demo.

---

## PART 2: HONEST REVIEW — THE FULL PICTURE

This is the unfiltered version. Not to discourage — to make sure NEXUS actually lands.

---

### What's Genuinely Strong ✅

**1. The Market Research Is Correct**
RAG is #1 in-demand AI skill in 2026. You're building the right thing.
The positioning ("42% knowledge loss") is emotionally powerful for B2B pitches.
The $5k-$15k project range is validated and realistic.

**2. The Differentiators Are Real**
Contradiction Radar and Knowledge Gap Detective are features that don't exist
in most RAG demos. They're hard to build but they're the reason someone
would choose NEXUS over a generic RAG tool. Don't drop them.

**3. The Free Stack Is Achievable**
Groq + Supabase + Vercel + Railway = $0. This is a legitimate production stack,
not a compromise. Supabase pgvector is what serious teams use.

**4. The Portfolio Panel Idea Is Smart**
Linking directly to a live app from your portfolio is how you convert
a browse into a demo. Most portfolios just show screenshots. You're showing
a working product.

---

### What Concerns Me — The Real Risks ⚠️

**Risk 1: The Demo Document Problem (CRITICAL)**
This is the #1 thing that will make or break NEXUS.

Most people who click on your portfolio panel will NOT upload their own documents.
They'll land on the chat interface, see "Upload a PDF to get started", and leave.

The magic of Contradiction Radar and Gap Detection is INVISIBLE without
the right documents. If someone uploads a random PDF, they probably won't
see any contradictions. They'll think the feature doesn't work.

→ FIX: Build a "Demo Mode" button. Pre-load 3-5 curated documents:
  - HR_Policy_v1.pdf vs HR_Policy_v2.pdf (with built-in contradictions)
  - Q3_Report.pdf vs Q4_Report.pdf (conflicting numbers)
  - Tech_Spec_v1.pdf vs Tech_Spec_v2.pdf

Make the first experience require ZERO effort from the visitor.
One click. Contradictions appear. Jaws drop.

**Risk 2: 4 V1 Features in 2 Weeks Is Too Ambitious**
Contradiction Radar alone is a hard engineering problem.
It requires a separate LLM pass to compare chunks against each other.
This is not a weekend feature.

Building 4 features mediocrely is worse than 2 features excellently.

→ FIX: Cut V1 to 2 features. Do them perfectly.
  - Keep: Contradiction Radar + Source Attribution (Radical Transparency)
  - Move to V2: Knowledge Gap Detection + Cross-Document Insights
  These two are already enough to differentiate NEXUS from every other RAG demo.

**Risk 3: No Evaluation Metrics = Unverifiable Claims**
"NEXUS surfaces institutional wisdom" is marketing.
"NEXUS achieves 0.87 faithfulness and 0.82 answer relevancy on RAGAS" is credibility.

Without a benchmark, a hiring manager at an AI company will assume
your RAG pipeline is average. With a RAGAS score, you stand out
from 90% of RAG portfolio projects.

→ FIX: Add RAGAS evaluation to Week 2. Build a 50-question test set
on your demo documents. Include the scores in your README.

**Risk 4: Next.js Risk If You're Not Already Fluent**
Weeks 3-4 are tight. If you're learning Next.js while building,
the UI polish will slip and the app will ship half-finished.

→ FIX: Decide now. If Next.js is new, stay in Streamlit for the MVP
and add a custom CSS theme to make it look polished.
Ship a working Streamlit app with great UX over a broken Next.js app.
You can always upgrade the frontend after you have your first client.

**Risk 5: Groq Rate Limits Under Real Demo Traffic**
14,400 requests/day sounds like a lot.
In demo mode with multiple concurrent visitors, each RAG query makes
2-4 LLM calls (retrieval + generation + contradiction check + gap detection).
That's 3,600 "real" sessions per day. Fine.

BUT: If your portfolio gets featured anywhere or a client shows their team,
you can exhaust the limit in hours.

→ FIX: Add rate limiting per session (max 20 queries/session).
Add LiteLLM as a router so you can fall back to Ollama or another free API.
Add a "Daily limit reached" graceful error message.

**Risk 6: The README Is Your Real CV**
The live demo matters but hiring managers at top AI companies
will go to your GitHub repo and READ the README.

If the README is just "how to run this locally", you're wasting the opportunity.

→ FIX: The README needs:
  - Problem statement (1 paragraph, business language)
  - Live demo GIF or Loom video (30 seconds)
  - Architecture diagram
  - RAGAS evaluation scores
  - Feature breakdown with "why this matters" for each
  - Tech stack table (this is what recruiters scan)
  - Deployment guide

---

### Strategic Recommendations — Ranked by Impact

**1. Build Demo Mode First (Before Any Feature)**
Don't start with the RAG pipeline.
Start with 5 curated documents with built-in contradictions.
Build the demo experience around those documents.
Everything else is built to make those documents shine.

**2. Cut to 2 Perfect Features**
Contradiction Radar + Source Attribution.
Nail these two. Then ship. Then add features.

**3. Add RAGAS Evaluation**
50 QA pairs on your demo documents.
Run faithfulness, answer_relevancy, context_recall.
Put the scores in the README and the app footer.

**4. Buy skay.dev Today**
$10/year. Changes the entire perception.
nexus.skay.dev vs nexus-skay.vercel.app is a massive difference
for a portfolio visitor making a 10-second hiring decision.

**5. Landing Page Before Chat**
When someone clicks the NEXUS panel in your portfolio:
- They should NOT land on a chat interface
- They should land on a 5-second hero screen:
  "Companies lose 42% of their knowledge when senior employees leave.
   NEXUS doesn't let that happen."
  [Try Demo] [Upload Your Docs]
- Then they enter the app

**6. Record a 2-Minute Loom Demo**
Show the contradiction detection in real time.
Upload two conflicting HR policies. Watch NEXUS flag the conflict.
Embed this in the README and your portfolio panel.
Video proof > live demo for async hiring situations.

---

### The Honest Timeline Assessment

| Week | Planned | Realistic |
|------|---------|-----------|
| 1 | Full pipeline + chat | Document ingestion + basic retrieval ✅ |
| 2 | Deploy + 4 features | 2 features working locally ⚠️ |
| 3 | Cross-doc insights + UI | Deploy working MVP ⚠️ |
| 4 | Polish | Polish + README + demo video ✅ |

The plan is slightly optimistic. That's fine for a solo project.
The key is: ship a live URL by end of Week 2, even if it's just
basic RAG + source attribution. Then iterate.

A live imperfect demo beats a perfect local demo every time.

---

### Final Verdict

NEXUS is a strong portfolio project with the right positioning.
The market research is solid, the differentiators are real,
and the stack you've chosen is legitimate.

The three things that will make or break it:
1. Demo Mode with pre-loaded curated documents (critical)
2. RAGAS evaluation score in the README (credibility)
3. A landing page before the chat (first impression)

Everything else is execution. You have the skills to execute this.

Ship fast, iterate based on tester feedback, and get a live URL
online by end of Week 2. The rest is polish.

---

### One-Line Summary
Build Demo Mode first, ship 2 perfect features by Week 2,
add RAGAS scores to the README, buy skay.dev, and you have
a portfolio project that gets responses.

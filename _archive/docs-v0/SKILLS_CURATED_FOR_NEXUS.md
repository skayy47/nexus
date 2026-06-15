# NEXUS Skills Curation

**Project**: NEXUS — Institutional Memory Engine (RAG-Powered)  
**Timeline**: 4 weeks  
**Created**: 2026-04-15

---

## 🎯 Essential Skills (Install Priority Order)

### Phase 1-2: Core RAG Development

#### 1. **skay-ai-engineer:rag-builder** ⭐ INSTALL IMMEDIATELY
- **Priority**: HIGHEST
- **When to Use**: Week 1-3 (document ingestion, retrieval pipeline)
- **For NEXUS**: Build production-grade RAG with Chroma, LangChain, hybrid retrieval (BM25 + semantic)
- **Key Features to Build**:
  - Document ingestion pipeline (PDF, DOCX)
  - Embedding strategy (all-MiniLM-L6-v2)
  - Contradiction Radar evaluation
  - Knowledge Gap Detection setup
- **Location**: `skay-ai-engineer:rag-builder`

#### 2. **skay-ai-engineer:data-pipeline** ⭐ INSTALL IMMEDIATELY
- **Priority**: HIGHEST
- **When to Use**: Week 1-2 (document processing setup)
- **For NEXUS**: Design document processing pipeline (PDF/DOCX → embeddings → vector DB)
- **Key Features to Build**:
  - LangChain + Unstructured orchestration
  - Batch document processing
  - Embedding pipeline with all-MiniLM-L6-v2
  - Chroma indexing workflow
- **Location**: `skay-ai-engineer:data-pipeline`

#### 3. **skay-ai-engineer:system-design** 
- **Priority**: HIGH
- **When to Use**: Week 1 (architecture decisions)
- **For NEXUS**: Document & justify tech choices
  - Ollama + Llama 3.3 8B locally vs Groq for production
  - Hybrid retrieval strategy (BM25 + semantic)
  - Streamlit MVP → Next.js transition plan
  - Contradiction detection architecture
- **Location**: `skay-ai-engineer:system-design`

---

### Phase 2-3: Feature Development & Polish

#### 4. **skay-ai-engineer:testing-strategy**
- **Priority**: HIGH
- **When to Use**: Week 2-3 (validate V1 differentiators)
- **For NEXUS**: Test your 4 core features
  - Contradiction Radar accuracy
  - Knowledge Gap Detection coverage
  - Cross-Document Insight Engine relevance
  - Radical Transparency Mode (confidence scores correct)
- **Location**: `skay-ai-engineer:testing-strategy`

#### 5. **design:ux-copy**
- **Priority**: MEDIUM
- **When to Use**: Week 2-3 (Streamlit UI refinement)
- **For NEXUS**: Write INFJ-flavored microcopy
  - Button labels (honest, transparent language)
  - Empty states (onboarding)
  - Confidence score explanations
  - Error messages (INFJ "sees what's missing" framing)
- **Location**: `design:ux-copy`

#### 6. **skay-ai-engineer:documentation**
- **Priority**: MEDIUM-HIGH
- **When to Use**: Week 3-4 (README + technical docs)
- **For NEXUS**: Business-value focused documentation
  - README with "42% knowledge loss" positioning
  - Architecture overview (how Contradiction Radar works)
  - Feature explanations (Transparency Mode, Gap Detection)
  - Deployment instructions (Vercel/HF Spaces)
  - Sample use cases for target verticals (HR, legal, customer support)
- **Location**: `skay-ai-engineer:documentation`

---

### Phase 3-4: Freelance Launch

#### 7. **skay-ai-engineer:freelance-proposal**
- **Priority**: MEDIUM (post-MVP)
- **When to Use**: Week 4 (before public launch)
- **For NEXUS**: Frame as reusable service for clients
  - $8,500 pitch template ("Reduce support tickets by 30%")
  - Scope for different verticals
  - ROI calculations
  - Retainer pricing ($1.5k-$3k/month)
- **Location**: `skay-ai-engineer:freelance-proposal`

---

## 📋 Optional Skills (If Time Permits)

#### 8. **skay-ai-engineer:architecture** (Optional)
- **Priority**: LOW
- **When to Use**: Week 1-2 (if you want formal ADRs)
- **For NEXUS**: Document major tech decisions as ADRs
  - "Why Chroma over Pinecone?" (free tier)
  - "Why hybrid retrieval?" (accuracy + performance)
  - "Why Ollama locally vs Groq for demo?"
- **Location**: `skay-ai-engineer:architecture`

#### 9. **marketing:content-creation** (Optional)
- **Priority**: LOW
- **When to Use**: Week 4 (demo video, LinkedIn post, case studies)
- **For NEXUS**: Create launch assets
  - Loom demo script
  - LinkedIn post (positioning)
  - Case study template for first client
- **Location**: `marketing:content-creation`

#### 10. **design:design-critique** (Optional)
- **Priority**: LOW
- **When to Use**: Week 3 (UI feedback)
- **For NEXUS**: Validate Streamlit/Next.js UI
  - Usability feedback
  - Visual hierarchy
  - Consistency with NEXUS brand (honesty, transparency)
- **Location**: `design:design-critique`

---

## 🗓️ Week-by-Week Skill Usage Map

### Week 1: MVP Foundation
- **rag-builder** — Start RAG pipeline
- **data-pipeline** — Set up document processing
- **system-design** — Validate architecture choices

### Week 2: Core Features
- **rag-builder** (continued) — Implement Contradiction Radar, Gap Detection
- **testing-strategy** — Begin feature testing
- **ux-copy** — Streamlit UI copy

### Week 3: Polish & Deploy
- **rag-builder** (continued) — Cross-Document Insights Engine
- **documentation** — Write README
- **design-critique** (optional) — UI feedback
- **testing-strategy** (continued) — Final validation

### Week 4: Launch
- **documentation** (continued) — Final polish
- **freelance-proposal** — Create pitch template
- **marketing:content-creation** (optional) — Demo video, launch post

---

## ✅ Installation Checklist

- [ ] skay-ai-engineer:rag-builder
- [ ] skay-ai-engineer:data-pipeline
- [ ] skay-ai-engineer:system-design
- [ ] skay-ai-engineer:testing-strategy
- [ ] design:ux-copy
- [ ] skay-ai-engineer:documentation
- [ ] skay-ai-engineer:freelance-proposal
- [ ] skay-ai-engineer:architecture (optional)
- [ ] marketing:content-creation (optional)
- [ ] design:design-critique (optional)

---

## 🎯 Quick Start
1. **Today**: Install skills #1-3 (rag-builder, data-pipeline, system-design)
2. **Week 2**: Add skills #4-6
3. **Week 3**: Add skill #7
4. **Week 4**: Use freelance-proposal for client pitching

This lineup gives you expert guidance at every phase of NEXUS development while respecting your 4-week timeline.

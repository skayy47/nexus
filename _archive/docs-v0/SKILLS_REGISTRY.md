# NEXUS Skills Registry

**Project**: NEXUS — Institutional Memory Engine  
**Skills Setup Date**: 2026-04-15  
**Total Installed**: 3 specialized RAG skills + 7 complementary skills

---

## 🚀 Core RAG Skills (Installed via npm)

### 1. **RAG Architect** ⭐
- **Source**: https://github.com/jeffallen/claude-skills
- **Status**: ✅ Installed
- **Phase**: Week 1
- **Purpose**: Design the RAG pipeline architecture for NEXUS
- **Key Tasks**:
  - Design retrieval strategy (hybrid BM25 + semantic)
  - Choose vector DB (Chroma) and embedding model (all-MiniLM-L6-v2)
  - Plan document ingestion pipeline
  - Design Contradiction Radar architecture
  - Plan Knowledge Gap Detection strategy

**When to Use**: Start of Week 1 before implementation
```bash
# Invoke in conversation:
Ask about RAG architecture decisions for NEXUS
```

---

### 2. **RAG Engineer** ⭐
- **Source**: https://github.com/icbn33/antigravity-awesome-skills
- **Status**: ✅ Installed
- **Phase**: Week 2-3
- **Purpose**: Build and optimize the RAG pipeline features
- **Key Tasks**:
  - Implement document ingestion (PDF, DOCX)
  - Set up embeddings pipeline (all-MiniLM-L6-v2)
  - Build Chroma vector store integration
  - Implement Contradiction Radar feature
  - Build Knowledge Gap Detection
  - Implement Cross-Document Insight Engine
  - Add Radical Transparency Mode (confidence scores)

**When to Use**: Mid-project during feature implementation
```bash
# Use for building specific features:
- Contradiction detection implementation
- Embedding optimization
- Retrieval quality tuning
- Source attribution pipeline
```

---

### 3. **RAG Implementation** ⭐
- **Source**: https://github.com/oshoban/agents
- **Status**: ✅ Installed
- **Phase**: Week 3-4
- **Purpose**: Deploy and integrate RAG system into production
- **Key Tasks**:
  - Integrate RAG with Streamlit frontend
  - Build chat interface
  - Set up API endpoints
  - Deploy to Vercel/HF Spaces
  - Connect to Groq API for production
  - Implement session memory and continuity

**When to Use**: Late-stage integration and deployment
```bash
# Use for deployment and integration:
- Streamlit integration
- API endpoint design
- Production deployment
- Frontend-backend communication
```

---

## 📚 Complementary Skills (Internal)

### Supporting Skills from Your Curated Set

| Skill | Purpose | Phase | When to Use |
|-------|---------|-------|------------|
| **system-design** | Validate overall architecture | Week 1 | Before RAG Architect |
| **testing-strategy** | Test RAG features | Week 2-3 | During feature development |
| **ux-copy** | Write UI copy for Streamlit | Week 2-3 | UI refinement |
| **documentation** | Write README & docs | Week 3-4 | During polish phase |
| **freelance-proposal** | Create client pitch | Week 4 | Pre-launch |
| **architecture** | Document ADRs | Week 1-2 | Major decisions |
| **content-creation** | Demo video & launch assets | Week 4 | Marketing |

---

## 🗓️ Week-by-Week Skill Activation Plan

### Week 1: Architecture & Foundation
```
✓ system-design         → Overall architecture decisions
✓ rag-architect         → RAG pipeline design (GitHub skill)
→ rag-engineer          → Start document ingestion
```

**Deliverable**: Architecture diagram, design decisions documented

---

### Week 2-3: Feature Development
```
→ rag-engineer          → Implement core features
  - Contradiction Radar
  - Knowledge Gap Detection
  - Cross-Document Insights
→ testing-strategy      → Test feature quality
→ ux-copy               → Streamlit UI microcopy
```

**Deliverable**: MVP with 4 V1 differentiators working

---

### Week 3-4: Integration & Launch Prep
```
→ rag-implementation    → Deploy & integrate (GitHub skill)
→ documentation         → Write business-value README
→ freelance-proposal    → Create $8.5k pitch template
→ content-creation      → Demo video & launch assets
```

**Deliverable**: Live demo online, polished docs, ready to pitch

---

## 🔧 How to Use These Skills

### In Your Development Workflow

1. **Ask about RAG Architect decisions**:
   - "Should we use BM25 + semantic hybrid search?"
   - "How should we structure the vector DB?"
   - "What embedding model for institutional documents?"

2. **Request RAG Engineer implementation help**:
   - "Build contradiction detection into the RAG pipeline"
   - "Optimize retrieval quality for knowledge gap detection"
   - "Implement source attribution"

3. **Get RAG Implementation deployment help**:
   - "Deploy this to Vercel"
   - "Connect Groq API for production"
   - "Integrate with Streamlit"

### Example Conversation Patterns

```
You: "rag-architect: Design a contradiction detection system for NEXUS"
→ Architect will design the system for detecting document conflicts

You: "rag-engineer: Implement contradiction detection in LangChain"
→ Engineer will build the actual feature

You: "rag-implementation: Deploy the Streamlit app to HF Spaces"
→ Implementation will handle deployment
```

---

## 📋 Configuration

**Skills Location**: Globally installed via `npm skills add`
**Project Integration**: Referenced in `skills.json`
**Documentation**: This registry file

**Total Skills Available**:
- 3 specialized RAG skills (GitHub-installed)
- 7 complementary skills (Internal/Cowork)
- = **10 skills total** for NEXUS

---

## ✅ Quick Reference Checklist

- [x] rag-architect installed
- [x] rag-engineer installed
- [x] rag-implementation installed
- [x] system-design available
- [x] testing-strategy available
- [x] ux-copy available
- [x] documentation available
- [x] freelance-proposal available
- [x] architecture available (optional)
- [x] content-creation available (optional)

---

## 🎯 Next Steps

**Today (Week 1)**:
1. Use **system-design** to validate overall NEXUS architecture
2. Use **rag-architect** to design your retrieval pipeline
3. Start with **rag-engineer** to build document ingestion

**This Week**:
- Design phase complete with architecture documented
- Begin feature implementation with rag-engineer

---

## Notes

- All three GitHub skills complement your existing 7-skill set perfectly
- The **rag-architect → rag-engineer → rag-implementation** flow matches your 4-week timeline
- Use these skills alongside your internal complementary skills for best results
- Review skills before use — they run with full agent permissions

For full skill descriptions and usage, see `SKILLS_CURATED_FOR_NEXUS.md`.

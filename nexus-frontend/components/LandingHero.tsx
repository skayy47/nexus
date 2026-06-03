'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, useScroll, useTransform, useSpring, type Variants } from 'framer-motion'
import {
  Zap, Search, FileText, BarChart2, Github,
  FileStack, GitMerge, Sparkles, ShieldCheck, AlertTriangle, ArrowRight,
} from 'lucide-react'
import { loadDemo, warmupBackend } from '@/lib/api'
import { SmoothScroll } from './SmoothScroll'
import { NeuralCanvas } from './NeuralCanvas'

type DemoStatus = 'idle' | 'waking' | 'loading' | 'error'

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 32 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } },
}
const stagger: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.1 } } }

const PIPELINE = [
  { icon: FileStack, title: '1 · Ingest & chunk', desc: 'PDF, DOCX, TXT parsed via Unstructured, split into 800-token semantic chunks with overlap and section headers.', tag: 'Unstructured · semantic chunking' },
  { icon: GitMerge, title: '2 · Hybrid retrieve', desc: 'Dense pgvector search and sparse BM25 run in parallel, then fuse with Reciprocal Rank Fusion (k=60) — beating vector-only on keyword-heavy queries.', tag: 'BM25 + pgvector · RRF' },
  { icon: Sparkles, title: '3 · Generate', desc: 'Groq Llama 3.3 70B streams the answer token-by-token over an LCEL chain — context wrapped in document tags to neutralise prompt injection.', tag: 'Groq · LCEL · SSE streaming' },
  { icon: ShieldCheck, title: '4 · Verify', desc: 'A deterministic confidence score plus a second LLM pass that compares sources — surfacing contradictions and knowledge gaps before you trust the answer.', tag: 'Confidence · Contradiction Radar' },
]

const FEATURES = [
  { icon: Zap, title: 'Contradiction Radar', desc: 'A second structured LLM pass compares retrieved chunks across documents and flags conflicting statements with a severity rating.', color: '#fb7185', bg: 'rgba(251,113,133,0.1)' },
  { icon: Search, title: 'Knowledge Gaps', desc: 'Flags when the corpus has no real answer instead of hallucinating one — telling you what your documents are missing.', color: '#fbbf24', bg: 'rgba(251,191,36,0.1)' },
  { icon: FileText, title: 'Source Attribution', desc: 'Every answer cites its exact document, page, and excerpt — expandable inline, never a black box.', color: '#818cf8', bg: 'rgba(99,102,241,0.1)' },
  { icon: BarChart2, title: 'Confidence Scores', desc: 'A deterministic, auditable score from retrieval relevance and source agreement — high, medium, or low. No guessing.', color: '#34d399', bg: 'rgba(52,211,153,0.1)' },
]

const STACK = ['LangChain', 'Groq · Llama 3.3 70B', 'Supabase pgvector', 'BM25 + RRF', 'FastAPI', 'Next.js 14']
const GH = 'https://github.com/skayy47/nexus'

export function LandingHero() {
  const router = useRouter()
  const [demoStatus, setDemoStatus] = useState<DemoStatus>('idle')
  const loading = demoStatus === 'waking' || demoStatus === 'loading'

  // cursor-follow ambient glow
  const glowRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let gx = innerWidth / 2, gy = innerHeight / 2, cx = gx, cy = gy, id = 0
    const onMove = (e: MouseEvent) => { gx = e.clientX; gy = e.clientY }
    const loop = () => {
      cx += (gx - cx) * 0.12; cy += (gy - cy) * 0.12
      if (glowRef.current) glowRef.current.style.transform = `translate(${cx}px, ${cy}px) translate(-50%, -50%)`
      id = requestAnimationFrame(loop)
    }
    window.addEventListener('mousemove', onMove)
    id = requestAnimationFrame(loop)
    return () => { window.removeEventListener('mousemove', onMove); cancelAnimationFrame(id) }
  }, [])

  async function handleTryDemo() {
    setDemoStatus('loading')
    try {
      await warmupBackend(() => setDemoStatus('waking'))
      setDemoStatus('loading')
      await loadDemo()
      router.push('/chat?mode=demo')
    } catch {
      setDemoStatus('error')
    }
  }

  const demoLabel =
    demoStatus === 'waking' ? 'Waking the server…'
    : demoStatus === 'loading' ? 'Indexing 5 documents…'
    : 'Try the live demo'

  const spinner = loading && (
    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
  )

  return (
    <SmoothScroll>
      <div className="bg-[#06070d] text-slate-100 relative">
        {/* cursor glow */}
        <div
          ref={glowRef}
          aria-hidden
          className="pointer-events-none fixed left-0 top-0 z-[1] hidden md:block"
          style={{
            width: 480, height: 480, borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(99,102,241,0.10), transparent 60%)',
            transform: 'translate(-50%,-50%)',
          }}
        />

        {/* ── Header ───────────────────────────────────────────── */}
        <header className="fixed top-0 inset-x-0 z-50 flex items-center justify-between px-6 py-4 bg-[#06070d]/55 backdrop-blur-md border-b border-white/5">
          <span className="text-xl font-extrabold tracking-tight">NEX<span className="text-indigo-400">US</span></span>
          <nav className="flex items-center gap-7">
            <a href="#pipeline" className="hidden sm:block text-sm text-slate-400 hover:text-slate-100 transition-colors">How it works</a>
            <a href="#features" className="hidden sm:block text-sm text-slate-400 hover:text-slate-100 transition-colors">Features</a>
            <a href="#proof" className="hidden sm:block text-sm text-slate-400 hover:text-slate-100 transition-colors">Live demo</a>
            <a href={GH} target="_blank" rel="noopener noreferrer"
               className="inline-flex items-center gap-2 text-sm font-semibold text-slate-300 hover:text-white border border-white/12 hover:border-white/30 rounded-xl px-4 py-2 transition-all hover:-translate-y-0.5">
              <Github size={16} /> GitHub
            </a>
          </nav>
        </header>

        <HeroSection
          loading={loading}
          demoStatus={demoStatus}
          demoLabel={demoLabel}
          spinner={spinner}
          onTryDemo={handleTryDemo}
        />

        {/* ── Tech strip ───────────────────────────────────────── */}
        <div className="relative z-[2] border-y border-white/5 bg-white/[0.012] py-7">
          <motion.div
            initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="max-w-5xl mx-auto px-6 flex flex-wrap items-center justify-center gap-x-10 gap-y-3"
          >
            {STACK.map((s, i) => (
              <span key={s} className="flex items-center gap-10">
                <span className="text-[15px] font-medium text-slate-500 hover:text-slate-200 transition-colors cursor-default">{s}</span>
                {i < STACK.length - 1 && <span className="text-white/10">·</span>}
              </span>
            ))}
          </motion.div>
        </div>

        {/* ── Pipeline ─────────────────────────────────────────── */}
        <section id="pipeline" className="relative z-[2] py-28">
          <div className="max-w-5xl mx-auto px-6">
            <SectionHead eyebrow="The pipeline" title={<>From documents to <span className="nx-grad">defensible answers</span></>}
              lead="Every query runs through four stages — and every stage is auditable." />
            <div className="relative max-w-3xl mx-auto flex flex-col gap-5">
              <div className="absolute left-[31px] top-8 bottom-8 w-0.5 bg-gradient-to-b from-indigo-500 via-violet-400 to-transparent opacity-35" />
              {PIPELINE.map((s, i) => (
                <motion.div key={s.title} variants={fadeUp} initial="hidden" whileInView="show"
                  viewport={{ once: true, margin: '-60px' }} className="flex gap-5 items-start relative">
                  <div className="shrink-0 w-16 h-16 rounded-[18px] grid place-items-center bg-[rgba(18,20,34,0.6)] border border-[rgba(99,102,241,0.45)] backdrop-blur-md relative z-[1]"
                    style={{ boxShadow: '0 0 22px rgba(99,102,241,0.18)' }}>
                    <s.icon size={24} className="text-indigo-300" />
                  </div>
                  <div className="flex-1 rounded-[18px] p-5 bg-[rgba(18,20,34,0.6)] border border-[rgba(99,102,241,0.16)] backdrop-blur-md hover:border-[rgba(99,102,241,0.45)] hover:translate-x-1 transition-all">
                    <h3 className="text-[17px] font-semibold mb-1">{s.title}</h3>
                    <p className="text-slate-400 text-[14.5px] leading-relaxed">{s.desc}</p>
                    <span className="inline-block mt-3 text-[11.5px] text-indigo-300 bg-indigo-500/10 border border-[rgba(99,102,241,0.16)] px-2.5 py-1 rounded-lg">{s.tag}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Features ─────────────────────────────────────────── */}
        <section id="features" className="relative z-[2] py-28">
          <div className="max-w-5xl mx-auto px-6">
            <SectionHead eyebrow="What NEXUS detects" title="Beyond chat-with-docs"
              lead="Four capabilities that make answers trustworthy — not just fluent." />
            <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, margin: '-40px' }}
              className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-4xl mx-auto">
              {FEATURES.map((f) => <FeatureCard key={f.title} {...f} />)}
            </motion.div>
          </div>
        </section>

        {/* ── Transparency showcase ────────────────────────────── */}
        <section id="proof" className="relative z-[2] py-28">
          <div className="max-w-5xl mx-auto px-6">
            <SectionHead eyebrow="See it think" title={<>It tells you when your own docs <span className="nx-grad">disagree</span></>}
              lead="A real exchange from the demo corpus — two HR policies, one year apart." />
            <TransparencyPanel />
          </div>
        </section>

        {/* ── Final CTA ────────────────────────────────────────── */}
        <section className="relative text-center py-32 px-6">
          <div aria-hidden className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-0"
            style={{ width: 600, height: 380, background: 'radial-gradient(ellipse, rgba(124,92,255,0.18), transparent 65%)', filter: 'blur(50px)' }} />
          <motion.h2 variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className="relative z-[1] text-[clamp(30px,5vw,54px)] font-extrabold tracking-tight leading-[1.08] mb-5">
            Give your documents <span className="nx-grad">a memory.</span>
          </motion.h2>
          <motion.p variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className="relative z-[1] text-slate-400 text-[17px] mb-9">
            One click loads a live corpus with built-in contradictions. No signup.
          </motion.p>
          <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className="relative z-[1] flex flex-col items-center gap-3">
            <div className="flex flex-col sm:flex-row gap-3.5 justify-center">
              <button onClick={handleTryDemo} disabled={loading}
                className="inline-flex items-center justify-center gap-2 px-7 py-3.5 text-[15px] font-semibold text-white rounded-xl bg-gradient-to-br from-indigo-500 to-[#7c5cff] shadow-xl shadow-indigo-500/30 hover:-translate-y-0.5 hover:shadow-indigo-500/50 disabled:opacity-60 disabled:cursor-wait transition-all">
                {spinner}{demoLabel}{!loading && <ArrowRight size={16} />}
              </button>
              <a href={GH} target="_blank" rel="noopener noreferrer"
                className="px-7 py-3.5 text-[15px] font-semibold text-slate-300 hover:text-white border border-white/12 hover:border-white/30 rounded-xl hover:-translate-y-0.5 transition-all">
                View source ↗
              </a>
            </div>
            {demoStatus === 'error' && (
              <button onClick={handleTryDemo} className="text-xs font-medium text-indigo-400 underline hover:text-indigo-300">
                Server’s waking up — retry →
              </button>
            )}
          </motion.div>
        </section>

        <footer className="border-t border-white/[0.06] py-8 px-6 text-center text-slate-500 text-[13px]">
          Built by Oussama Iskia (SKAY) · RAG · hybrid retrieval · contradiction detection · MIT licensed
        </footer>
      </div>
    </SmoothScroll>
  )
}

/* ── Hero (parallax) ──────────────────────────────────────────── */
function HeroSection({ loading, demoStatus, demoLabel, spinner, onTryDemo }: {
  loading: boolean; demoStatus: DemoStatus; demoLabel: string; spinner: React.ReactNode; onTryDemo: () => void
}) {
  const { scrollY } = useScroll()
  const opacity = useSpring(useTransform(scrollY, [0, 420], [1, 0]), { stiffness: 80, damping: 20 })
  const y = useSpring(useTransform(scrollY, [0, 700], [0, -40]), { stiffness: 80, damping: 20 })

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-4 pt-28 pb-20 overflow-hidden">
      <div className="absolute inset-0 z-0"><NeuralCanvas /></div>
      <div aria-hidden className="absolute top-[38%] left-1/2 -translate-x-1/2 -translate-y-1/2 z-0 pointer-events-none"
        style={{ width: 720, height: 520, background: 'radial-gradient(ellipse, rgba(99,102,241,0.16), transparent 65%)', filter: 'blur(40px)' }} />

      <motion.div style={{ opacity, y }} variants={stagger} initial="hidden" animate="show"
        className="relative z-[2] max-w-3xl flex flex-col items-center">
        <motion.div variants={fadeUp} className="inline-flex items-center gap-2 text-[11.5px] font-semibold uppercase tracking-[0.18em] text-indigo-300 bg-indigo-500/10 border border-[rgba(99,102,241,0.16)] px-4 py-1.5 rounded-full mb-7">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" style={{ boxShadow: '0 0 10px #34d399' }} />
          Institutional Memory Engine · Live
        </motion.div>
        <motion.h1 variants={fadeUp} className="text-[clamp(38px,6.4vw,76px)] font-extrabold leading-[1.04] tracking-[-0.035em] mb-6">
          Companies lose <span className="nx-grad">42%</span> of their knowledge<br className="hidden sm:block" /> when senior employees leave.
        </motion.h1>
        <motion.p variants={fadeUp} className="text-[clamp(16px,2vw,20px)] text-slate-400 max-w-xl mx-auto mb-9 leading-relaxed">
          NEXUS turns your documents into an institution that remembers — answering with cited sources, scoring its own confidence, and catching the moment two documents disagree.
        </motion.p>
        <motion.div variants={fadeUp} className="flex flex-col items-center gap-3">
          <div className="flex flex-col sm:flex-row gap-3.5">
            <button onClick={onTryDemo} disabled={loading}
              className="inline-flex items-center justify-center gap-2 px-7 py-3.5 text-[15px] font-semibold text-white rounded-xl bg-gradient-to-br from-indigo-500 to-[#7c5cff] shadow-xl shadow-indigo-500/30 hover:-translate-y-0.5 hover:shadow-indigo-500/50 disabled:opacity-60 disabled:cursor-wait transition-all">
              {spinner}{demoLabel}{!loading && <ArrowRight size={16} />}
            </button>
            <a href={GH} target="_blank" rel="noopener noreferrer"
              className="px-7 py-3.5 text-[15px] font-semibold text-slate-300 hover:text-white border border-white/12 hover:border-white/30 rounded-xl hover:-translate-y-0.5 transition-all">
              View source ↗
            </a>
          </div>
          <a href="/chat?mode=upload"
            className="text-[13px] text-slate-500 hover:text-indigo-300 transition-colors">
            or upload your own documents →
          </a>
          {demoStatus === 'waking' && (
            <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
              className="text-xs text-slate-500 max-w-xs">
              First visit in a while — the free server is waking up (~30–60s). This only happens once.
            </motion.p>
          )}
          {demoStatus === 'error' && (
            <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} onClick={onTryDemo}
              className="text-xs font-medium text-indigo-400 underline hover:text-indigo-300">
              The demo server is taking a moment — retry →
            </motion.button>
          )}
        </motion.div>
      </motion.div>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[2] flex flex-col items-center gap-2 text-slate-600">
        <span className="text-[10px] tracking-[0.25em] uppercase">Scroll</span>
        <div className="w-px h-8 bg-gradient-to-b from-slate-600 to-transparent animate-pulse" />
      </div>
    </section>
  )
}

/* ── Section heading ──────────────────────────────────────────── */
function SectionHead({ eyebrow, title, lead }: { eyebrow: string; title: React.ReactNode; lead: string }) {
  return (
    <>
      <motion.p variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
        className="text-center text-[11.5px] font-semibold tracking-[0.22em] uppercase text-slate-500 mb-3.5">{eyebrow}</motion.p>
      <motion.h2 variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
        className="text-center text-[clamp(28px,4vw,44px)] font-bold tracking-[-0.03em] leading-[1.1] mb-4">{title}</motion.h2>
      <motion.p variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
        className="text-center text-slate-400 max-w-xl mx-auto mb-14 text-[16.5px]">{lead}</motion.p>
    </>
  )
}

/* ── Feature card (cursor spotlight) ──────────────────────────── */
function FeatureCard({ icon: Icon, title, desc, color, bg }: typeof FEATURES[number]) {
  const ref = useRef<HTMLDivElement>(null)
  const onMove = (e: React.MouseEvent) => {
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    el.style.setProperty('--mx', `${e.clientX - r.left}px`)
    el.style.setProperty('--my', `${e.clientY - r.top}px`)
  }
  return (
    <motion.div ref={ref} variants={fadeUp} onMouseMove={onMove}
      className="nx-feat group relative rounded-[20px] p-7 bg-[rgba(18,20,34,0.6)] border border-[rgba(99,102,241,0.16)] backdrop-blur-md overflow-hidden hover:-translate-y-1.5 hover:border-[rgba(99,102,241,0.45)] transition-all duration-300">
      <div className="w-[46px] h-[46px] rounded-[13px] grid place-items-center mb-4 border border-[rgba(99,102,241,0.16)]" style={{ background: bg }}>
        <Icon size={22} style={{ color }} />
      </div>
      <h3 className="text-[17.5px] font-semibold mb-1.5">{title}</h3>
      <p className="text-slate-400 text-[14.5px] leading-relaxed">{desc}</p>
    </motion.div>
  )
}

/* ── Transparency panel ───────────────────────────────────────── */
function TransparencyPanel() {
  return (
    <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true, margin: '-40px' }}
      className="max-w-2xl mx-auto rounded-[22px] overflow-hidden border border-[rgba(99,102,241,0.45)]"
      style={{ background: 'linear-gradient(160deg, rgba(20,22,38,0.85), rgba(12,13,24,0.85))', boxShadow: '0 30px 80px rgba(0,0,0,0.5), 0 0 40px rgba(99,102,241,0.08)' }}>
      <div className="flex items-center gap-2 px-4.5 py-3.5 border-b border-white/[0.06] bg-white/[0.02]" style={{ padding: '14px 18px' }}>
        <span className="w-[11px] h-[11px] rounded-full bg-[#fb7185]" />
        <span className="w-[11px] h-[11px] rounded-full bg-[#fbbf24]" />
        <span className="w-[11px] h-[11px] rounded-full bg-[#34d399]" />
        <span className="ml-2 text-slate-500 text-xs font-mono">nexus · chat</span>
      </div>
      <div className="p-6">
        <div className="flex justify-end mb-4.5" style={{ marginBottom: 18 }}>
          <span className="text-white text-[14.5px] px-4 py-2.5 rounded-[14px_14px_4px_14px] max-w-[80%] bg-gradient-to-br from-indigo-500 to-[#7c5cff]">
            What is the remote work policy? How many days per week?
          </span>
        </div>
        <div className="bg-white/[0.03] border border-[rgba(99,102,241,0.16)] rounded-[4px_14px_14px_14px] p-[18px] text-[14.5px] text-slate-100 leading-relaxed">
          According to the 2024 HR Policy, employees may work remotely up to <b>two (2) days/week</b>{' '}
          <span className="text-indigo-300 text-[12.5px]">[TechCorp_HR_Policy_2024 · p.1]</span>. The 2023 version allowed up to{' '}
          <b>three (3) days/week</b> <span className="text-indigo-300 text-[12.5px]">[TechCorp_HR_Policy_2023 · p.1]</span>.

          <div className="mt-[18px]">
            <div className="flex justify-between text-xs text-slate-400 mb-1.5"><span>Confidence</span><span className="text-amber-400">Medium · 0.71</span></div>
            <div className="h-[7px] rounded-full bg-white/[0.07] overflow-hidden">
              <motion.div initial={{ width: 0 }} whileInView={{ width: '71%' }} viewport={{ once: true }}
                transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
                className="h-full rounded-full bg-gradient-to-r from-amber-400 to-emerald-400" />
            </div>
          </div>

          <div className="mt-4 flex gap-3 bg-[rgba(251,113,133,0.07)] border border-[rgba(251,113,133,0.25)] rounded-xl p-[13px_15px]" style={{ padding: '13px 15px' }}>
            <AlertTriangle size={18} className="text-[#fb7185] shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-[13.5px] text-[#fb7185] font-semibold mb-1">Contradiction detected · medium severity</h4>
              <p className="text-[13px] text-slate-400">These two policies disagree on the remote-work limit. The 2024 version appears more recent and may supersede the 2023 policy.</p>
              <div className="flex flex-col sm:flex-row gap-2.5 mt-2.5 text-xs">
                <div className="flex-1 bg-white/[0.03] border border-white/[0.07] rounded-lg p-2.5">
                  <div className="text-slate-500 text-[10.5px] mb-1">TechCorp_HR_Policy_2023</div>up to 3 days / week</div>
                <div className="flex-1 bg-white/[0.03] border border-white/[0.07] rounded-lg p-2.5">
                  <div className="text-slate-500 text-[10.5px] mb-1">TechCorp_HR_Policy_2024</div>up to 2 days / week</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

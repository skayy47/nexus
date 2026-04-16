'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  motion,
  useScroll,
  useTransform,
  useSpring,
} from 'framer-motion'
import { Zap, Search, FileText, BarChart2, Github } from 'lucide-react'
import { loadDemo } from '@/lib/api'
import { SmoothScroll } from './SmoothScroll'
import { ParticleField } from './ParticleField'

const FEATURES = [
  {
    icon: Zap,
    title: 'Contradiction Radar',
    desc: 'Detects when your documents contradict each other in real time.',
    color: 'text-red-400',
    bg: 'bg-red-500/10 border-red-500/20',
  },
  {
    icon: Search,
    title: 'Knowledge Gaps',
    desc: 'Surfaces what your corpus is missing before it costs you.',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/20',
  },
  {
    icon: FileText,
    title: 'Source Attribution',
    desc: 'Every answer cites its exact document, page, and excerpt.',
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/10 border-indigo-500/20',
  },
  {
    icon: BarChart2,
    title: 'Confidence Scores',
    desc: 'Know exactly how certain each answer is — no black boxes.',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/20',
  },
]

const STACK = ['LangChain', 'Groq', 'pgvector', 'Next.js', 'Supabase']

const springConfig = { stiffness: 80, damping: 20, mass: 0.8 }

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
}

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } },
}

export function LandingHero() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [demoError, setDemoError] = useState<string | null>(null)

  // Parallax layers — each element scrolls at a different Y rate
  const { scrollY } = useScroll()

  const rawBadgeY   = useTransform(scrollY, [0, 700], [0, -60])
  const rawTitleY   = useTransform(scrollY, [0, 700], [0, -40])
  const rawSubY     = useTransform(scrollY, [0, 700], [0, -24])
  const rawCtaY     = useTransform(scrollY, [0, 700], [0, -12])
  const rawHeroOpacity = useTransform(scrollY, [0, 420], [1, 0])
  const rawBgY      = useTransform(scrollY, [0, 700], [0, 80])

  const badgeY   = useSpring(rawBadgeY,   springConfig)
  const titleY   = useSpring(rawTitleY,   springConfig)
  const subY     = useSpring(rawSubY,     springConfig)
  const ctaY     = useSpring(rawCtaY,     springConfig)
  const heroOpacity = useSpring(rawHeroOpacity, springConfig)
  const bgY      = useSpring(rawBgY,      springConfig)

  async function handleTryDemo() {
    setLoading(true)
    setDemoError(null)
    try {
      await loadDemo()
      router.push('/chat?mode=demo')
    } catch (err) {
      setLoading(false)
      setDemoError(err instanceof Error ? err.message : 'Could not connect to backend.')
    }
  }

  return (
    <SmoothScroll>
      <div className="bg-slate-950 text-slate-100">

        {/* ── Fixed header ──────────────────────────────────────────── */}
        <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 border-b border-slate-800/40 bg-slate-950/80 backdrop-blur-md">
          <span className="text-xl font-bold tracking-tight">
            NEX<span className="text-indigo-400">US</span>
          </span>
          <a
            href="https://github.com/skay-dev/nexus"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
          >
            <Github size={16} />
            GitHub
          </a>
        </header>

        {/* ── Hero section ──────────────────────────────────────────── */}
        {/* overflow-x: clip (not hidden) — preserves stacking context so parallax transforms work */}
        <section
          className="relative min-h-screen flex flex-col items-center justify-center text-center px-4 pt-20"
          style={{ overflowX: 'clip' }}
        >
          {/* Particle field — canvas fills the hero, z-index behind text */}
          <div className="absolute inset-0 -z-10">
            <ParticleField />
          </div>

          {/* Ambient glow — moves slowest (furthest layer) */}
          <motion.div
            style={{ y: bgY }}
            className="pointer-events-none absolute inset-0 -z-10"
            aria-hidden
          >
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[500px] rounded-full bg-indigo-600/10 blur-[120px]" />
          </motion.div>

          <motion.div
            style={{ opacity: heroOpacity }}
            variants={stagger}
            initial="hidden"
            animate="show"
            className="flex flex-col items-center gap-6 max-w-4xl"
          >
            {/* Badge — fastest parallax layer */}
            <motion.p
              variants={fadeUp}
              style={{ y: badgeY }}
              className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-4 py-1.5 rounded-full"
            >
              Institutional Memory Engine
            </motion.p>

            {/* Title — second layer */}
            <motion.h1
              variants={fadeUp}
              style={{ y: titleY }}
              className="text-5xl sm:text-6xl md:text-7xl font-bold leading-[1.04] tracking-tight text-slate-100"
            >
              Companies lose{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">
                42%
              </span>{' '}
              of their knowledge<br className="hidden sm:block" /> when senior
              employees leave.
            </motion.h1>

            {/* Subtitle — third layer */}
            <motion.p
              variants={fadeUp}
              style={{ y: subY }}
              className="text-xl text-slate-400 max-w-xl leading-relaxed"
            >
              NEXUS doesn&apos;t let that happen.
            </motion.p>

            {/* CTAs — closest layer (least movement) */}
            <motion.div
              variants={fadeUp}
              style={{ y: ctaY }}
              className="flex flex-col items-center gap-3"
            >
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleTryDemo}
                  disabled={loading}
                  className="px-8 py-3.5 bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 text-white font-semibold rounded-xl transition-all shadow-xl shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5"
                >
                  {loading ? 'Loading demo...' : 'Try Demo'}
                </button>
                <button
                  onClick={() => router.push('/chat?mode=upload')}
                  className="px-8 py-3.5 border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-slate-100 font-semibold rounded-xl transition-all hover:-translate-y-0.5"
                >
                  Upload Docs
                </button>
              </div>

              {demoError && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex flex-col items-center gap-1"
                >
                  <p className="text-xs text-red-400">
                    Backend unreachable — make sure the server is running.
                  </p>
                  <button
                    onClick={() => router.push('/chat?mode=demo')}
                    className="text-xs text-indigo-400 underline hover:text-indigo-300"
                  >
                    Go to chat anyway →
                  </button>
                </motion.div>
              )}
            </motion.div>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.6, duration: 0.8 }}
            className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
          >
            <span className="text-xs text-slate-600 uppercase tracking-widest">Scroll</span>
            <motion.div
              animate={{ y: [0, 6, 0] }}
              transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
              className="w-px h-8 bg-gradient-to-b from-slate-600 to-transparent"
            />
          </motion.div>
        </section>

        {/* ── Features section ──────────────────────────────────────── */}
        <section
          className="relative px-4 pb-24 pt-8"
          style={{ overflowX: 'clip' }}
        >
          <div className="max-w-5xl mx-auto">
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="text-center text-xs uppercase tracking-[0.2em] text-slate-500 mb-12"
            >
              What NEXUS detects
            </motion.p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {FEATURES.map((f, i) => (
                <motion.div
                  key={f.title}
                  initial={{ opacity: 0, y: 32 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-40px' }}
                  transition={{
                    delay: i * 0.08,
                    duration: 0.6,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  className={`p-5 rounded-2xl border bg-slate-900/60 backdrop-blur-sm ${f.bg} text-left hover:-translate-y-1 transition-transform duration-300`}
                >
                  <f.icon size={20} className={`${f.color} mb-3`} />
                  <h3 className="text-sm font-semibold text-slate-100 mb-1">{f.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{f.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Tech stack ────────────────────────────────────────────── */}
        <section className="pb-20 px-4">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 1 }}
            className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2"
          >
            {STACK.map((name, i) => (
              <span key={name} className="flex items-center gap-6">
                <span className="text-sm text-slate-600 hover:text-slate-400 transition-colors cursor-default">
                  {name}
                </span>
                {i < STACK.length - 1 && (
                  <span className="text-slate-800">·</span>
                )}
              </span>
            ))}
          </motion.div>
        </section>

      </div>
    </SmoothScroll>
  )
}

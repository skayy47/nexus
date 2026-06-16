'use client'

import { useState, useRef, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { useRouter, Link } from '@/i18n/navigation'
import { motion, useScroll, useTransform, useSpring, type Variants } from 'framer-motion'
import {
  Zap, Search, FileText, Github,
  FileStack, GitMerge, Sparkles, ShieldCheck, AlertTriangle, ArrowRight,
} from 'lucide-react'
import { loadDemo, warmupBackend } from '@/lib/api'
import { LanguageSwitcher } from './LanguageSwitcher'
import { SmoothScroll } from './SmoothScroll'
import { NeuralCanvas } from './NeuralCanvas'

type DemoStatus = 'idle' | 'waking' | 'loading' | 'error'

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 32 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } },
}
const stagger: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.1 } } }

// Icons only — copy lives in messages (pipeline.step{n}* / features.item{n}*).
const PIPELINE_ICONS = [FileStack, GitMerge, Sparkles, ShieldCheck]
const FEATURE_META = [
  { icon: Zap, color: '#D4A843', bg: 'rgba(212,168,67,0.1)' },
  { icon: Search, color: '#C9973B', bg: 'rgba(201,151,59,0.1)' },
  { icon: FileText, color: '#EDE4D0', bg: 'rgba(237,228,208,0.08)' },
  { icon: ShieldCheck, color: '#9B6B3A', bg: 'rgba(155,107,58,0.1)' },
]

const STACK = ['LangChain', 'Groq · Llama 3.3 70B', 'Supabase pgvector', 'BM25 + RRF', 'FastAPI', 'Next.js 14']
const GH = 'https://github.com/skayy47/nexus'

export function LandingHero() {
  const t = useTranslations()
  // next-intl keys must be literals; cast for the indexed pipeline/feature keys.
  const tx = t as unknown as (key: string) => string
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
    demoStatus === 'waking' ? t('hero.waking')
    : demoStatus === 'loading' ? t('hero.indexing')
    : t('hero.tryDemo')

  const spinner = loading && (
    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
  )

  return (
    <SmoothScroll>
      <div className="bg-[#0E0A05] text-[#EDE4D0] relative">
        {/* cursor glow */}
        <div
          ref={glowRef}
          aria-hidden
          className="pointer-events-none fixed left-0 top-0 z-[1] hidden md:block"
          style={{
            width: 480, height: 480, borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(201,151,59,0.10), transparent 60%)',
            transform: 'translate(-50%,-50%)',
          }}
        />

        {/* ── Header ───────────────────────────────────────────── */}
        <header className="fixed top-0 inset-x-0 z-50 flex items-center justify-between px-6 py-4 bg-[#0E0A05]/70 backdrop-blur-md border-b border-[#C9973B]/10">
          <span className="text-xl font-extrabold tracking-tight">NEX<span className="text-[#C9973B]">US</span></span>
          <nav className="flex items-center gap-7">
            <a href="#pipeline" className="hidden sm:block text-sm text-[#8A7A62] hover:text-[#EDE4D0] transition-colors">{t('nav.howItWorks')}</a>
            <a href="#features" className="hidden sm:block text-sm text-[#8A7A62] hover:text-[#EDE4D0] transition-colors">{t('nav.features')}</a>
            <a href="#proof" className="hidden sm:block text-sm text-[#8A7A62] hover:text-[#EDE4D0] transition-colors">{t('nav.liveDemo')}</a>
            <LanguageSwitcher />
            <a href={GH} target="_blank" rel="noopener noreferrer"
               className="inline-flex items-center gap-2 text-sm font-semibold text-[#C4B49A] hover:text-[#EDE4D0] border border-[#C9973B]/20 hover:border-[#C9973B]/50 rounded-xl px-4 py-2 transition-all hover:-translate-y-0.5">
              <Github size={16} /> {t('nav.github')}
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
        <div className="relative z-[2] border-y border-[#C9973B]/10 bg-[#C9973B]/[0.02] py-7">
          <motion.div
            initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="max-w-5xl mx-auto px-6 flex flex-wrap items-center justify-center gap-x-10 gap-y-3"
          >
            {STACK.map((s, i) => (
              <span key={s} className="flex items-center gap-10">
                <span className="text-[15px] font-medium text-[#5E5040] hover:text-[#EDE4D0] transition-colors cursor-default">{s}</span>
                {i < STACK.length - 1 && <span className="text-white/10">·</span>}
              </span>
            ))}
          </motion.div>
        </div>

        {/* ── Pipeline ─────────────────────────────────────────── */}
        <section id="pipeline" className="relative z-[2] py-28">
          <div className="max-w-5xl mx-auto px-6">
            <SectionHead eyebrow={t('pipeline.eyebrow')} title={<>{t('pipeline.titlePre')}<span className="nx-grad">{t('pipeline.titleAccent')}</span></>}
              lead={t('pipeline.lead')} />
            <div className="relative max-w-3xl mx-auto flex flex-col gap-5">
              <div className="absolute left-[31px] top-8 bottom-8 w-0.5 bg-gradient-to-b from-[#D4A843] via-[#C9973B] to-transparent opacity-35" />
              {PIPELINE_ICONS.map((Icon, i) => {
                const n = i + 1
                return (
                  <motion.div key={n} variants={fadeUp} initial="hidden" whileInView="show"
                    viewport={{ once: true, margin: '-60px' }} className="flex gap-5 items-start relative">
                    <div className="shrink-0 w-16 h-16 rounded-[18px] grid place-items-center bg-[rgba(20,14,8,0.7)] border border-[rgba(201,151,59,0.45)] backdrop-blur-md relative z-[1]"
                      style={{ boxShadow: '0 0 22px rgba(201,151,59,0.18)' }}>
                      <Icon size={24} className="text-[#D4A843]" />
                    </div>
                    <div className="flex-1 rounded-[18px] p-5 bg-[rgba(20,14,8,0.7)] border border-[rgba(201,151,59,0.16)] backdrop-blur-md hover:border-[rgba(201,151,59,0.45)] hover:translate-x-1 transition-all">
                      <h3 className="text-[17px] font-semibold mb-1">{tx(`pipeline.step${n}Title`)}</h3>
                      <p className="text-[#8A7A62] text-[14.5px] leading-relaxed">{tx(`pipeline.step${n}Desc`)}</p>
                      <span className="inline-block mt-3 text-[11.5px] text-[#D4A843] bg-[#C9973B]/10 border border-[rgba(201,151,59,0.25)] px-2.5 py-1 rounded-lg">{tx(`pipeline.step${n}Tag`)}</span>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        </section>

        {/* ── Features ─────────────────────────────────────────── */}
        <section id="features" className="relative z-[2] py-28">
          <div className="max-w-5xl mx-auto px-6">
            <SectionHead eyebrow={t('features.eyebrow')} title={t('features.title')}
              lead={t('features.lead')} />
            <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, margin: '-40px' }}
              className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-4xl mx-auto">
              {FEATURE_META.map((f, i) => (
                <FeatureCard key={i} icon={f.icon} color={f.color} bg={f.bg}
                  title={tx(`features.item${i + 1}Title`)} desc={tx(`features.item${i + 1}Desc`)} />
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── Transparency showcase ────────────────────────────── */}
        <section id="proof" className="relative z-[2] py-28">
          <div className="max-w-5xl mx-auto px-6">
            <SectionHead eyebrow={t('showcase.eyebrow')} title={<>{t('showcase.titlePre')}<span className="nx-grad">{t('showcase.titleAccent')}</span></>}
              lead={t('showcase.lead')} />
            <TransparencyPanel />
          </div>
        </section>

        {/* ── Final CTA ────────────────────────────────────────── */}
        <section className="relative text-center py-32 px-6">
          <div aria-hidden className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-0"
            style={{ width: 600, height: 380, background: 'radial-gradient(ellipse, rgba(201,151,59,0.15), transparent 65%)', filter: 'blur(50px)' }} />
          <motion.h2 variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className="relative z-[1] text-[clamp(30px,5vw,54px)] font-extrabold tracking-tight leading-[1.08] mb-5">
            {t('cta.titlePre')}<span className="nx-grad">{t('cta.titleAccent')}</span>
          </motion.h2>
          <motion.p variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className="relative z-[1] text-[#8A7A62] text-[17px] mb-9">
            {t('cta.sub')}
          </motion.p>
          <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className="relative z-[1] flex flex-col items-center gap-3">
            <div className="flex flex-col sm:flex-row gap-3.5 justify-center">
              <button onClick={handleTryDemo} disabled={loading}
                className="inline-flex items-center justify-center gap-2 px-7 py-3.5 text-[15px] font-semibold text-white rounded-xl bg-gradient-to-br from-[#D4A843] to-[#9B6B3A] shadow-xl shadow-[#C9973B]/30 hover:-translate-y-0.5 hover:shadow-[#C9973B]/50 disabled:opacity-60 disabled:cursor-wait transition-all">
                {spinner}{demoLabel}{!loading && <ArrowRight size={16} />}
              </button>
              <a href={GH} target="_blank" rel="noopener noreferrer"
                className="px-7 py-3.5 text-[15px] font-semibold text-[#C4B49A] hover:text-[#EDE4D0] border border-[#C9973B]/20 hover:border-[#C9973B]/50 rounded-xl hover:-translate-y-0.5 transition-all">
                {t('hero.viewSource')}
              </a>
            </div>
            {demoStatus === 'error' && (
              <button onClick={handleTryDemo} className="text-xs font-medium text-[#C9973B] underline hover:text-[#D4A843]">
                {t('cta.errorRetry')}
              </button>
            )}
          </motion.div>
        </section>

        <footer className="border-t border-[#C9973B]/10 py-8 px-6 text-center text-[#5E5040] text-[13px]">
          {t('footer.tagline')}
        </footer>
      </div>
    </SmoothScroll>
  )
}

/* ── Hero (parallax) ──────────────────────────────────────────── */
function HeroSection({ loading, demoStatus, demoLabel, spinner, onTryDemo }: {
  loading: boolean; demoStatus: DemoStatus; demoLabel: string; spinner: React.ReactNode; onTryDemo: () => void
}) {
  const t = useTranslations('hero')
  const { scrollY } = useScroll()
  const opacity = useSpring(useTransform(scrollY, [0, 420], [1, 0]), { stiffness: 80, damping: 20 })
  const y = useSpring(useTransform(scrollY, [0, 700], [0, -40]), { stiffness: 80, damping: 20 })

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-4 pt-28 pb-20 overflow-hidden">
      <div className="absolute inset-0 z-0"><NeuralCanvas /></div>
      <div aria-hidden className="absolute top-[38%] left-1/2 -translate-x-1/2 -translate-y-1/2 z-0 pointer-events-none"
        style={{ width: 720, height: 520, background: 'radial-gradient(ellipse, rgba(201,151,59,0.16), transparent 65%)', filter: 'blur(40px)' }} />

      <motion.div style={{ opacity, y }} variants={stagger} initial="hidden" animate="show"
        className="relative z-[2] max-w-3xl flex flex-col items-center">
        <motion.div variants={fadeUp} className="inline-flex items-center gap-2 text-[11.5px] font-semibold uppercase tracking-[0.18em] text-[#D4A843] bg-[#C9973B]/10 border border-[rgba(201,151,59,0.25)] px-4 py-1.5 rounded-full mb-7">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" style={{ boxShadow: '0 0 10px #34d399' }} />
          {t('badge')}
        </motion.div>
        <motion.h1 variants={fadeUp} className="text-[clamp(38px,6.4vw,76px)] font-extrabold leading-[1.04] tracking-[-0.035em] mb-6">
          {t('titlePre')}<span className="nx-grad">{t('titlePercent')}</span>{t('titlePost')}
        </motion.h1>
        <motion.p variants={fadeUp} className="text-[clamp(16px,2vw,20px)] text-[#8A7A62] max-w-xl mx-auto mb-9 leading-relaxed">
          {t('sub')}
        </motion.p>
        <motion.div variants={fadeUp} className="flex flex-col items-center gap-3">
          <div className="flex flex-col sm:flex-row gap-3.5">
            <button onClick={onTryDemo} disabled={loading}
              className="inline-flex items-center justify-center gap-2 px-7 py-3.5 text-[15px] font-semibold text-white rounded-xl bg-gradient-to-br from-[#D4A843] to-[#9B6B3A] shadow-xl shadow-[#C9973B]/30 hover:-translate-y-0.5 hover:shadow-[#C9973B]/50 disabled:opacity-60 disabled:cursor-wait transition-all">
              {spinner}{demoLabel}{!loading && <ArrowRight size={16} />}
            </button>
            <a href={GH} target="_blank" rel="noopener noreferrer"
              className="px-7 py-3.5 text-[15px] font-semibold text-[#C4B49A] hover:text-[#EDE4D0] border border-[#C9973B]/20 hover:border-[#C9973B]/50 rounded-xl hover:-translate-y-0.5 transition-all">
              {t('viewSource')}
            </a>
          </div>
          <Link href="/chat?mode=upload"
            className="text-[13px] text-[#5E5040] hover:text-[#D4A843] transition-colors">
            {t('uploadOwn')}
          </Link>
          {demoStatus === 'waking' && (
            <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
              className="text-xs text-[#5E5040] max-w-xs">
              {t('wakingNote')}
            </motion.p>
          )}
          {demoStatus === 'error' && (
            <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} onClick={onTryDemo}
              className="text-xs font-medium text-[#C9973B] underline hover:text-[#D4A843]">
              {t('errorRetry')}
            </motion.button>
          )}
        </motion.div>
      </motion.div>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[2] flex flex-col items-center gap-2 text-[#3E3020]">
        <span className="text-[10px] tracking-[0.25em] uppercase">{t('scroll')}</span>
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
        className="text-center text-[11.5px] font-semibold tracking-[0.22em] uppercase text-[#6A5A42] mb-3.5">{eyebrow}</motion.p>
      <motion.h2 variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
        className="text-center text-[clamp(28px,4vw,44px)] font-bold tracking-[-0.03em] leading-[1.1] mb-4">{title}</motion.h2>
      <motion.p variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
        className="text-center text-[#8A7A62] max-w-xl mx-auto mb-14 text-[16.5px]">{lead}</motion.p>
    </>
  )
}

/* ── Feature card (cursor spotlight) ──────────────────────────── */
function FeatureCard({ icon: Icon, title, desc, color, bg }: {
  icon: typeof Zap; title: string; desc: string; color: string; bg: string
}) {
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
      className="nx-feat group relative rounded-[20px] p-7 bg-[rgba(20,14,8,0.7)] border border-[rgba(201,151,59,0.16)] backdrop-blur-md overflow-hidden hover:-translate-y-1.5 hover:border-[rgba(201,151,59,0.45)] transition-all duration-300">
      <div className="w-[46px] h-[46px] rounded-[13px] grid place-items-center mb-4 border border-[rgba(201,151,59,0.16)]" style={{ background: bg }}>
        <Icon size={22} style={{ color }} />
      </div>
      <h3 className="text-[17.5px] font-semibold mb-1.5">{title}</h3>
      <p className="text-[#8A7A62] text-[14.5px] leading-relaxed">{desc}</p>
    </motion.div>
  )
}

/* ── Transparency panel ───────────────────────────────────────── */
function TransparencyPanel() {
  const t = useTranslations('showcase')
  return (
    <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true, margin: '-40px' }}
      className="max-w-2xl mx-auto rounded-[22px] overflow-hidden border border-[rgba(201,151,59,0.45)]"
      style={{ background: 'linear-gradient(160deg, rgba(26,18,8,0.92), rgba(14,10,4,0.92))', boxShadow: '0 30px 80px rgba(0,0,0,0.6), 0 0 40px rgba(201,151,59,0.12)' }}>
      <div className="flex items-center gap-2 px-4.5 py-3.5 border-b border-white/[0.06] bg-white/[0.02]" style={{ padding: '14px 18px' }}>
        <span className="w-[11px] h-[11px] rounded-full bg-[#fb7185]" />
        <span className="w-[11px] h-[11px] rounded-full bg-[#fbbf24]" />
        <span className="w-[11px] h-[11px] rounded-full bg-[#34d399]" />
        <span className="ml-2 text-slate-500 text-xs font-mono">{t('tab')}</span>
      </div>
      <div className="p-6">
        <div className="flex justify-end mb-4.5" style={{ marginBottom: 18 }}>
          <span className="text-[#0E0A05] text-[14.5px] px-4 py-2.5 rounded-[14px_14px_4px_14px] max-w-[80%] bg-gradient-to-br from-[#D4A843] to-[#9B6B3A]">
            {t('question')}
          </span>
        </div>
        <div className="bg-[#C9973B]/[0.04] border border-[rgba(201,151,59,0.2)] rounded-[4px_14px_14px_14px] p-[18px] text-[14.5px] text-[#EDE4D0] leading-relaxed">
          {t('answerPre')}<b>{t('answer2days')}</b>{' '}
          <span className="text-[#D4A843] text-[12.5px]">[TechCorp_HR_Policy_2024 · p.1]</span>{t('answerMid')}
          <b>{t('answer3days')}</b> <span className="text-[#D4A843] text-[12.5px]">[TechCorp_HR_Policy_2023 · p.1]</span>{t('answerPost')}

          <div className="mt-4 flex gap-3 bg-[rgba(251,113,133,0.07)] border border-[rgba(251,113,133,0.25)] rounded-xl p-[13px_15px]" style={{ padding: '13px 15px' }}>
            <AlertTriangle size={18} className="text-[#fb7185] shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-[13.5px] text-[#fb7185] font-semibold mb-1">{t('contradictionTitle')}</h4>
              <p className="text-[13px] text-[#8A7A62]">{t('contradictionDesc')}</p>
              <div className="flex flex-col sm:flex-row gap-2.5 mt-2.5 text-xs">
                <div className="flex-1 bg-[#C9973B]/[0.04] border border-[#C9973B]/10 rounded-lg p-2.5">
                  <div className="text-[#6A5A42] text-[10.5px] mb-1">TechCorp_HR_Policy_2023</div>{t('policy2023Limit')}</div>
                <div className="flex-1 bg-[#C9973B]/[0.04] border border-[#C9973B]/10 rounded-lg p-2.5">
                  <div className="text-[#6A5A42] text-[10.5px] mb-1">TechCorp_HR_Policy_2024</div>{t('policy2024Limit')}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

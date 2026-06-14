'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  ChevronDown,
  ChevronUp,
  Check,
  AlertCircle,
} from 'lucide-react'
import { GroundingResult } from '@/lib/api'

const VERDICT = {
  grounded: { color: '#10b981', bg: 'rgba(16,185,129,0.08)', Icon: ShieldCheck },
  partial: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', Icon: ShieldAlert },
  ungrounded: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', Icon: ShieldX },
} as const

/**
 * Grounding panel — the visible expression of answer faithfulness. Shows how
 * much of the answer is backed by the cited sources (coverage), a verdict, and
 * an optional per-claim breakdown with [n] citations into the source cards.
 * Replaces the old similarity-only "confidence" bar.
 */
export function GroundingPanel({ grounding }: { grounding: GroundingResult }) {
  const t = useTranslations('grounding')
  const [open, setOpen] = useState(false)
  const v = VERDICT[grounding.verdict] ?? VERDICT.partial
  const pct = Math.round(grounding.coverage * 100)
  const Icon = v.Icon
  const hasClaims = grounding.claim_count > 0

  return (
    <div
      className="mt-4 rounded-md px-3 py-2.5 space-y-2"
      style={{ background: v.bg, borderLeft: `3px solid ${v.color}`, borderRadius: '6px' }}
    >
      {/* Header row: verdict + coverage */}
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 text-xs font-bold" style={{ color: v.color }}>
          <Icon size={14} strokeWidth={2.5} />
          {t(grounding.verdict)}
        </span>
        <span className="text-xs font-semibold tabular-nums" style={{ color: v.color }}>
          {t('cited', { supported: grounding.supported_count, total: grounding.claim_count, pct })}
        </span>
      </div>

      {/* Coverage meter */}
      <div className="h-1.5 bg-slate-700/60 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ background: v.color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        />
      </div>

      {/* Per-claim verification toggle */}
      {hasClaims && (
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
        >
          {open ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
          {open ? t('hideCheck') : t('showCheck')}
        </button>
      )}

      <AnimatePresence>
        {open && (
          <motion.ul
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="overflow-hidden space-y-1.5"
          >
            {grounding.claims.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-xs leading-relaxed">
                {c.supported ? (
                  <Check size={13} className="mt-0.5 shrink-0 text-emerald-400" />
                ) : (
                  <AlertCircle size={13} className="mt-0.5 shrink-0 text-amber-400" />
                )}
                <span className={c.supported ? 'text-slate-300' : 'text-slate-400'}>
                  {c.text}
                  {c.supported && c.source_index !== null && (
                    <sup className="ml-0.5 text-indigo-400 font-semibold">[{c.source_index + 1}]</sup>
                  )}
                </span>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>

      {grounding.single_source && (
        <p className="text-[11px] text-slate-500 italic">{t('singleSource')}</p>
      )}
    </div>
  )
}

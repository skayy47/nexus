'use client'

import { motion } from 'framer-motion'

interface Props {
  score: number
  label: 'high' | 'moderate' | 'low'
  reasoning?: string
}

const CONFIG = {
  high:     { gradient: 'from-emerald-500 to-emerald-400', text: '#22c55e', label: 'High confidence' },
  moderate: { gradient: 'from-amber-500 to-yellow-400',    text: '#f59e0b', label: 'Moderate confidence' },
  low:      { gradient: 'from-red-500 to-red-400',         text: '#ef4444', label: 'Low confidence' },
}

export function ConfidenceBar({ score, label, reasoning }: Props) {
  const pct = Math.round(score * 100)
  const cfg = CONFIG[label] ?? CONFIG.moderate

  return (
    <div
      className="mt-4 rounded-md px-3 py-2.5 space-y-2"
      style={{
        background: 'rgba(34,197,94,0.08)',
        borderLeft: '3px solid #22c55e',
        borderRadius: '6px',
      }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 text-xs font-bold" style={{ color: '#22c55e' }}>
          ✅ Confidence note:
        </span>
        <span className="text-xs font-semibold tabular-nums" style={{ color: cfg.text }}>
          {cfg.label} — {pct}%
        </span>
      </div>

      {/* Gradient bar */}
      <div className="h-1.5 bg-slate-700/60 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${cfg.gradient}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        />
      </div>

      {/* Reasoning */}
      {reasoning && (
        <p className="text-xs text-slate-400 leading-relaxed">{reasoning}</p>
      )}
    </div>
  )
}

'use client'

import { motion } from 'framer-motion'
import { BookOpen, Sparkles, ChevronRight } from 'lucide-react'
import { useTranslations } from 'next-intl'

interface Props {
  filename: string
  summary: string
  bullets: string[]
  questions: string[]
  onAsk?: (q: string) => void
}

export function DocumentSummaryCard({ filename, summary, bullets, questions, onAsk }: Props) {
  const t = useTranslations('documentZone')

  if (!summary && bullets.length === 0) return null

  // Strip path separators, keep just the base name for display
  const displayName = filename.split(/[\\/]/).pop() ?? filename

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="mt-3 rounded-xl border border-[#C9973B]/20 bg-[#1A1208]/60 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-[#C9973B]/10 bg-[#C9973B]/5">
        <BookOpen size={12} className="text-[#C9973B] shrink-0" />
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-[10px] font-semibold text-[#C9973B] uppercase tracking-wider shrink-0">
            {t('summaryTitle')}
          </span>
          <span className="text-[#6A5A42] text-[10px]">—</span>
          <span className="text-[10px] text-[#8A7A62] truncate" title={displayName}>
            {displayName}
          </span>
        </div>
      </div>

      <div className="p-3 space-y-3">
        {/* One-liner */}
        {summary && (
          <p className="text-xs text-[#8A7A62] italic leading-relaxed">{summary}</p>
        )}

        {/* Bullet points */}
        {bullets.length > 0 && (
          <ul className="space-y-2">
            {bullets.map((b, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.1 + i * 0.07 }}
                className="flex items-start gap-2 text-xs text-[#C4B49A] leading-relaxed"
              >
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#C9973B]/70 shrink-0" />
                {b}
              </motion.li>
            ))}
          </ul>
        )}

        {/* Suggested questions */}
        {questions.length > 0 && onAsk && (
          <div className="space-y-1.5 pt-2 border-t border-[#C9973B]/10">
            <p className="text-[10px] text-[#6A5A42] uppercase tracking-wider font-semibold flex items-center gap-1">
              <Sparkles size={10} className="text-[#C9973B]" />
              {t('suggestedQuestions')}
            </p>
            {questions.map((q, i) => (
              <motion.button
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.35 + i * 0.06 }}
                onClick={() => onAsk(q)}
                className="w-full text-left text-xs text-[#8A7A62] hover:text-[#EDE4D0] border border-[#C9973B]/10 hover:border-[#C9973B]/40 hover:bg-[#C9973B]/5 rounded-lg px-2.5 py-1.5 transition-all flex items-center gap-1.5 cursor-pointer group"
              >
                <ChevronRight size={10} className="shrink-0 text-[#C9973B] group-hover:translate-x-0.5 transition-transform" />
                {q}
              </motion.button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

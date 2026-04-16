'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { SourceRef } from '@/lib/api'

interface Props {
  source: SourceRef
}

const PALETTES = [
  { chip: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40' },
  { chip: 'bg-violet-500/20 text-violet-300 border-violet-500/40' },
  { chip: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' },
  { chip: 'bg-amber-500/20 text-amber-300 border-amber-500/40' },
  { chip: 'bg-rose-500/20 text-rose-300 border-rose-500/40' },
  { chip: 'bg-sky-500/20 text-sky-300 border-sky-500/40' },
  { chip: 'bg-teal-500/20 text-teal-300 border-teal-500/40' },
]

function docPalette(name: string) {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffff
  return PALETTES[h % PALETTES.length]
}

export function SourceCard({ source }: Props) {
  const [open, setOpen] = useState(false)
  const pal = docPalette(source.document_name)

  return (
    <div className="rounded-lg overflow-hidden border border-slate-700/40 bg-slate-800/30">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-slate-700/20 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          {/* Colored doc chip */}
          <span className={`shrink-0 border rounded-full px-2 py-0.5 text-[10px] font-medium truncate max-w-[160px] ${pal.chip}`}>
            {source.document_name}
          </span>
          <span className="text-slate-500 text-xs shrink-0">p.{source.page_number}</span>
        </div>
        {open
          ? <ChevronUp size={12} className="text-slate-500 shrink-0" />
          : <ChevronDown size={12} className="text-slate-500 shrink-0" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div className="px-3 py-2 border-t border-slate-700/40">
              <p className="text-xs text-slate-500 italic leading-relaxed font-mono">
                &ldquo;{source.excerpt}&rdquo;
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

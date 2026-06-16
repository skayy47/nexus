'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { SourceRef } from '@/lib/api'

interface Props {
  source: SourceRef
}

const PALETTES = [
  { chip: 'bg-[#C9973B]/20 text-[#D4A843] border-[#C9973B]/40' },
  { chip: 'bg-[#9B6B3A]/20 text-[#C4A06A] border-[#9B6B3A]/40' },
  { chip: 'bg-[#D4A843]/20 text-[#EDD270] border-[#D4A843]/40' },
  { chip: 'bg-amber-500/20 text-amber-300 border-amber-500/40' },
  { chip: 'bg-[#C9973B]/15 text-[#C4B49A] border-[#C9973B]/30' },
  { chip: 'bg-[#9B6B3A]/15 text-[#C4A06A] border-[#9B6B3A]/30' },
  { chip: 'bg-[#D4A843]/15 text-[#D4A843] border-[#D4A843]/30' },
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
    <div className="rounded-lg overflow-hidden border border-[#C9973B]/20 bg-[#1A1208]/50">
      <button
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-label={`${open ? 'Collapse' : 'Expand'} source: ${source.document_name} page ${source.page_number}`}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-[#C9973B]/[0.06] transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          {/* Colored doc chip */}
          <span className={`shrink-0 border rounded-full px-2 py-0.5 text-[10px] font-medium truncate max-w-[160px] ${pal.chip}`}>
            {source.document_name}
          </span>
          <span className="text-[#6A5A42] text-xs shrink-0">p.{source.page_number}</span>
        </div>
        {open
          ? <ChevronUp size={12} className="text-[#6A5A42] shrink-0" aria-hidden />
          : <ChevronDown size={12} className="text-[#6A5A42] shrink-0" aria-hidden />}
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
            <div className="px-3 py-2 border-t border-[#C9973B]/15">
              <p className="text-xs text-[#6A5A42] italic leading-relaxed font-mono">
                &ldquo;{source.excerpt}&rdquo;
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

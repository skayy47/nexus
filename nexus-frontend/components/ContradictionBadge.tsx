'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { ContradictionResult } from '@/lib/api'

interface Props {
  contradiction?: ContradictionResult
}

/** Renders the contradiction status block.
 *  - No contradiction: green ✅ block
 *  - Contradiction detected: red ⚠️ expandable block
 */
export function ContradictionBadge({ contradiction }: Props) {
  const [expanded, setExpanded] = useState(false)

  if (!contradiction) {
    return (
      <div
        className="mt-4 flex items-center gap-2 px-3 py-2 rounded-md text-xs font-bold"
        style={{
          background: 'rgba(34,197,94,0.08)',
          borderLeft: '3px solid #22c55e',
          borderRadius: '6px',
          color: '#22c55e',
        }}
      >
        ✅ No contradictions detected
      </div>
    )
  }

  return (
    <div className="mt-4">
      {/* Pulsing toggle button */}
      <motion.button
        onClick={() => setExpanded(e => !e)}
        animate={{
          boxShadow: [
            '0 0 0 0 rgba(239,68,68,0.5)',
            '0 0 0 8px rgba(239,68,68,0)',
            '0 0 0 0 rgba(239,68,68,0)',
          ],
        }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeOut' }}
        className="w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-bold transition-colors hover:opacity-90"
        style={{
          background: 'rgba(239,68,68,0.1)',
          borderLeft: '3px solid #ef4444',
          borderRadius: '6px',
          color: '#ef4444',
        }}
      >
        <span>⚠️ Contradiction Detected</span>
        {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </motion.button>

      {/* Expandable detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div
              className="mt-2 p-4 space-y-3 text-sm"
              style={{
                background: 'rgba(239,68,68,0.06)',
                border: '1px solid rgba(239,68,68,0.25)',
                borderRadius: '8px',
              }}
            >
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-red-400/70 truncate">
                    {contradiction.source_a}
                  </p>
                  <p className="text-slate-300 italic leading-relaxed text-xs font-mono">
                    &ldquo;{contradiction.excerpt_a}&rdquo;
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-red-400/70 truncate">
                    {contradiction.source_b}
                  </p>
                  <p className="text-slate-300 italic leading-relaxed text-xs font-mono">
                    &ldquo;{contradiction.excerpt_b}&rdquo;
                  </p>
                </div>
              </div>
              <p className="text-slate-400 text-xs border-t border-red-500/20 pt-3 leading-relaxed">
                {contradiction.explanation}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

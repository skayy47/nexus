'use client'

import { useLocale } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'
import { motion, useReducedMotion } from 'framer-motion'

const LOCALES = [
  { code: 'fr', label: 'FR', name: 'Français' },
  { code: 'en', label: 'EN', name: 'English' },
] as const

function GlobeGlyph() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M2 12h20" />
      <path d="M12 2a15.3 15.3 0 0 1 0 20 15.3 15.3 0 0 1 0-20Z" />
    </svg>
  )
}

/**
 * Premium segmented FR/EN language toggle (nexus indigo theme).
 * Glassmorphic pill with a spring-animated active indicator (Framer Motion
 * shared layout). Honors prefers-reduced-motion and is keyboard-accessible.
 */
export function LanguageSwitcher() {
  const locale = useLocale()
  const router = useRouter()
  const pathname = usePathname()
  const reduceMotion = useReducedMotion()

  const switchTo = (next: string) => {
    if (next === locale) return
    router.replace(pathname, { locale: next })
  }

  return (
    <div
      role="group"
      aria-label={locale === 'fr' ? 'Langue' : 'Language'}
      className="group relative inline-flex items-center gap-1.5 h-8 pl-2.5 pr-1 rounded-full bg-[#C9973B]/[0.06] border border-[#C9973B]/20 backdrop-blur-md"
    >
      <span className="text-[#6A5A42] transition-colors duration-200 group-hover:text-[#C4B49A]">
        <GlobeGlyph />
      </span>
      <div className="relative flex items-center">
        {LOCALES.map(({ code, label, name }) => {
          const isActive = locale === code
          return (
            <button
              key={code}
              type="button"
              onClick={() => switchTo(code)}
              aria-pressed={isActive}
              aria-label={name}
              title={name}
              lang={code}
              className="relative z-10 px-2.5 py-1 rounded-full text-[0.72rem] font-semibold tracking-wide outline-none transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-[#C9973B]/60"
              style={{ color: isActive ? '#0E0A05' : '#8A7A62' }}
            >
              {isActive && (
                <motion.span
                  layoutId="nexus-lang-pill"
                  className="absolute inset-0 rounded-full"
                  style={{
                    background:
                      'linear-gradient(135deg, #D4A843 0%, #9B6B3A 100%)',
                    boxShadow:
                      '0 0 0 1px rgba(201,151,59,0.5), 0 6px 16px -6px rgba(201,151,59,0.5)',
                  }}
                  transition={
                    reduceMotion
                      ? { duration: 0 }
                      : { type: 'spring', stiffness: 400, damping: 32 }
                  }
                />
              )}
              <span className="relative z-10">{label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

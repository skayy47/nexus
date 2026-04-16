import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        nexus: {
          bg: '#020817',
          card: '#0f172a',
          accent: '#6366f1',
          danger: '#ef4444',
          success: '#10b981',
          info: '#3b82f6',
          warning: '#f59e0b',
        },
      },
    },
  },
  plugins: [],
}

export default config

import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        nexus: {
          bg: '#0E0A05',
          card: '#1A1208',
          accent: '#C9973B',
          bronze: '#9B6B3A',
          danger: '#ef4444',
          success: '#10b981',
          info: '#C9973B',
          warning: '#D4A843',
          ivory: '#EDE4D0',
          muted: '#7A6A52',
        },
      },
    },
  },
  plugins: [],
}

export default config

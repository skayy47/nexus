import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'NEXUS — Institutional Memory Engine',
  description:
    'Companies lose 42% of their knowledge when senior employees leave. NEXUS is a RAG system that detects contradictions in your documents and is radically transparent about its confidence.',
  keywords: [
    'RAG',
    'knowledge management',
    'AI',
    'LangChain',
    'contradiction detection',
    'document intelligence',
  ],
  authors: [{ name: 'Oussama Iskia', url: 'https://skay.dev' }],
  metadataBase: new URL('https://nexus.skay.dev'),
  openGraph: {
    title: 'NEXUS — Institutional Memory Engine',
    description:
      "Companies lose 42% of their knowledge when senior employees leave. NEXUS doesn't let that happen.",
    url: 'https://nexus.skay.dev',
    siteName: 'NEXUS',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'NEXUS — Institutional Memory Engine',
    description: 'RAG system that detects contradictions in your company documents.',
  },
  robots: { index: true, follow: true },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased">{children}</body>
    </html>
  )
}

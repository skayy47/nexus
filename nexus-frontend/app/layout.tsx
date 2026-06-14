import type { ReactNode } from 'react'

// Root layout — app/[locale]/layout.tsx owns <html> and <body> for locale-aware
// lang. This passthrough is required by Next.js 14 App Router.
export default function RootLayout({ children }: { children: ReactNode }): any {
  return children
}

import type { Metadata } from 'next'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages, getTranslations } from 'next-intl/server'
import '../globals.css'

export async function generateMetadata({
  params,
}: {
  params: { locale: string }
}): Promise<Metadata> {
  const { locale } = params
  const t = await getTranslations({ locale, namespace: 'meta' })
  return {
    title: t('title'),
    description: t('description'),
    metadataBase: new URL('https://nexussss-two.vercel.app'),
    openGraph: {
      title: t('title'),
      description: t('description'),
      url: 'https://nexussss-two.vercel.app',
      siteName: 'NEXUS',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: t('title'),
      description: t('description'),
    },
    robots: { index: true, follow: true },
  }
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: { locale: string }
}) {
  const { locale } = params
  const messages = await getMessages()

  return (
    <html lang={locale} className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased">
        <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
      </body>
    </html>
  )
}

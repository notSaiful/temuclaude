import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { CookieConsent } from '@/components/CookieConsent';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-jetbrains',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://timuclaude.com'),
  title: 'Timuclaude — Open-Source LLM Orchestration | Beat Frontier Models',
  description: 'One question. Many minds. One superior answer. Timuclaude orchestrates 5 AI models to beat frontier models at 28x lower cost. Try it free in the playground. Open source. MIT licensed.',
  keywords: ['LLM orchestration', 'multi-model AI', 'AI playground', 'model comparison', 'open source AI'],
  authors: [{ name: 'Mohammad Saiful Haque' }],
  icons: { icon: '/favicon.svg' },
  openGraph: {
    title: 'Timuclaude — Open-Source LLM Orchestration',
    description: 'One question. Many minds. One superior answer. 28x cheaper than frontier models.',
    type: 'website',
    url: 'https://timuclaude.com',
    siteName: 'Timuclaude',
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: 'Timuclaude playground interface' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Timuclaude — Open-Source LLM Orchestration',
    description: 'One question. Many minds. One superior answer. 28x cheaper than frontier models.',
    images: ['/og-image.png'],
    site: '@timuclaude',
  },
  robots: { index: true, follow: true },
};

const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Timuclaude',
  applicationCategory: 'DeveloperApplication',
  operatingSystem: 'Web',
  description: 'Multi-model AI orchestration platform that beats frontier models at 28x lower cost.',
  offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
  url: 'https://timuclaude.com',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </head>
      <body>
        <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-bg-dark focus:text-text-inverse focus:rounded-sm">
          Skip to content
        </a>
        {children}
        <CookieConsent />
      </body>
    </html>
  );
}
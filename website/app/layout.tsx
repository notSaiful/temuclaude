import type { Metadata } from 'next';
import { Source_Sans_3, Newsreader, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { CookieConsent } from '@/components/CookieConsent';

const sourceSans = Source_Sans_3({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
  weight: ['300', '400', '500', '600'],
});

const newsreader = Newsreader({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-serif',
  weight: ['300', '400', '500'],
  style: ['normal', 'italic'],
});

const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://temuclaude.com'),
  title: 'TemuClaude — Three-Model AI API',
  description: 'An OpenAI-compatible API that routes each request to Kimi K3, GLM 5.2, or Grok 4.5.',
  keywords: ['LLM API', 'model routing', 'coding agent API', 'AI orchestration'],
  authors: [{ name: 'Mohammad Saiful Haque' }],
  icons: { icon: '/favicon.svg' },
  openGraph: {
    title: 'TemuClaude — Three-Model AI API',
    description: 'Simple, capable routing for coding, agentic workflows, repair, and general reasoning.',
    type: 'website',
    url: 'https://temuclaude.com',
    siteName: 'TemuClaude',
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: 'TemuClaude — Three-Model AI API' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TemuClaude — Three-Model AI API',
    description: 'Kimi K3, GLM 5.2, and Grok 4.5 behind one OpenAI-compatible endpoint.',
    images: ['/og-image.png'],
    site: '@temuclaude',
  },
  robots: { index: true, follow: true },
};

const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'TemuClaude',
  applicationCategory: 'DeveloperApplication',
  operatingSystem: 'Web',
  description: 'OpenAI-compatible AI API with a small, deterministic three-model router.',
  offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
  url: 'https://temuclaude.com',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sourceSans.variable} ${newsreader.variable} ${jetbrains.variable}`}>
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

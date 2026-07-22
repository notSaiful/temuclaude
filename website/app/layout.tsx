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
  title: 'TemuClaude — Multi-Model AI Orchestration | 8 Models, Adaptive Multi-Layer Pipeline',
  description: 'TemuClaude assigns ten AI model roles by capability, synthesizes parallel specialist work, and independently verifies nontrivial responses. Try it free.',
  keywords: ['LLM orchestration', 'multi-model AI', 'Mixture of Agents', 'AI playground', 'model fusion', 'open source AI', 'frontier AI', 'cheap AI API'],
  authors: [{ name: 'Mohammad Saiful Haque' }],
  icons: { icon: '/favicon.svg' },
  openGraph: {
    title: 'TemuClaude — One Question. Eight Minds. One Superior Answer.',
    description: '8 models. Adaptive multi-layer pipeline — up to 10 layers for hard queries. A fraction of comparable frontier direct token cost. Open source. 25% to charity.',
    type: 'website',
    url: 'https://temuclaude.com',
    siteName: 'TemuClaude',
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: 'TemuClaude — Multi-Model AI Orchestration' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TemuClaude — One Question. Eight Minds. One Superior Answer.',
    description: '8 models. Adaptive multi-layer pipeline. Fraction of the cost. Open source. 25% to charity.',
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
  description: 'Multi-model AI orchestration platform. 8 models, an adaptive multi-layer pipeline (up to 10 layers for hard queries), and a cost-aware frontier escalation policy. Open source.',
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

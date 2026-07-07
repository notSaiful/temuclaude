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
  metadataBase: new URL('https://temuclaude.com'),
  title: 'TemuClaude — Multi-Model AI Orchestration | 8 Models, 10-Layer Pipeline',
  description: 'TemuClaude orchestrates 8 frontier AI models in parallel, fuses their answers, verifies with code execution, and quality-checks every response. 25x cheaper than frontier models. Try it free.',
  keywords: ['LLM orchestration', 'multi-model AI', 'Mixture of Agents', 'AI playground', 'model fusion', 'open source AI', 'frontier AI', 'cheap AI API'],
  authors: [{ name: 'Mohammad Saiful Haque' }],
  icons: { icon: '/favicon.svg' },
  openGraph: {
    title: 'TemuClaude — One Question. Eight Minds. One Superior Answer.',
    description: '8 frontier models. 10-layer quality pipeline. 25x cheaper than Fable 5. Open source. 25% to the Ummah Fund.',
    type: 'website',
    url: 'https://temuclaude.com',
    siteName: 'TemuClaude',
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: 'TemuClaude — Multi-Model AI Orchestration' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TemuClaude — One Question. Eight Minds. One Superior Answer.',
    description: '8 models. 10-layer pipeline. 25x cheaper. Open source. 25% to the Ummah.',
    images: ['/og-image.png'],
    site: '@temuclaude',
  },
  robots: { index: true, follow: true },
};

const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Temuclaude',
  applicationCategory: 'DeveloperApplication',
  operatingSystem: 'Web',
  description: 'Multi-model AI orchestration platform that beats frontier models at 28x lower cost.',
  offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
  url: 'https://temuclaude.com',
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
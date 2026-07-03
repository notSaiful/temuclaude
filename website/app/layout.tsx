import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';

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
  title: 'Timuclaude — Open-Source LLM Orchestration | Beat Frontier Models',
  description: 'One question. Many minds. One superior answer. Timuclaude orchestrates 5 AI models to beat frontier models at 28x lower cost. Try it free in the playground. Open source. MIT licensed.',
  keywords: ['LLM orchestration', 'multi-model AI', 'AI playground', 'model comparison', 'open source AI'],
  authors: [{ name: 'Mohammad Saiful Haque' }],
  openGraph: {
    title: 'Timuclaude — Open-Source LLM Orchestration',
    description: 'One question. Many minds. One superior answer. 28x cheaper than frontier models.',
    type: 'website',
    url: 'https://timuclaude.com',
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: 'Timuclaude playground interface' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Timuclaude — Open-Source LLM Orchestration',
    description: 'One question. Many minds. One superior answer. 28x cheaper than frontier models.',
    images: ['/og-image.png'],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body>{children}</body>
    </html>
  );
}
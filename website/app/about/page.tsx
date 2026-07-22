import { Navbar } from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'About Us — TemuClaude',
  description: 'About TemuClaude, an AI orchestration platform for developers and teams.',
};

export default function AboutPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="About Us">
        <div className="container-max max-w-3xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-serif text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
            About TemuClaude
          </h1>
          <p className="text-sm text-text-muted mb-12">Last updated: July 9, 2026</p>

          <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">Who We Are</h2>
              <p>TemuClaude is an AI orchestration platform built by Mohammad Saiful Haque. The service helps developers, researchers, and teams use multiple AI models through one interface, one API, and a quality-checking pipeline.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">What We Provide</h2>
              <p>We provide digital access to an AI playground, developer API, usage dashboard, and enterprise AI orchestration support. Our platform routes requests across model providers, combines strong answers, and verifies responses before returning output where possible.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">Business Model</h2>
              <p>TemuClaude offers a free playground tier, paid monthly plans for higher usage and API access, and custom enterprise plans. Paid access is currently activated by request while hosted checkout is finalized. Plan details are available on our <a href="/pricing" className="text-accent-primary hover:underline">pricing page</a>.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">Open Source Commitment</h2>
              <p>The TemuClaude project is MIT licensed, and we keep the core orchestration work transparent through the public repository linked from the website footer.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">Contact</h2>
              <p>For support, billing, legal, or enterprise enquiries, visit our <a href="/contact" className="text-accent-primary hover:underline">Contact Us page</a>.</p>
            </section>
          </div>
        </div>
      </main>
    </>
  );
}

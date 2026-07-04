'use client';

import { useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';
import { PLANS } from '@/lib/plans';

const faqs = [
  { q: 'How is Temuclaude different from using GPT-5.5 directly?', a: 'GPT-5.5 is one model. Temuclaude orchestrates 8 models — fusing their answers, verifying with code, and quality-checking with self-QA. The result is measurably better, at 7x lower cost.' },
  { q: 'Is it really free?', a: 'Yes. Try it free in the playground — 50 queries/day, no signup required. Upgrade when you need more.' },
  { q: 'Which models does Temuclaude use?', a: '8 models: GLM-5.2, DeepSeek V4 Pro, Hy3 Preview, MiMo-V2.5, Gemini 3 Flash, MiniMax M3, Claude Sonnet 5, and Nemotron 3 Ultra. We route to the best model automatically — you never have to choose.' },
  { q: 'How does the orchestration work?', a: 'Temuclaude classifies your query, routes it to the best model(s), fuses multiple answers, verifies math with code execution, and quality-checks with a self-QA gate. You see the whole process in the playground.' },
  { q: 'Is my data stored?', a: 'No. Queries are processed in real-time and not stored.' },
  { q: 'What about enterprise?', a: 'Enterprise includes SSO, SLA, self-hosted deployment, dedicated support, and 200K queries/month.' },
  { q: 'Can I cancel anytime?', a: 'Yes. No contracts. Cancel anytime from your dashboard or contact us.' },
  { q: 'Do you offer pay-as-you-go?', a: 'Yes. API users can pay per token: $2/M input, $10/M output. Contact us to set up metered billing.' },
];

export default function PricingPage() {
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubscribe = async (planId: string) => {
    setError('');
    setSuccess('');

    if (planId === 'free') {
      window.location.href = '/playground';
      return;
    }

    if (planId === 'enterprise') {
      window.location.href = '/enterprise';
      return;
    }

    if (!email) {
      setError('Please enter your email to subscribe.');
      return;
    }

    setCheckoutLoading(planId);
    try {
      const res = await fetch('/api/payments/create-subscription', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planId, email, name }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || 'Failed to create subscription');
        setCheckoutLoading(null);
        return;
      }

      // Redirect to Razorpay checkout
      if (data.shortUrl) {
        window.location.href = data.shortUrl;
      } else {
        setError('No checkout URL returned. Please try again.');
        setCheckoutLoading(null);
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
      setCheckoutLoading(null);
    }
  };

  const planList = Object.values(PLANS);

  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Pricing">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3 text-center" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Pricing</h1>
          <p className="text-text-secondary text-center mb-10 max-w-xl mx-auto">
            Frontier-level intelligence at 1/5th the cost. Free to try in the playground.
          </p>

          {/* Price comparison banner */}
          <div className="card max-w-3xl mx-auto mb-12" style={{ background: '#F0EDE6' }}>
            <div className="text-center">
              <p className="text-sm text-text-secondary mb-3">vs Frontier Models (per 1M tokens)</p>
              <div className="flex flex-wrap justify-center gap-4 md:gap-8 text-sm">
                <div><span className="text-text-muted">Fable 5</span> <strong className="text-text-primary">$10 / $50</strong></div>
                <div><span className="text-text-muted">GPT-5.5</span> <strong className="text-text-primary">$5 / $30</strong></div>
                <div><span className="text-text-muted">Fugu Ultra</span> <strong className="text-text-primary">$5 / $30</strong></div>
                <div><span className="text-text-muted">Gemini 3.1 Pro</span> <strong className="text-text-primary">$2 / $12</strong></div>
                <div><span className="text-accent-primary font-bold">Temuclaude $2 / $10</span></div>
              </div>
            </div>
          </div>

          {/* Email input for subscription */}
          <div className="max-w-md mx-auto mb-8">
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-border bg-card-bg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary transition-colors"
              aria-label="Email address"
            />
            <input
              type="text"
              placeholder="Your name (optional)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 mt-2 rounded-lg border border-border bg-card-bg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary transition-colors"
              aria-label="Name"
            />
          </div>

          {error && (
            <div className="max-w-md mx-auto mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm text-center">
              {error}
            </div>
          )}
          {success && (
            <div className="max-w-md mx-auto mb-4 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm text-center">
              {success}
            </div>
          )}

          {/* Pricing tiers */}
          <StaggerReveal className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-20">
            {planList.map((tier, i) => (
              <StaggerItem key={i}>
                <div className={`card h-full ${tier.featured ? 'border-accent-primary border-2' : ''}`}>
                  {tier.featured && <div className="badge-accent mb-4 w-fit">Most Popular</div>}
                  <h3 className="text-lg font-semibold text-text-primary mb-1">{tier.name}</h3>
                  <div className="mb-1 flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-text-primary">{tier.priceLabel}</span>
                    <span className="text-sm text-text-muted">{tier.period}</span>
                  </div>
                  <p className="text-sm text-text-secondary mb-4">{tier.description}</p>
                  <ul className="space-y-2 mb-6">
                    {tier.features.map((f, j) => (
                      <li key={j} className="flex items-start gap-2 text-sm text-text-secondary">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3" className="mt-0.5 flex-shrink-0">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={() => handleSubscribe(tier.id)}
                    disabled={checkoutLoading === tier.id}
                    className={`${tier.featured ? 'btn-accent' : 'btn-secondary'} w-full ${checkoutLoading === tier.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {checkoutLoading === tier.id ? 'Redirecting...' : tier.cta}
                  </button>
                </div>
              </StaggerItem>
            ))}
          </StaggerReveal>

          {/* Pay-as-you-go section */}
          <div className="card max-w-4xl mx-auto mb-20">
            <div className="text-center mb-6">
              <h2 className="text-xl font-semibold text-text-primary mb-2">Pay-as-you-go API</h2>
              <p className="text-text-secondary text-sm">For production workloads and variable usage. No commitment.</p>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-4 rounded-lg" style={{ background: '#F0EDE6' }}>
                <div className="text-2xl font-bold text-text-primary">$2</div>
                <div className="text-sm text-text-muted">per 1M input tokens</div>
              </div>
              <div className="p-4 rounded-lg" style={{ background: '#F0EDE6' }}>
                <div className="text-2xl font-bold text-text-primary">$10</div>
                <div className="text-sm text-text-muted">per 1M output tokens</div>
              </div>
              <div className="p-4 rounded-lg" style={{ background: '#F0EDE6' }}>
                <div className="text-2xl font-bold text-text-primary">$0.20</div>
                <div className="text-sm text-text-muted">per 1M cached input</div>
              </div>
            </div>
            <p className="text-center text-sm text-text-secondary mt-4">
              5x cheaper than Fable 5 ($10/$50). 3x cheaper than GPT-5.5 ($5/$30).
            </p>
          </div>

          {/* FAQs */}
          <section className="max-w-2xl mx-auto">
            <h2 className="text-xl font-semibold text-text-primary mb-6 text-center">Frequently Asked Questions</h2>
            <div className="space-y-4">
              {faqs.map((faq, i) => (
                <div key={i} className="card">
                  <h3 className="text-sm font-semibold text-text-primary mb-2">{faq.q}</h3>
                  <p className="text-sm text-text-secondary">{faq.a}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </>
  );
}
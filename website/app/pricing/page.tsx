'use client';

import { useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';
import { PLANS } from '@/lib/plans';

const faqs = [
  { q: 'How is TemuClaude different from using Claude directly?', a: 'Claude is one model. TemuClaude orchestrates 8 models — fusing their answers, verifying math with code execution, and quality-checking every response on 5 rubrics. The result is measurably better, at 30x lower cost than Claude Sonnet 5.' },
  { q: 'Is it really free?', a: 'Yes. Try it free in the playground — 20 queries/day, no signup required. Upgrade when you need more.' },
  { q: 'Which models does TemuClaude use?', a: '8 models: GLM-5.2 (orchestrator), DeepSeek V4 Pro (reasoning), Hy3 Preview (cheapest), Gemini 3 Flash (legal/health), MiniMax M3 (vision/creative), MiMo-V2.5 (multimodal), Claude Sonnet 5 (frontier fallback), and Nemotron 3 Ultra (QA gate, free). We route to the best model automatically.' },
  { q: 'How does the orchestration work?', a: 'TemuClaude classifies your query, routes it to the best model(s), fuses multiple answers through a 3-layer Mixture-of-Agents, verifies math with code execution, and quality-checks with a self-QA gate on 5 rubrics. You see the whole process in the playground.' },
  { q: 'Are the benchmark scores verified?', a: 'Not yet. Our benchmark scores are projected from research analysis of our orchestration architecture. We will publish live, verified results after ArtificialAnalysis testing. We believe in transparency.' },
  { q: 'Is my data stored?', a: 'No. Queries are processed in real-time and not stored. We log routing decisions and quality scores for self-improvement, but never the content of your queries.' },
  { q: 'What about enterprise?', a: 'Enterprise includes SSO/SAML, SLA 99.9%, dedicated support, custom integrations, and unlimited queries. Contact us for details.' },
  { q: 'Can I cancel anytime?', a: 'Yes. No contracts. Cancel anytime from your dashboard or contact us.' },
  { q: 'Do you offer pay-as-you-go?', a: 'Yes. API users pay per token: $0.50/M input, $2.00/M output, $0.05/M cached input. Contact us to set up metered billing.' },
  { q: 'How are you so much cheaper than frontier models?', a: 'We route 60% of queries to free models, 30% to ultra-cheap models ($0.06-0.14/M), and only 10% to premium models. Our 3-layer MoA fusion makes cheap models together smarter than one expensive model alone. You get frontier-level answers at a fraction of the cost.' },
  { q: 'Does TemuClaude give back to the community?', a: 'Yes. 25% of all profit goes to verified charitable causes — food relief, community kitchens, medical clinics, and education programs. Every query you make helps.' },
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
            Frontier-level intelligence at 1/10th the cost. 25% of every payment goes to charity.
          </p>

          {/* Price comparison banner */}
          <div className="card max-w-3xl mx-auto mb-12" style={{ background: '#F0EDE6' }}>
            <div className="text-center">
              <p className="text-sm text-text-secondary mb-3">vs Frontier Models (per 1M tokens)</p>
              <div className="flex flex-wrap justify-center gap-4 md:gap-8 text-sm">
                <div><span className="text-text-muted">Claude Sonnet 5</span> <strong className="text-text-primary">$3 / $15</strong></div>
                <div><span className="text-text-muted">GPT-5.5</span> <strong className="text-text-primary">$5 / $30</strong></div>
                <div><span className="text-text-muted">GPT-5</span> <strong className="text-text-primary">$5 / $25</strong></div>
                <div><span className="text-text-muted">GLM-5.2</span> <strong className="text-text-primary">$1.40 / $4.40</strong></div>
                <div><span className="text-accent-primary font-bold">TemuClaude $0.50 / $2.00</span></div>
              </div>
            </div>
          </div>

          {/* Charity Fund banner */}
          <div className="card max-w-3xl mx-auto mb-12" style={{ background: '#788C5D', color: '#fff' }}>
            <div className="text-center">
              <p className="text-sm opacity-90 mb-1">25% of all profit goes to charity</p>
              <p className="text-xs opacity-75">Food relief · Community kitchens · Medical clinics · Education programs</p>
            </div>
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

          {/* Pricing tiers — 4 plans */}
          <StaggerReveal className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto mb-20">
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
                <div className="text-2xl font-bold text-text-primary">$0.50</div>
                <div className="text-sm text-text-muted">per 1M input tokens</div>
              </div>
              <div className="p-4 rounded-lg" style={{ background: '#F0EDE6' }}>
                <div className="text-2xl font-bold text-text-primary">$2.00</div>
                <div className="text-sm text-text-muted">per 1M output tokens</div>
              </div>
              <div className="p-4 rounded-lg" style={{ background: '#F0EDE6' }}>
                <div className="text-2xl font-bold text-text-primary">$0.05</div>
                <div className="text-sm text-text-muted">per 1M cached input</div>
              </div>
            </div>
            <p className="text-center text-sm text-text-secondary mt-4">
              30x cheaper than Claude Sonnet 5 ($3/$15). 15x cheaper than GPT-5.5 ($5/$30). 7x cheaper than GLM-5.2 ($1.40/$4.40).
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
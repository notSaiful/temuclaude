'use client';

import { useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';
import { PLANS } from '@/lib/plans';
import { getStoredSession } from '@/lib/auth';

const checkoutEnabled = process.env.NEXT_PUBLIC_BILLING_CHECKOUT_ENABLED === 'true';

const faqs = [
  { q: 'How is TemuClaude different from a frontier direct model?', a: 'A direct model uses one provider for every request. TemuClaude uses a bounded hybrid pool, with verification and escalation only when a task needs them. The result is designed to preserve quality while materially reducing blended token cost.' },
  { q: 'Is it really free?', a: 'Yes. Sign in and try the playground with standard free usage limits. Upgrade when you need more.' },
  { q: 'Which models does TemuClaude use?', a: 'The current pool is DeepSeek V4 Flash and Pro, GLM-5.2, MiniMax M3, Gemini 3.5 Flash, GPT-5.6 Luna, Grok 4.5, and Nemotron 3 Ultra. GPT-5.6 Terra is restricted to emergency fallback only. We route by task and provider availability.' },
  { q: 'How does the orchestration work?', a: 'TemuClaude classifies your query, routes it to the best model(s) from the pool, fuses multiple answers through Mixture-of-Agents, and runs self-consistency sampling for math and reasoning. An independent verifier model (Nemotron 3 Ultra) then scores the answer in a self-QA gate; if it flags issues, a reflexion pass produces a corrected answer. Routing is cost-aware — easy work goes to cheaper models, with escalation only on verified failures.' },
  { q: 'Are the benchmark scores verified?', a: 'Not yet. Our benchmark scores are projected from research analysis of our orchestration architecture. We will publish live, verified results after ArtificialAnalysis testing. We believe in transparency.' },
  { q: 'Is my data stored?', a: 'No. Queries are processed in real-time and not stored. We log routing decisions and quality scores for self-improvement, but never the content of your queries.' },
  { q: 'What about enterprise?', a: 'Enterprise plans include custom token volume allocations, SSO/SAML, SLA 99.9%, dedicated support, custom integrations, and contract overages. Contact us for details.' },
  { q: 'Can I cancel anytime?', a: 'Yes. No contracts. Cancel anytime from your dashboard or contact us.' },
  { q: 'How do you control cost?', a: 'We route easy work to DeepSeek Flash, reserve expensive escalation for verified failures, and avoid sending every request through a full ensemble. You pay for the work the task needs, not a premium route by default.' },
  { q: 'Does TemuClaude give back to the community?', a: 'Yes. 25% of all profit goes to verified charitable causes — food relief, community kitchens, medical clinics, and education programs. Every query you make helps.' },
];

export default function PricingPage() {
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [tokens, setTokens] = useState(10); // in Millions of tokens per month

  const handleSubscribe = async (planId: string) => {
    setError('');
    const session = await getStoredSession().catch(() => null);

    if (planId === 'free') {
      window.location.href = session ? '/playground' : '/login?returnTo=/playground';
      return;
    }

    if (planId === 'enterprise') {
      window.location.href = '/enterprise';
      return;
    }

    if (!checkoutEnabled) {
      const plan = PLANS[planId as keyof typeof PLANS];
      const subject = encodeURIComponent(`TemuClaude ${plan?.name || planId} plan access`);
      const body = encodeURIComponent(
        `Hi TemuClaude team,\n\nI would like access to the ${plan?.name || planId} plan.\n\nAccount email: ${session?.email || ''}\nExpected monthly usage:\nUse case:\n\nThanks.`
      );
      window.location.href = `mailto:hello@temuclaude.com?subject=${subject}&body=${body}`;
      return;
    }

    if (!session) {
      window.location.href = `/login?returnTo=/pricing`;
      return;
    }

    setCheckoutLoading(planId);
    try {
      const res = await fetch('/api/payments/create-subscription', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: session.email, name: session.name, planId }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || 'Failed to initiate subscription');
        setCheckoutLoading(null);
        return;
      }

      // Redirect to hosted checkout when billing is enabled.
      if (data.shortUrl) {
        window.location.href = data.shortUrl;
      } else {
        // Fallback to mock success redirect
        window.location.href = `/payment-success?planId=${planId}`;
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
      setCheckoutLoading(null);
    }
  };

  const [activeTab, setActiveTab] = useState<'individual' | 'enterprise'>('individual');
  const planList = Object.values(PLANS);

  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-24 px-6" aria-label="Pricing">
        <div className="container-max">
          <div className="text-center mb-10">
            <h1 className="text-3xl md:text-4xl font-serif text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Plans & Pricing</h1>
            <p className="text-text-secondary max-w-xl mx-auto">
              Frontier-quality ambition with a cost-aware routing policy. 25% of every payment goes to charity.
            </p>
          </div>

          {/* Interactive Cost Calculator */}
          <div className="card max-w-3xl mx-auto mb-12 overflow-hidden bg-white shadow-sm border border-border-subtle" style={{ borderRadius: '16px', padding: '28px' }}>
            <div className="text-center mb-6">
              <h2 className="text-xl font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>API Token Cost Calculator</h2>
              <p className="text-sm text-text-secondary">Drag the slider to adjust your estimated monthly token volume.</p>
            </div>

            <div className="mb-8">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-text-primary">Monthly Volume:</span>
                <span className="text-lg font-mono text-accent-primary font-bold">{tokens}M tokens</span>
              </div>
              <input
                type="range"
                min="1"
                max="100"
                value={tokens}
                onChange={(e) => setTokens(Number(e.target.value))}
                className="w-full h-1 bg-border-default rounded-lg appearance-none cursor-pointer accent-accent-primary"
                style={{ outline: 'none' }}
              />
              <div className="flex justify-between text-[10px] text-text-muted mt-1 font-mono">
                <span>1M tokens</span>
                <span>50M tokens</span>
                <span>100M tokens</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div className="p-4 rounded-lg bg-bg-secondary border border-border-subtle">
                <div className="text-xs text-text-muted mb-1 font-medium">TemuClaude Cost</div>
                <div className="text-2xl font-mono font-bold text-accent-olive">${(tokens * 1.35).toFixed(2)}</div>
                <div className="text-[10px] text-text-muted mt-1 font-mono">~$1.35/M modeled blend</div>
              </div>
              <div className="p-4 rounded-lg bg-bg-secondary border border-border-subtle">
                <div className="text-xs text-text-muted mb-1 font-medium">Frontier Direct Baseline</div>
                <div className="text-2xl font-mono font-bold text-text-secondary">${(tokens * 50.00).toFixed(2)}</div>
                <div className="text-[10px] text-text-muted mt-1 font-mono">$10.00 / $50.00 split</div>
              </div>
              <div className="p-4 rounded-lg bg-accent-light/10 border border-accent-primary/20">
                <div className="text-xs text-accent-primary font-semibold mb-1">Your Monthly Savings</div>
                <div className="text-2xl font-mono font-bold text-accent-primary">${(tokens * 48.65).toFixed(2)}</div>
                <div className="text-[10px] text-accent-primary/80 mt-1 font-medium font-semibold">Modeled savings from cost-aware routing</div>
              </div>
            </div>
          </div>

          {/* Charity Fund banner */}
          <div className="max-w-3xl mx-auto mb-12 p-6 rounded-sm bg-[#738E54] text-white border border-border-subtle shadow-sm">
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

          {!checkoutEnabled && (
            <div className="max-w-3xl mx-auto mb-8 p-4 rounded-lg bg-bg-secondary border border-border-subtle text-sm text-text-secondary text-center">
              Paid plans are available by request while hosted checkout is being finalized. Free access is live now.
            </div>
          )}

          {/* Segmented control tabs */}
          <div className="flex justify-center gap-4 mb-12">
            <button
              onClick={() => setActiveTab('individual')}
              className={`px-6 py-2.5 rounded-full text-sm font-medium transition-all ${
                activeTab === 'individual'
                  ? 'bg-accent-primary text-white shadow-sm'
                  : 'bg-bg-secondary text-text-secondary hover:text-text-primary border border-border-subtle'
              }`}
            >
              Individual Plans
            </button>
            <button
              onClick={() => setActiveTab('enterprise')}
              className={`px-6 py-2.5 rounded-full text-sm font-medium transition-all ${
                activeTab === 'enterprise'
                  ? 'bg-accent-primary text-white shadow-sm'
                  : 'bg-bg-secondary text-text-secondary hover:text-text-primary border border-border-subtle'
              }`}
            >
              Enterprise Tier
            </button>
          </div>

          {/* Pricing tiers */}
          {activeTab === 'individual' ? (
            <StaggerReveal className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto mb-20">
              {planList
                .filter((p) => p.id !== 'enterprise')
                .map((tier, i) => (
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
          ) : (
            <div className="max-w-md mx-auto mb-20 animate-fade-in">
              {planList
                .filter((p) => p.id === 'enterprise')
                .map((tier, i) => (
                  <div key={i} className="card border-accent-primary border-2">
                    <div className="badge-accent mb-4 w-fit">Scale Orchestration</div>
                    <h3 className="text-xl font-semibold text-text-primary mb-2">{tier.name}</h3>
                    <div className="mb-3 flex items-baseline gap-1">
                      <span className="text-4xl font-bold text-text-primary">{tier.priceLabel}</span>
                      <span className="text-sm text-text-muted">{tier.period}</span>
                    </div>
                    <p className="text-sm text-text-secondary mb-6">{tier.description}</p>
                    <ul className="space-y-3 mb-8">
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
                      className="btn-accent w-full py-3"
                    >
                      {checkoutLoading === tier.id ? 'Redirecting...' : tier.cta}
                    </button>
                  </div>
                ))}
            </div>
          )}

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

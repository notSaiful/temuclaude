'use client';

import { useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';
import { PLANS } from '@/lib/plans';

const faqs = [
  { q: 'How is TemuClaude different from using Claude directly?', a: 'Claude is one model. TemuClaude orchestrates our hybrid model pool — fusing their answers, self-checking every response, and retrying if quality is low. The result is measurably better, at 10x to 50x lower cost than Claude 3.5 Sonnet.' },
  { q: 'Is it really free?', a: 'Yes. Try it free in the playground — 20 queries/day, no signup required. Upgrade when you need more.' },
  { q: 'Which models does TemuClaude use?', a: 'Unified Model Pool: GLM-5.2 (orchestrator), DeepSeek Pro (reasoning), Llama 3.3 (specialist), Gemini 2.0 Flash (worker/RAG), Mistral Large 2 (logic), Claude 3.5 Sonnet (frontier fallback), and MiMo-V2.5 (multimodal). We route to the best model automatically.' },
  { q: 'How does the orchestration work?', a: 'TemuClaude classifies your query, routes it to the best model(s), fuses multiple answers through Mixture-of-Agents, checks logical consistency using Z3 and SymPy solvers inside secure execution sandboxes, and runs a self-play Generator-Discriminator correction loop.' },
  { q: 'Are the benchmark scores verified?', a: 'Not yet. Our benchmark scores are projected from research analysis of our orchestration architecture. We will publish live, verified results after ArtificialAnalysis testing. We believe in transparency.' },
  { q: 'Is my data stored?', a: 'No. Queries are processed in real-time and not stored. We log routing decisions and quality scores for self-improvement, but never the content of your queries.' },
  { q: 'What about enterprise?', a: 'Enterprise includes SSO/SAML, SLA 99.9%, dedicated support, custom integrations, and unlimited queries. Contact us for details.' },
  { q: 'Can I cancel anytime?', a: 'Yes. No contracts. Cancel anytime from your dashboard or contact us.' },
  { q: 'Do you offer pay-as-you-go?', a: 'Yes. API users pay per token: ~$1.44/M blended (varies by question difficulty — trivial costs less, hard costs more). Contact us to set up metered billing.' },
  { q: 'How are you so much cheaper than frontier models?', a: 'We route 60% of queries to Llama 3.3 / Gemini 2.0 Flash (cheapest), 30% to specialized shepherding logic, and only 10% trigger the full MCTS-guided multi-agent fusion. You pay for smart routing, not raw frontier compute.' },
  { q: 'Does TemuClaude give back to the community?', a: 'Yes. 25% of all profit goes to verified charitable causes — food relief, community kitchens, medical clinics, and education programs. Every query you make helps.' },
];

export default function PricingPage() {
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tokens, setTokens] = useState(10); // in Millions of tokens per month

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
        body: JSON.stringify({ email, name, planId }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || 'Failed to initiate subscription');
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
            Frontier-level intelligence at a fraction of the cost. 25% of every payment goes to charity.
          </p>

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
                <div className="text-2xl font-mono font-bold text-accent-olive">${(tokens * 1.44).toFixed(2)}</div>
                <div className="text-[10px] text-text-muted mt-1 font-mono">~$1.44/M blended</div>
              </div>
              <div className="p-4 rounded-lg bg-bg-secondary border border-border-subtle">
                <div className="text-xs text-text-muted mb-1 font-medium">Claude 3.5 Sonnet</div>
                <div className="text-2xl font-mono font-bold text-text-secondary">${(tokens * 15.00).toFixed(2)}</div>
                <div className="text-[10px] text-text-muted mt-1 font-mono">$3.00 / $15.00 split</div>
              </div>
              <div className="p-4 rounded-lg bg-accent-light/10 border border-accent-primary/20">
                <div className="text-xs text-accent-primary font-semibold mb-1">Your Monthly Savings</div>
                <div className="text-2xl font-mono font-bold text-accent-primary">${(tokens * 13.56).toFixed(2)}</div>
                <div className="text-[10px] text-accent-primary/80 mt-1 font-medium font-semibold">Up to 90% savings</div>
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
                <div className="text-2xl font-bold text-text-primary">~$1.44</div>
                <div className="text-sm text-text-muted">per 1M tokens (blended)</div>
              </div>
              <div className="p-4 rounded-lg" style={{ background: '#F0EDE6' }}>
                <div className="text-2xl font-bold text-text-primary">$0.06</div>
                <div className="text-sm text-text-muted">per 1M trivial (Llama 3.3)</div>
              </div>
              <div className="p-4 rounded-lg" style={{ background: '#F0EDE6' }}>
                <div className="text-2xl font-bold text-text-primary">Free</div>
                <div className="text-sm text-text-muted">QA gate (Gemini 2.0)</div>
              </div>
            </div>
            <p className="text-center text-sm text-text-secondary mt-4">
              10x to 50x cheaper than Claude 3.5 Sonnet. You pay for smart routing, not raw frontier compute.
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
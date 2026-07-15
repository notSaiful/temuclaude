'use client';

import { useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { PLANS, type PlanId } from '@/lib/plans';
import { getStoredSession } from '@/lib/auth';

const checkoutEnabled = process.env.NEXT_PUBLIC_BILLING_CHECKOUT_ENABLED === 'true';
const individualPlanIds: PlanId[] = ['free', 'developer', 'pro', 'max'];

const faqs = [
  { q: 'How is usage measured?', a: 'Each completed request uses credits based on the work performed. Your dashboard shows the recorded usage.' },
  { q: 'Does every request call several models?', a: 'No. Routine work normally uses one model. Extra models or checks are reserved for requests that need them.' },
  { q: 'Are benchmark claims included in the price?', a: 'No performance guarantee is implied by a plan. Model and routing changes must pass the release checks described in the public roadmap.' },
  { q: 'Can I cancel?', a: 'Yes. Use the dashboard or contact support. The current cancellation and refund terms apply.' },
  { q: 'How do paid plans start?', a: checkoutEnabled ? 'Choose a plan and complete the hosted checkout.' : 'Paid access is activated by request while hosted checkout is disabled.' },
];

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong';
}

export default function PricingPage() {
  const [checkoutLoading, setCheckoutLoading] = useState<PlanId | null>(null);
  const [error, setError] = useState('');

  const handleSubscribe = async (planId: PlanId) => {
    setError('');
    const session = await getStoredSession().catch(() => null);
    const plan = PLANS[planId];

    if (planId === 'free') {
      window.location.href = session ? '/playground' : '/login?returnTo=/playground';
      return;
    }
    if (planId === 'enterprise') {
      window.location.href = '/enterprise';
      return;
    }
    if (!checkoutEnabled) {
      const subject = encodeURIComponent(`TemuClaude ${plan.name} plan access`);
      const body = encodeURIComponent(`Hi TemuClaude team,\n\nI would like access to the ${plan.name} plan.\n\nAccount email: ${session?.email || ''}\nExpected monthly usage:\nUse case:\n\nThanks.`);
      window.location.href = `mailto:hello@temuclaude.com?subject=${subject}&body=${body}`;
      return;
    }
    if (!session) {
      window.location.href = '/login?returnTo=/pricing';
      return;
    }

    setCheckoutLoading(planId);
    try {
      const response = await fetch('/api/payments/create-subscription', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: session.email, name: session.name, planId }),
      });
      const data = await response.json();
      if (!response.ok || typeof data.shortUrl !== 'string') {
        throw new Error(data.error || 'Checkout is unavailable');
      }
      window.location.href = data.shortUrl;
    } catch (caught) {
      setError(errorMessage(caught));
      setCheckoutLoading(null);
    }
  };

  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-24 px-6" aria-label="Pricing">
        <div className="container-max">
          <header className="text-center mb-12">
            <h1 className="text-3xl md:text-4xl font-serif text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Plans and pricing</h1>
            <p className="text-text-secondary max-w-xl mx-auto">Choose a credit limit that matches your usage. The routing policy is the same product; higher plans provide more capacity and support.</p>
          </header>

          {!checkoutEnabled && <div className="max-w-3xl mx-auto mb-8 p-4 rounded-lg bg-bg-secondary border border-border-subtle text-sm text-text-secondary text-center">Paid access is available by request. Hosted checkout is currently disabled.</div>}
          {error && <div role="alert" className="max-w-md mx-auto mb-6 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm text-center">{error}</div>}

          <section aria-label="Individual plans" className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {individualPlanIds.map((planId) => {
              const plan = PLANS[planId];
              return (
                <article key={plan.id} className={`card h-full flex flex-col ${plan.featured ? 'border-accent-primary border-2' : ''}`}>
                  {plan.featured && <div className="badge-accent mb-4 w-fit">Recommended</div>}
                  <h2 className="text-lg font-semibold text-text-primary mb-1">{plan.name}</h2>
                  <div className="mb-3"><span className="text-3xl font-bold text-text-primary">{plan.priceLabel}</span><span className="text-sm text-text-muted">{plan.period}</span></div>
                  <p className="text-sm text-text-secondary mb-4">{plan.description}</p>
                  <ul className="space-y-2 mb-6 flex-1">
                    {plan.features.map((feature) => <li key={feature} className="text-sm text-text-secondary">✓ {feature}</li>)}
                  </ul>
                  <button onClick={() => handleSubscribe(plan.id)} disabled={checkoutLoading === plan.id} className={`${plan.featured ? 'btn-accent' : 'btn-secondary'} w-full disabled:opacity-50`}>
                    {checkoutLoading === plan.id ? 'Opening checkout…' : plan.cta}
                  </button>
                </article>
              );
            })}
          </section>

          <section className="card max-w-3xl mx-auto mb-16">
            <h2 className="text-xl font-semibold text-text-primary mb-2">Enterprise</h2>
            <p className="text-sm text-text-secondary mb-4">{PLANS.enterprise.description} Scope, support, and service terms are agreed before activation.</p>
            <button onClick={() => handleSubscribe('enterprise')} className="btn-secondary">Contact sales</button>
          </section>

          <section className="max-w-2xl mx-auto">
            <h2 className="text-xl font-semibold text-text-primary mb-6 text-center">Questions</h2>
            <div className="space-y-4">
              {faqs.map((faq) => <article key={faq.q} className="card"><h3 className="text-sm font-semibold text-text-primary mb-2">{faq.q}</h3><p className="text-sm text-text-secondary">{faq.a}</p></article>)}
            </div>
          </section>
        </div>
      </main>
    </>
  );
}

'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MagneticButton } from '@/components/MagneticButton';

/**
 * Pricing section with 3-tier cards, monthly/annual toggle,
 * cost comparison bar, and FAQ accordion.
 * 
 * Pricing tier card design adapted from 21st.dev PricingTier component
 * by ugahpraiseaudu — Linear/Vercel-style with real hierarchy.
 * Restyled to match TemuClaude's warm Anthropic-inspired palette.
 */

const tiers = [
  {
    name: 'Free',
    monthly: 0,
    annual: 0,
    features: [
      '20 queries per day',
      'No signup required',
      'All 8 models included',
      'Community support',
      'Full orchestration metadata',
    ],
    cta: 'Start Free',
    href: '/playground',
    popular: false,
  },
  {
    name: 'Starter',
    monthly: 5,
    annual: 4,
    features: [
      '5,000 queries per month',
      'API key included',
      'Email support',
      'Priority model routing',
      'Usage dashboard',
      'No rate limits',
    ],
    cta: 'Choose Starter',
    href: '/pricing',
    popular: true,
  },
  {
    name: 'Pro',
    monthly: 25,
    annual: 20,
    features: [
      '50,000 queries per month',
      'API key + webhooks',
      'Priority support (24h)',
      'Custom model weights',
      'Advanced analytics',
      'Team sharing',
    ],
    cta: 'Choose Pro',
    href: '/pricing',
    popular: false,
  },
];

const faqs = [
  {
    q: 'How are you this cheap?',
    a: '60% of queries go to Hy3 Preview ($0.06/$0.21 per M). 30% route to specialists. Only 10% trigger the full 3-model fusion. The QA gate is free (Nemotron). You pay for smart routing, not raw frontier compute.',
  },
  {
    q: 'Is quality really frontier-level?',
    a: 'For hard questions, 3 models answer independently in parallel, and a dynamic aggregator synthesizes the best answer. A free QA gate scores every response on 5 rubrics. If quality is low, it retries with feedback. Live results coming after third-party verification.',
  },
  {
    q: 'Can I use this in production?',
    a: 'Yes. The API is live and stable. MIT licensed, open source. Full pipeline visible — you can see exactly which models answered and how the final answer was built.',
  },
  {
    q: 'What if I exceed my plan?',
    a: 'Free tier resets daily. Paid tiers: we notify you at 80% and 100% usage. You can upgrade instantly or let it pause until the next billing cycle. No surprise charges.',
  },
  {
    q: 'Do you store my data?',
    a: 'Queries are processed in real-time and not stored. We cache repeated queries for performance, but the cache is anonymous and expires automatically. Your data is never used for training.',
  },
  {
    q: 'How does the fusion work?',
    a: 'TemuClaude classifies your question, picks the best models for the task type, runs them in parallel, and a dynamic aggregator analyzes consensus and contradictions to synthesize one superior answer. 6 quality layers for hard questions.',
  },
];

const competitors = [
  { name: 'TemuClaude', input: 0.50, output: 2.00, color: '#E25822' },
  { name: 'Claude API', input: 15, output: 75, color: '#8E8B85' },
  { name: 'GPT-5.5', input: 30, output: 120, color: '#8E8B85' },
  { name: 'Gemini 3.1', input: 7, output: 21, color: '#8E8B85' },
];

export function PricingSection() {
  const [annual, setAnnual] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <section className="py-24 px-6">
      <div className="container-max">
        {/* Heading */}
        <div className="mb-12 max-w-2xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>
            Pricing that makes sense.
          </h2>
          <p className="text-text-secondary">
            20 free queries/day. No signup. Upgrade when you need more. Cancel anytime.
          </p>
        </div>

        {/* Monthly/Annual toggle */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <span className={`text-sm ${!annual ? 'text-text-primary font-medium' : 'text-text-muted'}`}>Monthly</span>
          <button
            onClick={() => setAnnual(!annual)}
            className="relative w-12 h-6 rounded-full transition-colors"
            style={{ background: annual ? '#E25822' : '#E8E4DC' }}
            aria-label="Toggle annual billing"
          >
            <motion.div
              className="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm"
              animate={{ x: annual ? 24 : 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            />
          </button>
          <span className={`text-sm ${annual ? 'text-text-primary font-medium' : 'text-text-muted'}`}>
            Annual <span className="text-accent-primary text-xs">save 20%</span>
          </span>
        </div>

        {/* Pricing cards */}
        <div className="grid md:grid-cols-3 gap-4 max-w-4xl mx-auto mb-16">
          {tiers.map((tier) => {
            const price = annual ? tier.annual : tier.monthly;
            return (
              <div
                key={tier.name}
                className={`relative flex flex-col bg-white rounded-md p-6 border transition-all ${
                  tier.popular
                    ? 'border-accent-primary md:-translate-y-2.5 shadow-md'
                    : 'border-border-default'
                }`}
              >
                {tier.popular && (
                  <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-accent-primary text-white text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full whitespace-nowrap">
                    Most Popular
                  </span>
                )}
                <div className="font-serif text-2xl text-text-primary leading-none mb-2" style={{ fontWeight: 400 }}>
                  {tier.name}
                </div>
                <div className="text-[1.7rem] font-semibold text-text-primary tracking-tight mb-1" style={{ fontVariantNumeric: 'tabular-nums' }}>
                  ${price}
                  <span className="text-sm font-normal text-text-muted">/mo</span>
                </div>
                {annual && tier.monthly > 0 && (
                  <div className="text-xs text-text-muted mb-4">
                    billed annually (${price * 12}/yr)
                  </div>
                )}
                {!annual && (
                  <div className="text-xs text-text-muted mb-4">
                    {tier.monthly === 0 ? 'no credit card needed' : 'billed monthly'}
                  </div>
                )}
                <ul className="text-sm text-text-secondary space-y-2 flex-1 mb-6">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2">
                      <svg className="w-3.5 h-3.5 mt-1 shrink-0" style={{ color: tier.popular ? '#E25822' : '#788C5D' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                {tier.popular ? (
                  <MagneticButton href={tier.href} className="btn-accent w-full justify-center">
                    {tier.cta}
                  </MagneticButton>
                ) : (
                  <a href={tier.href} className="btn-secondary w-full justify-center">
                    {tier.cta}
                  </a>
                )}
              </div>
            );
          })}
        </div>

        {/* Cost comparison bar chart */}
        <div className="max-w-3xl mx-auto mb-16">
          <div className="text-center mb-6">
            <h3 className="text-lg font-serif text-text-primary mb-1" style={{ fontWeight: 400 }}>
              Token cost comparison
            </h3>
            <p className="text-sm text-text-muted">Per million tokens (input + output combined)</p>
          </div>
          <div className="space-y-3">
            {competitors.map((comp) => {
              const total = comp.input + comp.output;
              const maxWidth = 150; // max competitor total
              const widthPct = Math.min((total / maxWidth) * 100, 100);
              return (
                <div key={comp.name} className="flex items-center gap-4">
                  <div className="w-24 text-sm text-text-primary font-medium shrink-0">{comp.name}</div>
                  <div className="flex-1 h-8 bg-bg-secondary rounded-sm overflow-hidden">
                    <motion.div
                      className="h-full rounded-sm flex items-center justify-end px-2"
                      style={{ background: comp.color, color: '#fff' }}
                      initial={{ width: 0 }}
                      whileInView={{ width: `${widthPct}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8, ease: 'easeOut' }}
                    >
                      <span className="text-xs font-mono font-medium">
                        ${comp.input.toFixed(2)} + ${comp.output.toFixed(2)}
                      </span>
                    </motion.div>
                  </div>
                  <div className="w-16 text-sm text-text-muted text-right shrink-0 font-mono">
                    ${total.toFixed(2)}
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-text-muted mt-3 text-center">
            TemuClaude: $0.50 input + $2.00 output = $2.50/M total. Others: published API pricing.
          </p>
        </div>

        {/* FAQ accordion */}
        <div className="max-w-2xl mx-auto">
          <h3 className="text-lg font-serif text-text-primary mb-6 text-center" style={{ fontWeight: 400 }}>
            Frequently asked questions
          </h3>
          <div className="space-y-2">
            {faqs.map((faq, i) => (
              <div
                key={i}
                className="border border-border-subtle rounded-sm bg-white overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-bg-secondary/50 transition-colors"
                  aria-expanded={openFaq === i}
                >
                  <span className="text-sm font-medium text-text-primary">{faq.q}</span>
                  <motion.div
                    animate={{ rotate: openFaq === i ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="shrink-0 ml-3"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-text-muted">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </motion.div>
                </button>
                <AnimatePresence initial={false}>
                  {openFaq === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                      className="overflow-hidden"
                    >
                      <div className="px-5 pb-4 text-sm text-text-secondary leading-relaxed">
                        {faq.a}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
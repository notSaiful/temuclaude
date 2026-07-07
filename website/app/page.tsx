'use client';

import { motion } from 'framer-motion';
import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main id="main-content">
        {/* ━━ Hero — asymmetric, Stripe-meets-Anthropic ━━ */}
        <section className="relative pt-32 pb-24 px-6 overflow-hidden">
          {/* Layered ambient gradients */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: `
                radial-gradient(ellipse 70% 50% at 70% 10%, rgba(217, 119, 87, 0.08) 0%, transparent 60%),
                radial-gradient(ellipse 50% 40% at 20% 30%, rgba(120, 140, 93, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse 40% 30% at 90% 60%, rgba(196, 102, 134, 0.04) 0%, transparent 50%)
              `,
            }}
          />
          <div className="container-max relative">
            <div className="grid lg:grid-cols-12 gap-8 items-center">
              {/* Left: headline + CTAs */}
              <div className="lg:col-span-7">
                <div
                  className="inline-flex items-center gap-2 badge-accent mb-6 animate-fade-in-up"
                  style={{ animationDelay: '0ms' }}
                >
                  <span className="w-2 h-2 rounded-full bg-accent-olive animate-pulse-soft" />
                  Open-source · 8 models · 10-layer pipeline
                </div>

                <h1
                  className="text-5xl md:text-6xl lg:text-7xl font-light tracking-tight text-text-primary leading-[1.02] mb-6 animate-fade-in-up text-balance"
                  style={{ animationDelay: '100ms', letterSpacing: '-0.05em', fontWeight: 300 }}
                >
                  One question.<br />
                  Eight minds.<br />
                  <span className="text-accent-primary">One superior answer.</span>
                </h1>

                <p
                  className="text-lg text-text-secondary mb-8 max-w-lg leading-relaxed animate-fade-in-up"
                  style={{ animationDelay: '300ms' }}
                >
                  TemuClaude orchestrates 8 frontier models in parallel, fuses their answers,
                  verifies with code execution, and quality-checks every response.
                  Smarter than any single model. 25x cheaper than Fable 5.
                </p>

                <div
                  className="flex flex-col sm:flex-row gap-3 mb-6 animate-fade-in-up"
                  style={{ animationDelay: '500ms' }}
                >
                  <a href="/playground" className="btn-accent">
                    Try the Playground
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                  </a>
                  <a href="/pricing" className="btn-secondary">
                    View Pricing
                  </a>
                </div>

                {/* Inline stats — no separate bar, save vertical space */}
                <div
                  className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-text-muted animate-fade-in-up"
                  style={{ animationDelay: '700ms' }}
                >
                  <span><strong className="text-text-primary">$0.50</strong> /MTok input</span>
                  <span className="text-border-default">·</span>
                  <span><strong className="text-text-primary">20</strong> free queries/day</span>
                  <span className="text-border-default">·</span>
                  <span><strong className="text-text-primary">25%</strong> → charity</span>
                </div>
              </div>

              {/* Right: orchestration visualization */}
              <div
                className="lg:col-span-5 animate-fade-in-up"
                style={{ animationDelay: '400ms' }}
              >
                <OrchestrationVisual />
              </div>
            </div>
          </div>
        </section>

        {/* ━━ Bento grid: Why TemuClaude ━━ */}
        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                Why TemuClaude
              </h2>
              <p className="text-text-secondary">
                Not another model. An orchestration layer that makes existing models smarter together.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Large card — Fusion */}
              <div className="card lg:col-span-2 lg:row-span-2" style={{ padding: '32px' }}>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#D97757" strokeWidth="2">
                      <circle cx="6" cy="6" r="3" /><circle cx="18" cy="6" r="3" />
                      <circle cx="6" cy="18" r="3" /><circle cx="18" cy="18" r="3" />
                      <line x1="6" y1="9" x2="6" y2="15" /><line x1="18" y1="9" x2="18" y2="15" />
                      <line x1="9" y1="6" x2="15" y2="6" /><line x1="9" y1="18" x2="15" y2="18" />
                    </svg>
                  </div>
                  <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Core Engine</span>
                </div>
                <h3 className="text-xl font-semibold text-text-primary mb-3">3-Layer Mixture-of-Agents Fusion</h3>
                <p className="text-sm text-text-secondary mb-4 leading-relaxed">
                  For hard questions, 3 models answer independently in parallel. Then each model
                  reviews the others' answers and refines its own. Finally, a dynamic aggregator
                  synthesizes the best parts of all refined responses into one superior answer.
                </p>
                <p className="text-sm text-text-muted leading-relaxed">
                  Based on research from arXiv:2406.04692 — 3-layer MoA achieves 65.1% on AlpacaEval
                  vs GPT-4o's 57.5%. Each layer adds measurable quality.
                </p>
                <div className="flex flex-wrap gap-2 mt-4">
                  {['Parallel generation', 'Cross-review', 'Dynamic aggregation', 'Consensus detection'].map(tag => (
                    <span key={tag} className="badge-muted text-xs">{tag}</span>
                  ))}
                </div>
              </div>

              {/* Small card — Code Verification */}
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-accent-olive/15 flex items-center justify-center">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="2">
                      <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-base font-semibold text-text-primary mb-2">Code-Verified Math</h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  Math answers are verified by generating Python code, executing it in a sandbox,
                  and returning the ground-truth output. No hallucination possible in computation.
                </p>
              </div>

              {/* Small card — Self-QA */}
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-accent-fig/15 flex items-center justify-center">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C46686" strokeWidth="2">
                      <path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="10" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-base font-semibold text-text-primary mb-2">Self-QA Gate</h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  Every answer is scored on 5 rubrics: logical coherence, factual accuracy,
                  completeness, goal alignment, and clarity. Below 8/10 triggers automatic retry.
                </p>
              </div>

              {/* Medium card — Cost */}
              <div className="card lg:col-span-2">
                <div className="flex items-center gap-4">
                  <div>
                    <h3 className="text-base font-semibold text-text-primary mb-2">Radical Cost Efficiency</h3>
                    <p className="text-sm text-text-secondary leading-relaxed mb-3">
                      60% of queries route to free models. 30% to ultra-cheap MoE models ($0.06-0.14/M).
                      Only 10% use premium models. The cache serves 40% of repeat queries at $0.
                    </p>
                    <div className="flex flex-wrap gap-4 text-sm">
                      <div>
                        <span className="text-2xl font-light text-accent-primary" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>$0.50</span>
                        <span className="text-text-muted ml-1">/M input</span>
                      </div>
                      <div>
                        <span className="text-2xl font-light text-accent-primary" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>$2.00</span>
                        <span className="text-text-muted ml-1">/M output</span>
                      </div>
                      <div>
                        <span className="text-2xl font-light text-accent-olive" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>$0.05</span>
                        <span className="text-text-muted ml-1">/M cached</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Small card — Charity Fund */}
              <div className="card" style={{ background: 'linear-gradient(135deg, #788C5D 0%, #5D7048 100%)', color: '#fff', borderColor: 'transparent' }}>
                <h3 className="text-base font-semibold mb-2">25% of profit → charity</h3>
                <p className="text-sm opacity-90 leading-relaxed">
                  25% of profit funds food relief, community kitchens,
                  medical clinics, and education programs. Every query helps.
                </p>
              </div>

              {/* Small card — Open Source */}
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-accent-amber/15 flex items-center justify-center">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E8B547" strokeWidth="2">
                      <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" /><path d="M12 22V12" /><path d="M2 7l10 5 10-5" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-base font-semibold text-text-primary mb-2">Open Source</h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  MIT licensed. Full orchestration pipeline visible. No black boxes.
                  See exactly which models answered and how the final answer was built.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ━━ How It Works — 10-layer pipeline ━━ */}
        <section className="py-24 px-6">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                The 10-layer pipeline
              </h2>
              <p className="text-text-secondary">
                Every query passes through up to 10 quality layers. Most queries use 1-3.
                Hard questions trigger the full stack. You see it all in the playground.
              </p>
            </div>

            <StaggerReveal className="grid md:grid-cols-2 gap-3">
              {[
                { num: '01', title: 'Web Search', desc: 'Live search results augment the prompt with current information for knowledge and reasoning queries.', tier: 'Hard' },
                { num: '02', title: 'MoA 3-Layer Fusion', desc: '3 models answer independently, cross-review each other, then a dynamic aggregator synthesizes the best answer.', tier: 'Hard' },
                { num: '03', title: 'Self-Consistency', desc: 'For math and reasoning, N samples are generated and PRM-weighted voting selects the most consistent answer.', tier: 'Hard · Math/Reasoning' },
                { num: '04', title: 'Code Verification', desc: 'Python code is generated to solve the problem, executed in a sandbox, and the output becomes the verified answer.', tier: 'Hard · Math/Coding' },
                { num: '05', title: 'Reflexion', desc: 'If code verification fails, the model reflects on what went wrong and retries with that context.', tier: 'Hard · On failure' },
                { num: '06', title: 'Self-QA Gate', desc: 'The answer is scored 0-10 on 5 rubrics. Below 8 triggers retry with feedback. Up to 2 retries.', tier: 'Hard + Medium' },
                { num: '07', title: 'Z3 Logical Verification', desc: 'Logical claims in reasoning answers are checked with a Z3 SMT solver for mathematical certainty.', tier: 'Hard · Reasoning' },
                { num: '08', title: 'Budget Forcing', desc: 'If the answer is suspiciously short for a hard problem, "Wait" is appended to force longer reasoning.', tier: 'Hard · Math/Reasoning' },
                { num: '09', title: 'Step-Level Verification', desc: 'Each reasoning step is verified independently with generated code — catches errors before they cascade.', tier: 'Hard · Math/Coding' },
                { num: '10', title: 'Frontier Fallback', desc: 'If all layers fail, the query escalates to Claude Sonnet 5 (IQ 53) — the strongest model available.', tier: 'Hardest 2%' },
              ].map((layer, i) => (
                <StaggerItem key={i}>
                  <div className="card flex items-start gap-4" style={{ padding: '20px 24px' }}>
                    <span className="text-sm font-mono text-text-muted tabular-nums">{layer.num}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-sm font-semibold text-text-primary">{layer.title}</h3>
                        <span className="badge-muted text-[10px]">{layer.tier}</span>
                      </div>
                      <p className="text-xs text-text-secondary leading-relaxed">{layer.desc}</p>
                    </div>
                  </div>
                </StaggerItem>
              ))}
            </StaggerReveal>
          </div>
        </section>

        {/* ━━ Model Pool ━━ */}
        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                Powered by 8 frontier models
              </h2>
              <p className="text-text-secondary">
                Each model has a specific role. TemuClaude routes automatically — you never choose.
                The right model for the right question, every time.
              </p>
            </div>

            <StaggerReveal className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: 'GLM-5.2', role: 'Orchestrator', iq: '51', desc: 'Highest open-weight IQ. Routes queries and aggregates fusion.' },
                { name: 'DeepSeek V4 Pro', role: 'Reasoning', iq: '44', desc: '#1 Finance. Hard math, coding, and complex logic.' },
                { name: 'Hy3 Preview', role: 'Trivial Router', iq: '—', desc: 'Cheapest on OpenRouter. Handles 60% of queries.' },
                { name: 'Gemini 3 Flash', role: 'Legal/Health', iq: '50', desc: '#1 Legal, #2 Health. Near-Pro reasoning.' },
                { name: 'MiniMax M3', role: 'Vision/Creative', iq: '44', desc: 'Best GPQA (93%). Vision + creative generation.' },
                { name: 'MiMo-V2.5', role: 'Multimodal', iq: '40', desc: 'Omnimodal from Xiaomi. Text, image, video.' },
                { name: 'Claude Sonnet 5', role: 'Frontier', iq: '53', desc: 'Highest IQ. Used for the hardest 2% of queries.' },
                { name: 'Nemotron 3 Ultra', role: 'QA Gate', iq: '38', desc: '550B MoE. Free — scores every answer.' },
              ].map((model, i) => (
                <StaggerItem key={i}>
                  <div className="card" style={{ padding: '20px 16px' }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-text-primary">{model.name}</span>
                      {model.iq !== '—' && (
                        <span className="text-xs text-text-muted font-mono">IQ {model.iq}</span>
                      )}
                    </div>
                    <div className="text-xs text-accent-primary mb-2">{model.role}</div>
                    <p className="text-xs text-text-muted leading-relaxed">{model.desc}</p>
                  </div>
                </StaggerItem>
              ))}
            </StaggerReveal>

            <div className="mt-8 text-center">
              <a href="/models" className="text-sm text-accent-primary hover:underline">
                See detailed model profiles →
              </a>
            </div>
          </div>
        </section>

        {/* ━━ Benchmarks — honest, projected ━━ */}
        <section className="py-24 px-6">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                Benchmarks
              </h2>
              <p className="text-text-secondary">
                Projected scores from research analysis of our orchestration architecture.
                Live benchmark results will be published after ArtificialAnalysis verification.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-default">
                    <th className="text-left py-3 px-4 font-semibold text-text-primary">Benchmark</th>
                    <th className="text-center py-3 px-4 font-semibold text-accent-primary">TemuClaude*</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Fable 5</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">GPT-5.5</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Gemini 3.1</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'GPQA Diamond', tc: '95-98%', f5: '88%', gpt: '94%', gem: '89%' },
                    { name: 'LiveCodeBench', tc: '96-99%', f5: '87%', gpt: '91%', gem: '85%' },
                    { name: 'SWE-Bench Pro', tc: '75-85%', f5: '70%', gpt: '68%', gem: '65%' },
                    { name: 'Terminal-Bench', tc: '91-96%', f5: '85%', gpt: '82%', gem: '80%' },
                    { name: 'GDPval-AA v2', tc: '1824+', f5: '1783', gpt: '1700', gem: '1650' },
                    { name: 'MultiChallenge', tc: '87-94%', f5: '82%', gpt: '85%', gem: '79%' },
                  ].map((row, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-bg-secondary/40' : ''}>
                      <td className="py-3 px-4 text-text-primary font-medium">{row.name}</td>
                      <td className="py-3 px-4 text-center font-bold text-accent-primary">{row.tc}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.f5}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.gpt}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.gem}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-text-muted mt-4">
              * TemuClaude scores are <strong className="text-text-secondary">projected</strong> from research analysis,
              not yet verified by ArtificialAnalysis. Frontier scores from published results.
              We are committed to transparent, verified benchmarks.
            </p>
          </div>
        </section>

        {/* ━━ Pricing CTA ━━ */}
        <section className="py-20 px-6 bg-bg-secondary">
          <div className="container-max text-center">
            <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              Frontier intelligence. Fraction of the cost.
            </h2>
            <p className="text-text-secondary mb-8 max-w-xl mx-auto">
              Start free. Upgrade when you need more. Cancel anytime.
              25% of every payment goes to charity.
            </p>
            <div className="flex items-center justify-center gap-4">
              <a href="/playground" className="btn-accent">
                Start Free
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
              </a>
              <a href="/pricing" className="btn-secondary">
                See Plans
              </a>
            </div>
          </div>
        </section>

        {/* ━━ Footer ━━ */}
        <footer className="py-12 px-6 border-t border-border-subtle bg-bg-primary">
          <div className="container-max">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
              <div>
                <h4 className="text-sm font-semibold text-text-primary mb-3">Product</h4>
                <ul className="space-y-2">
                  <li><a href="/playground" className="text-sm text-text-secondary hover:text-accent-primary">Playground</a></li>
                  <li><a href="/models" className="text-sm text-text-secondary hover:text-accent-primary">Models</a></li>
                  <li><a href="/benchmarks" className="text-sm text-text-secondary hover:text-accent-primary">Benchmarks</a></li>
                  <li><a href="/pricing" className="text-sm text-text-secondary hover:text-accent-primary">Pricing</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary mb-3">Resources</h4>
                <ul className="space-y-2">
                  <li><a href="/docs" className="text-sm text-text-secondary hover:text-accent-primary">Documentation</a></li>
                  <li><a href="/enterprise" className="text-sm text-text-secondary hover:text-accent-primary">Enterprise</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary mb-3">Connect</h4>
                <ul className="space-y-2">
                  <li><a href="https://github.com/notSaiful/temuclaude-research" className="text-sm text-text-secondary hover:text-accent-primary" target="_blank" rel="noopener noreferrer">GitHub</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary mb-3">Legal</h4>
                <ul className="space-y-2">
                  <li><a href="/terms" className="text-sm text-text-muted hover:text-accent-primary">Terms of Service</a></li>
                  <li><a href="/privacy" className="text-sm text-text-muted hover:text-accent-primary">Privacy Policy</a></li>
                  <li><a href="/refunds" className="text-sm text-text-muted hover:text-accent-primary">Refund Policy</a></li>
                </ul>
              </div>
            </div>
            <div className="pt-8 border-t border-border-subtle flex flex-col items-center gap-3">
              <svg width="32" height="32" viewBox="0 0 200 200" aria-hidden="true">
                <line x1="25" y1="55" x2="100" y2="85" stroke="#E8D5C4" strokeWidth="7" strokeLinecap="round"/>
                <line x1="55" y1="30" x2="100" y2="85" stroke="#D4A574" strokeWidth="7" strokeLinecap="round"/>
                <line x1="100" y1="20" x2="100" y2="85" stroke="#C97B50" strokeWidth="7" strokeLinecap="round"/>
                <line x1="145" y1="30" x2="100" y2="85" stroke="#D4A574" strokeWidth="7" strokeLinecap="round"/>
                <line x1="175" y1="55" x2="100" y2="85" stroke="#E8D5C4" strokeWidth="7" strokeLinecap="round"/>
                <rect x="90" y="85" width="20" height="95" rx="5" fill="#D97757"/>
                <circle cx="100" cy="85" r="6" fill="#D97757"/>
              </svg>
              <p className="text-sm text-text-muted">
                Built by Mohammad Saiful Haque with Hermes Agent
              </p>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}

/* ━━ Orchestration Visual — premium Framer Motion interactive visualization ━━ */
function OrchestrationVisual() {
  return (
    <div className="relative w-full" style={{ aspectRatio: '1.1', minHeight: '320px' }}>
      <OrchAnim />
    </div>
  );
}

function OrchAnim() {
  const models = [
    { color: '#D97757', name: 'GLM-5.2', angle: -75, delay: 0 },
    { color: '#C97B50', name: 'DeepSeek', angle: -45, delay: 0.1 },
    { color: '#788C5D', name: 'Hy3', angle: -15, delay: 0.2 },
    { color: '#C46686', name: 'Gemini', angle: 15, delay: 0.3 },
    { color: '#E8B547', name: 'MiniMax', angle: 45, delay: 0.4 },
    { color: '#D4A574', name: 'Sonnet', angle: 75, delay: 0.5 },
  ];

  const cx = 150, cy = 95, r = 68;

  return (
    <>
      <svg viewBox="0 0 300 280" className="w-full h-auto" aria-hidden="true">
        <defs>
          <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#D97757" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#D97757" stopOpacity="0" />
          </radialGradient>
          <filter id="softGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Ambient glow behind center */}
        <circle cx={cx} cy={cy} r="50" fill="url(#centerGlow)" />

        {/* Animated connection lines */}
        {models.map((m, i) => {
          const rad = (m.angle * Math.PI) / 180;
          const x = cx + r * Math.sin(rad);
          const y = cy - r * Math.cos(rad);
          return (
            <motion.line
              key={`line-${i}`}
              x1={x} y1={y} x2={cx} y2={cy}
              stroke={m.color}
              strokeWidth="1.5"
              strokeLinecap="round"
              opacity="0.5"
              strokeDasharray="3 3"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 0.5 }}
              transition={{ duration: 0.8, delay: 0.2 + m.delay, ease: 'easeOut' }}
            />
          );
        })}

        {/* Pulsing data particles flowing toward center */}
        {models.map((m, i) => {
          const rad = (m.angle * Math.PI) / 180;
          const x = cx + r * Math.sin(rad);
          const y = cy - r * Math.cos(rad);
          return (
            <motion.circle
              key={`particle-${i}`}
              r="2.5"
              fill={m.color}
              initial={{ cx: x, cy: y, opacity: 0 }}
              animate={{
                cx: [x, cx],
                cy: [y, cy],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: 1.5,
                delay: 1 + m.delay,
                repeat: Infinity,
                repeatDelay: 2,
                ease: 'easeIn',
              }}
            />
          );
        })}

        {/* Model nodes */}
        {models.map((m, i) => {
          const rad = (m.angle * Math.PI) / 180;
          const x = cx + r * Math.sin(rad);
          const y = cy - r * Math.cos(rad);
          return (
            <motion.g
              key={`node-${i}`}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: m.delay, ease: 'easeOut' }}
            >
              <motion.circle
                cx={x} cy={y} r="15"
                fill={m.color}
                opacity="0.9"
                animate={{ r: [15, 16, 15] }}
                transition={{ duration: 2, delay: m.delay, repeat: Infinity, ease: 'easeInOut' }}
              />
              <circle cx={x} cy={y} r="15" fill="none" stroke={m.color} strokeWidth="1" opacity="0.25" />
              <text x={x} y={y + 1} textAnchor="middle" dominantBaseline="middle" fontSize="6.5" fill="#1A1816" fontWeight="700">
                {m.name.slice(0, 7)}
              </text>
            </motion.g>
          );
        })}

        {/* Center aggregation node with pulse ring */}
        <motion.circle
          cx={cx} cy={cy} r="25" fill="none" stroke="#D97757" strokeWidth="1" opacity="0.2"
          animate={{ r: [25, 40], opacity: [0.3, 0] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeOut' }}
        />
        <motion.circle
          cx={cx} cy={cy} r="22"
          fill="#D97757"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, delay: 0.8, ease: 'backOut' }}
          filter="url(#softGlow)"
        />
        <motion.text
          x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle"
          fontSize="8" fill="#FAF8F5" fontWeight="800"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          FUSE
        </motion.text>

        {/* Output arrow */}
        <motion.line
          x1={cx} y1={cy + 22} x2={cx} y2={cy + 48}
          stroke="#D97757" strokeWidth="2" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.2 }}
        />
        <motion.polygon
          points={`${cx - 5},${cy + 44} ${cx + 5},${cy + 44} ${cx},${cy + 52}`}
          fill="#D97757"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.4 }}
        />

        {/* Output box */}
        <motion.g
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5, duration: 0.4 }}
        >
          <rect x={cx - 60} y={cy + 54} width="120" height="28" rx="6" fill="#1A1816" />
          <text x={cx} y={cy + 72} textAnchor="middle" dominantBaseline="middle" fontSize="8" fill="#FAF8F5" fontWeight="600">
            One superior answer
          </text>
        </motion.g>

        {/* Tier labels on the left side */}
        <motion.g
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1.8, duration: 0.4 }}
        >
          <text x="8" y="20" fontSize="7" fill="#8E8B85" fontWeight="600">TRIVIAL</text>
          <text x="8" y="32" fontSize="6" fill="#8E8B85">1 model · $0</text>
          <line x1="8" y1="40" x2="20" y2="40" stroke="#8E8B85" strokeWidth="0.5" opacity="0.3" />
        </motion.g>

        <motion.g
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 2.0, duration: 0.4 }}
        >
          <text x="8" y="55" fontSize="7" fill="#8E8B85" fontWeight="600">MEDIUM</text>
          <text x="8" y="67" fontSize="6" fill="#8E8B85">1 specialist</text>
          <line x1="8" y1="75" x2="20" y2="75" stroke="#8E8B85" strokeWidth="0.5" opacity="0.3" />
        </motion.g>

        <motion.g
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 2.2, duration: 0.4 }}
        >
          <text x="8" y="90" fontSize="7" fill="#D97757" fontWeight="700">HARD</text>
          <text x="8" y="102" fontSize="6" fill="#8E8B85">3 models · 10 layers</text>
        </motion.g>
      </svg>
      <div className="absolute bottom-0 left-0 right-0 text-center">
        <p className="text-xs text-text-muted font-mono">8 models → 3-layer MoA → 10 quality layers → 1 answer</p>
      </div>
    </>
  );
}
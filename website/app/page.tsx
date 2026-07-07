'use client';

import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main id="main-content">
        {/* ━━ Hero ━━ */}
        <section className="relative pt-32 pb-24 px-6 overflow-hidden">
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
              <div className="lg:col-span-7">
                <div
                  className="inline-flex items-center gap-2 badge-accent mb-6 animate-fade-in-up"
                  style={{ animationDelay: '0ms' }}
                >
                  <span className="w-2 h-2 rounded-full bg-accent-olive animate-pulse-soft" />
                  One API · 8 models · MIT licensed
                </div>

                <h1
                  className="text-5xl md:text-6xl lg:text-7xl font-light tracking-tight text-text-primary leading-[1.02] mb-6 animate-fade-in-up text-balance"
                  style={{ animationDelay: '100ms', letterSpacing: '-0.05em', fontWeight: 300 }}
                >
                  Frontier-quality AI.<br />
                  <span className="text-accent-primary">Fraction of the cost.</span><br />
                  One API call.
                </h1>

                <p
                  className="text-lg text-text-secondary mb-8 max-w-lg leading-relaxed animate-fade-in-up"
                  style={{ animationDelay: '300ms' }}
                >
                  TemuClaude runs 8 AI models in parallel, fuses their best answers,
                  verifies math with code execution, and self-checks every response.
                  You get one answer — smarter than any single model, at a fraction of the cost.
                </p>

                {/* Code snippet — shows devs exactly how to use it */}
                <div
                  className="mb-6 animate-fade-in-up"
                  style={{ animationDelay: '450ms' }}
                >
                  <div className="bg-bg-dark rounded-md p-4 max-w-md font-mono text-sm overflow-x-auto">
                    <div className="text-text-muted text-xs mb-2"># One request. One answer. No model selection.</div>
                    <div><span className="text-accent-olive">curl</span> <span className="text-accent-fig">-X POST</span> temuclaude.com/api/chat \</div>
                    <div className="pl-4">-H <span className="text-accent-amber">"Content-Type: application/json"</span> \</div>
                    <div className="pl-4">-d <span className="text-accent-amber">'{"{"}"messages":[{"{"}"role":"user","content":"hi"{"}"}]{"}"}'</span></div>
                  </div>
                </div>

                <div
                  className="flex flex-col sm:flex-row gap-3 mb-6 animate-fade-in-up"
                  style={{ animationDelay: '500ms' }}
                >
                  <a href="/playground" className="btn-accent">
                    Try Free — 20 queries/day
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                  </a>
                  <a href="/pricing" className="btn-secondary">
                    View Pricing
                  </a>
                </div>

                <div
                  className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-text-muted animate-fade-in-up"
                  style={{ animationDelay: '700ms' }}
                >
                  <span><strong className="text-text-primary">$0.50</strong> /MTok input</span>
                  <span className="text-border-default">·</span>
                  <span><strong className="text-text-primary">$2.00</strong> /MTok output</span>
                  <span className="text-border-default">·</span>
                  <span><strong className="text-text-primary">No signup</strong> to try</span>
                </div>
              </div>

              <div
                className="lg:col-span-5 animate-fade-in-up flex items-center justify-center"
                style={{ animationDelay: '400ms' }}
              >
                <svg width="280" height="280" viewBox="0 0 200 200" className="opacity-90" aria-hidden="true">
                  <line x1="25" y1="55" x2="100" y2="85" stroke="#E8D5C4" strokeWidth="7" strokeLinecap="round"/>
                  <line x1="55" y1="30" x2="100" y2="85" stroke="#D4A574" strokeWidth="7" strokeLinecap="round"/>
                  <line x1="100" y1="20" x2="100" y2="85" stroke="#C97B50" strokeWidth="7" strokeLinecap="round"/>
                  <line x1="145" y1="30" x2="100" y2="85" stroke="#D4A574" strokeWidth="7" strokeLinecap="round"/>
                  <line x1="175" y1="55" x2="100" y2="85" stroke="#E8D5C4" strokeWidth="7" strokeLinecap="round"/>
                  <rect x="90" y="85" width="20" height="95" rx="5" fill="#D97757"/>
                  <circle cx="100" cy="85" r="6" fill="#D97757"/>
                </svg>
              </div>
            </div>
          </div>
        </section>

        {/* ━━ Why TemuClaude — for vibe coders ━━ */}
        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                Built for builders
              </h2>
              <p className="text-text-secondary">
                Stop paying $30/M tokens for GPT-5.5. Stop wrangling multiple APIs.
                One endpoint, frontier quality, a fraction of the cost.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Large card — Fusion */}
              <div className="card lg:col-span-2 lg:row-span-2" style={{ padding: '32px' }}>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#E25822" strokeWidth="2">
                      <circle cx="6" cy="6" r="3" /><circle cx="18" cy="6" r="3" />
                      <circle cx="6" cy="18" r="3" /><circle cx="18" cy="18" r="3" />
                      <line x1="6" y1="9" x2="6" y2="15" /><line x1="18" y1="9" x2="18" y2="15" />
                      <line x1="9" y1="6" x2="15" y2="6" /><line x1="9" y1="18" x2="15" y2="18" />
                    </svg>
                  </div>
                  <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Core Engine</span>
                </div>
                <h3 className="text-xl font-semibold text-text-primary mb-3">3 models answer. 1 wins.</h3>
                <p className="text-sm text-text-secondary mb-4 leading-relaxed">
                  For hard questions, 3 models answer independently in parallel. Each one
                  reviews the others' answers and refines its own. Then a dynamic aggregator
                  picks the best parts and synthesizes one superior answer.
                </p>
                <p className="text-sm text-text-muted leading-relaxed">
                  The result: measurably smarter than any single model — including GPT-5 and Claude.
                  You don't choose models. TemuClaude does it for you, automatically.
                </p>
                <div className="flex flex-wrap gap-2 mt-4">
                  {['Parallel generation', 'Cross-review', 'Dynamic aggregation', 'Consensus detection'].map(tag => (
                    <span key={tag} className="badge-muted text-xs">{tag}</span>
                  ))}
                </div>
              </div>

              {/* Code Verification */}
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-accent-olive/15 flex items-center justify-center">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="2">
                      <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-base font-semibold text-text-primary mb-2">Math that can't lie</h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  Math answers are verified by generating Python code, running it in a sandbox,
                  and returning the actual output. No hallucinated numbers. Ever.
                </p>
              </div>

              {/* Self-QA */}
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-accent-fig/15 flex items-center justify-center">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C46686" strokeWidth="2">
                      <path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="10" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-base font-semibold text-text-primary mb-2">Self-checking</h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  Every answer is scored on 5 quality rubrics. If it scores below 8/10,
                  TemuClaude retries with feedback. You always get the best version.
                </p>
              </div>

              {/* Cost */}
              <div className="card lg:col-span-2">
                <div className="flex items-center gap-4">
                  <div>
                    <h3 className="text-base font-semibold text-text-primary mb-2">Radically cheap</h3>
                    <p className="text-sm text-text-secondary leading-relaxed mb-3">
                      60% of queries go to free models. 30% to ultra-cheap models ($0.06-0.14/M).
                      Only 10% use premium models. The cache serves repeat queries at $0.
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

              {/* Charity */}
              <div className="card" style={{ background: 'linear-gradient(135deg, #788C5D 0%, #5D7048 100%)', color: '#fff', borderColor: 'transparent' }}>
                <h3 className="text-base font-semibold mb-2">25% of profit → charity</h3>
                <p className="text-sm opacity-90 leading-relaxed">
                  Food relief, community kitchens, medical clinics, and education programs.
                  Your queries help people.
                </p>
              </div>

              {/* Open Source */}
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-accent-amber/15 flex items-center justify-center">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E8B547" strokeWidth="2">
                      <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" /><path d="M12 22V12" /><path d="M2 7l10 5 10-5" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-base font-semibold text-text-primary mb-2">Open source</h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  MIT licensed. Full pipeline visible. See exactly which models answered
                  and how the final answer was built. No black boxes.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ━━ How It Works — simplified for builders ━━ */}
        <section className="py-24 px-6">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                How it works
              </h2>
              <p className="text-text-secondary">
                You send one request. TemuClaude does the rest — and shows you exactly what happened.
              </p>
            </div>

            <StaggerReveal className="grid md:grid-cols-3 gap-6">
              {[
                {
                  num: '01',
                  title: 'You send a question',
                  desc: 'One API call. No model selection, no parameters, no temperature tuning. Just your question.',
                },
                {
                  num: '02',
                  title: 'TemuClaude routes & fuses',
                  desc: 'It classifies your question, picks the best models, runs them in parallel, cross-reviews, and synthesizes the best answer. 10 quality layers for hard questions.',
                },
                {
                  num: '03',
                  title: 'You get one answer',
                  desc: 'Plus a full breakdown: which models ran, how long each took, the quality score, and which techniques were used. Full transparency.',
                },
              ].map((step, i) => (
                <StaggerItem key={i}>
                  <div className="card h-full">
                    <div className="text-2xl font-light text-accent-primary mb-3" style={{ fontWeight: 300 }}>{step.num}</div>
                    <h3 className="text-lg font-semibold text-text-primary mb-2">{step.title}</h3>
                    <p className="text-sm text-text-secondary leading-relaxed">{step.desc}</p>
                  </div>
                </StaggerItem>
              ))}
            </StaggerReveal>

            {/* Orchestration metadata example */}
            <div className="mt-12 max-w-2xl mx-auto">
              <p className="text-sm text-text-muted mb-3 text-center">Every response includes full orchestration metadata:</p>
              <div className="bg-bg-dark rounded-md p-4 font-mono text-sm overflow-x-auto">
                <div className="text-text-muted text-xs mb-2">// Returned with every answer</div>
                <div className="text-accent-olive">"orchestration"</div>
                <div className="pl-4 text-accent-fig">"taskType"</div><div className="pl-8 text-text-inverse">"math"</div>
                <div className="pl-4 text-accent-fig">"tier"</div><div className="pl-8 text-text-inverse">"hard"</div>
                <div className="pl-4 text-accent-fig">"models"</div><div className="pl-8 text-text-inverse">["glm-5.2", "deepseek-v4-pro", "gemini-3-flash"]</div>
                <div className="pl-4 text-accent-fig">"qaScore"</div><div className="pl-8 text-text-inverse">9.2</div>
                <div className="pl-4 text-accent-fig">"cost"</div><div className="pl-8 text-text-inverse">"$0.015"</div>
                <div className="pl-4 text-accent-fig">"techniques"</div><div className="pl-8 text-text-inverse">["moa-3-layer", "code-verification", "reflexion"]</div>
              </div>
            </div>
          </div>
        </section>

        {/* ━━ Model Pool ━━ */}
        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                8 models. You never pick.
              </h2>
              <p className="text-text-secondary">
                TemuClaude routes automatically — the right model for the right question.
                Easy questions cost $0. Hard ones get the full fusion pipeline.
              </p>
            </div>

            <StaggerReveal className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: 'GLM-5.2', role: 'Orchestrator', iq: '51', desc: 'Highest open-weight IQ. Routes and aggregates.' },
                { name: 'DeepSeek V4 Pro', role: 'Reasoning', iq: '44', desc: 'Hard math, coding, complex logic.' },
                { name: 'Hy3 Preview', role: 'Cheap router', iq: '—', desc: 'Handles 60% of queries at lowest cost.' },
                { name: 'Gemini 3 Flash', role: 'Legal/Health', iq: '50', desc: '#1 Legal, #2 Health on benchmarks.' },
                { name: 'MiniMax M3', role: 'Vision/Creative', iq: '44', desc: 'Best GPQA score. Vision + creative.' },
                { name: 'MiMo-V2.5', role: 'Multimodal', iq: '40', desc: 'Text, image, video. From Xiaomi.' },
                { name: 'Claude Sonnet 5', role: 'Frontier', iq: '53', desc: 'Highest IQ. Used for hardest 2% only.' },
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

        {/* ━━ Benchmarks ━━ */}
        <section className="py-24 px-6">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                Benchmarks
              </h2>
              <p className="text-text-secondary">
                Projected from research analysis. Live results coming after third-party verification.
                We show projected scores because we believe in honesty over hype.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-default">
                    <th className="text-left py-3 px-4 font-semibold text-text-primary">Benchmark</th>
                    <th className="text-center py-3 px-4 font-semibold text-accent-primary">TemuClaude*</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Claude Sonnet 5</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">GPT-5.5</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Gemini 3.1</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'GPQA Diamond', tc: '95-98%', comp: '88%', gpt: '94%', gem: '89%' },
                    { name: 'LiveCodeBench', tc: '96-99%', comp: '87%', gpt: '91%', gem: '85%' },
                    { name: 'SWE-Bench Pro', tc: '75-85%', comp: '70%', gpt: '68%', gem: '65%' },
                    { name: 'Terminal-Bench', tc: '91-96%', comp: '85%', gpt: '82%', gem: '80%' },
                    { name: 'MultiChallenge', tc: '87-94%', comp: '82%', gpt: '85%', gem: '79%' },
                  ].map((row, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-bg-secondary/40' : ''}>
                      <td className="py-3 px-4 text-text-primary font-medium">{row.name}</td>
                      <td className="py-3 px-4 text-center font-bold text-accent-primary">{row.tc}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.comp}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.gpt}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.gem}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-text-muted mt-4">
              * Projected from research analysis, not yet verified by ArtificialAnalysis. Frontier scores from published results.
            </p>
          </div>
        </section>

        {/* ━━ Pricing CTA ━━ */}
        <section className="py-20 px-6 bg-bg-secondary">
          <div className="container-max text-center">
            <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              $0.50 per million tokens.<br />That's it.
            </h2>
            <p className="text-text-secondary mb-8 max-w-xl mx-auto">
              20 free queries/day. No signup. Upgrade when you need more. Cancel anytime.
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
                  <li><a href="https://github.com/notSaiful/temuclaude" className="text-sm text-text-secondary hover:text-accent-primary" target="_blank" rel="noopener noreferrer">GitHub</a></li>
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
                Built by Mohammad Saiful Haque · MIT Licensed
              </p>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}

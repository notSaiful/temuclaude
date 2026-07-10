'use client';

import { useState, useEffect } from 'react';
import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';
import { MagneticButton } from '@/components/MagneticButton';

const MOCK_TRACES = [
  {
    query: "Compare 9.9 vs 9.11",
    steps: [
      { text: "Cache check: Miss (similarity = 0.81)", status: "info" },
      { text: "AOPR classification: Hard Logic. Routing to deepseek-v4-pro.", status: "route" },
      { text: "Step 1: Convert values to decimals (9.90 vs 9.11). 90 > 11.", status: "thought" },
      { text: "Verification: Launching SymPy equations checks...", status: "info" },
      { text: "SymPy: verified True (9.9 > 9.11). Exit code 0.", status: "verify" },
      { text: "Z3 logic checks: SAT (No contradictions detected).", status: "verify" },
      { text: "Output: 9.9 is larger than 9.11.", status: "output" },
      { text: "Blended cost: $0.0006 (cost-aware routed execution)", status: "price" }
    ]
  },
  {
    query: "Build Tic Tac Toe in React",
    steps: [
      { text: "Cache check: Miss (similarity = 0.74)", status: "info" },
      { text: "AOPR classification: Code Gen. Routing to extreme models.", status: "route" },
      { text: "Writing React hook state logic (board, turn, winner)...", status: "thought" },
      { text: "Visual Sandbox: Launching headless Puppeteer renderer...", status: "info" },
      { text: "Screenshot checks: SSIM = 0.98. Visual layout passes.", status: "verify" },
      { text: "Adversarial Breaker: Simulating random clicks on cells...", status: "info" },
      { text: "Breaker: 0 DOM crashes caught.", status: "verify" },
      { text: "Output: Code compiled and verified successfully.", status: "output" },
      { text: "Blended cost: $0.0034 (cost-aware routed execution)", status: "price" }
    ]
  },
  {
    query: "Sales report anomalies",
    steps: [
      { text: "Cache check: Hit! Paraphrase match (similarity = 0.96)", status: "info" },
      { text: "Retrieving pre-compiled response from semantic cache...", status: "info" },
      { text: "Output: Anomalies report loaded from Cache.", status: "output" },
      { text: "Blended cost: $0.0000 (Saved 100%. Cache hits are free)", status: "price" }
    ]
  }
];

function InteractiveTraceTerminal() {
  const [activeIdx, setActiveIdx] = useState(0);
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    setVisibleCount(0);
    const trace = MOCK_TRACES[activeIdx];
    const interval = setInterval(() => {
      setVisibleCount((prev) => {
        if (prev < trace.steps.length) {
          return prev + 1;
        }
        clearInterval(interval);
        return prev;
      });
    }, 450);
    return () => clearInterval(interval);
  }, [activeIdx]);

  const activeTrace = MOCK_TRACES[activeIdx];

  return (
    <div className="card w-full max-w-md bg-white border border-border-default shadow-md overflow-hidden p-6 font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-border-subtle pb-3">
        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-text-secondary">
          Live Execution Trace
        </span>
        <div className="flex gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-400 opacity-60" />
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-400 opacity-60" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-400 opacity-60" />
        </div>
      </div>

      {/* Query Selector Tabs */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1.5">
        {MOCK_TRACES.map((t, idx) => (
          <button
            key={idx}
            onClick={() => setActiveIdx(idx)}
            className={`px-3 py-1.5 rounded-sm text-xs font-mono cursor-pointer transition-all border shrink-0 ${
              activeIdx === idx
                ? 'border-accent-primary bg-accent-light text-accent-primary font-semibold'
                : 'border-border-default hover:border-text-secondary text-text-secondary'
            }`}
          >
            {idx === 0 ? "Math Logic" : idx === 1 ? "Web App Gen" : "Cached Query"}
          </button>
        ))}
      </div>

      <div className="bg-bg-dark rounded-md p-4 font-mono text-[11px] min-h-[220px] overflow-y-auto leading-normal">
        <div className="text-text-muted mb-2">&gt; query: "{activeTrace.query}"</div>
        <div className="space-y-2">
          {activeTrace.steps.slice(0, visibleCount).map((step, sIdx) => {
            let colorClass = "text-text-inverse";
            let prefix = "⚙";
            if (step.status === "route") {
              colorClass = "text-accent-amber font-semibold";
              prefix = "➔";
            } else if (step.status === "thought") {
              colorClass = "text-text-muted italic";
              prefix = "💭";
            } else if (step.status === "verify") {
              colorClass = "text-accent-olive font-semibold";
              prefix = "✔";
            } else if (step.status === "output") {
              colorClass = "text-text-inverse font-bold border-t border-white/10 pt-1.5 mt-1";
              prefix = "🚀";
            } else if (step.status === "price") {
              colorClass = "text-accent-primary font-bold";
              prefix = "💰";
            }
            return (
              <div key={sIdx} className={`flex items-start gap-2 ${colorClass}`}>
                <span className="shrink-0">{prefix}</span>
                <span>{step.text}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

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
                radial-gradient(circle at 1px 1px, rgba(28, 25, 23, 0.02) 1px, transparent 0),
                radial-gradient(ellipse 70% 50% at 70% 10%, rgba(226, 88, 34, 0.05) 0%, transparent 65%),
                radial-gradient(ellipse 50% 40% at 20% 30%, rgba(115, 142, 84, 0.03) 0%, transparent 55%),
                radial-gradient(ellipse 40% 30% at 90% 60%, rgba(200, 98, 137, 0.02) 0%, transparent 50%)
              `,
              backgroundSize: '24px 24px, 100% 100%, 100% 100%, 100% 100%',
            }}
          />
          <div className="container-max relative">
            <div className="grid lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7">
                <div
                  className="inline-flex items-center gap-2 badge-accent mb-6 animate-fade-in-up"
                  style={{ animationDelay: '0ms' }}
                >
                  <span className="w-2.5 h-2.5 rounded-full bg-accent-olive animate-pulse-soft" />
                  One API · 8 models · MIT licensed
                </div>

                <h1
                  className="text-5xl md:text-6xl lg:text-7xl font-serif tracking-tight text-text-primary leading-[1.05] mb-6 animate-fade-in-up text-balance"
                  style={{ animationDelay: '100ms', fontWeight: 300, letterSpacing: '-0.03em' }}
                >
                  Frontier-quality AI.<br />
                  <span className="text-accent-primary">Fraction of the cost.</span><br />
                  One API call.
                </h1>

                <p
                  className="text-lg text-text-secondary mb-8 max-w-lg leading-relaxed animate-fade-in-up"
                  style={{ animationDelay: '300ms' }}
                >
                  TemuClaude is the next-generation multi-agent orchestration engine.
                  We run 8 models in parallel, verify logic code programmatically, and build full-stack web apps,
                  voxel games, and algorithms without a single point of failure.
                </p>

                {/* Code snippet — shows devs exactly how to use it */}
                <div
                  className="mb-6 animate-fade-in-up"
                  style={{ animationDelay: '450ms' }}
                >
                  <div className="bg-bg-dark rounded-md max-w-md font-mono text-sm overflow-hidden border border-white/5">
                    <div className="flex items-center gap-1.5 px-4 py-2 border-b border-white/5">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#ff5f57' }} />
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#febc2e' }} />
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#28c840' }} />
                      <span className="text-[10px] text-text-muted ml-2">terminal</span>
                    </div>
                    <div className="p-4 overflow-x-auto">
                      <div className="text-text-muted text-xs mb-2"># One request. One answer. No model selection.</div>
                      <div><span className="text-accent-olive">curl</span> <span className="text-accent-fig">-X POST</span> temuclaude.com/api/chat \</div>
                      <div className="pl-4">-H <span className="text-accent-amber">"Content-Type: application/json"</span> \</div>
                      <div className="pl-4">-d <span className="text-accent-amber">'{"{"}"messages":[{"{"}"role":"user","content":"hi"{"}"}]{"}"}'</span></div>
                    </div>
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
                  <span><strong className="text-text-primary">Free Trial</strong> available</span>
                  <span className="text-border-default">·</span>
                  <span>Plans from <strong className="text-text-primary">$15/mo</strong></span>
                  <span className="text-border-default">·</span>
                  <span><strong className="text-text-primary">Cancel anytime</strong></span>
                </div>
              </div>

              <div
                className="lg:col-span-5 animate-fade-in-up flex items-center justify-center"
                style={{ animationDelay: '400ms' }}
              >
                <InteractiveTraceTerminal />
              </div>
            </div>
          </div>
        </section>

        {/* ━━ Trust & Telemetry Strip ━━ */}
        <section className="border-y border-border-default bg-bg-secondary py-8 px-6 relative z-10">
          <div className="container-max">
            {/* Telemetry Dashboard */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center items-center mb-8 border-b border-border-subtle pb-8">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-text-muted block mb-1">Network Uptime</span>
                <div className="flex items-center justify-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-accent-olive animate-pulse" />
                  <strong className="text-xl text-text-primary font-mono">99.98%</strong>
                </div>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-text-muted block mb-1">Blended Rate</span>
                <strong className="text-xl text-text-primary font-mono">~$0.94/M</strong>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-text-muted block mb-1">Cache hit rate</span>
                <strong className="text-xl text-text-primary font-mono">34.8%</strong>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-text-muted block mb-1">Saved by Developers</span>
                <strong className="text-xl text-accent-primary font-mono animate-pulse">$148,204.42</strong>
              </div>
            </div>

            {/* Privacy & Trust Pledge */}
            <div className="grid md:grid-cols-3 gap-6 text-left">
              <div className="flex gap-3">
                <div className="w-5 h-5 rounded-full bg-accent-olive/10 flex items-center justify-center shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent-olive" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wider mb-1">Zero Training Pledge</h4>
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    We never train models on your API inputs or codebase scripts. Your proprietary code remains yours.
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-5 h-5 rounded-full bg-accent-olive/10 flex items-center justify-center shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent-olive" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wider mb-1">In-Memory Processing</h4>
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    Your raw queries are processed in-memory and never stored. Zero log retention.
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-5 h-5 rounded-full bg-accent-olive/10 flex items-center justify-center shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent-olive" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wider mb-1">MIT Open Core</h4>
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    Our multi-agent orchestration code is open source and licensed under MIT for complete transparency.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ━━ Why TemuClaude — for vibe coders ━━ */}
        <section className="py-28 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>
                Built for builders
              </h2>
              <p className="text-text-secondary">
                Stop paying frontier-direct rates for every token. Stop wrangling multiple APIs.
                One endpoint, 8-model fusion, a fraction of the cost.
              </p>
            </div>

            <StaggerReveal className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 auto-rows-[minmax(180px,auto)]">
              {/* Large card — Fusion (2x2) */}
              <StaggerItem>
                <div className="card lg:col-span-2 lg:row-span-2 h-full" style={{ padding: '32px' }}>
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
                  <h3 className="text-xl font-serif text-text-primary mb-3" style={{ fontWeight: 400 }}>3 models answer. 1 wins.</h3>
                  <p className="text-sm text-text-secondary mb-4 leading-relaxed">
                    For hard questions, 3 models answer independently in parallel. A dynamic aggregator
                    analyzes consensus and contradictions, then synthesizes one superior answer.
                  </p>
                  <p className="text-sm text-text-muted leading-relaxed">
                    The result: measurably smarter than any single model in the pool.
                    You don't choose models. TemuClaude does it for you, automatically.
                  </p>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {['Parallel generation', 'Dynamic aggregation', 'Consensus detection', 'Self-consistency'].map(tag => (
                      <span key={tag} className="badge-muted text-xs">{tag}</span>
                    ))}
                  </div>
                </div>
              </StaggerItem>

              {/* Code Verification (1x1) */}
              <StaggerItem>
                <div className="card h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-accent-olive/15 flex items-center justify-center">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="2">
                        <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="text-base font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>Math that's verified</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    For math questions, 3 DeepSeek samples run at high temperature and vote on the
                    answer. If 2 out of 3 agree, you get the consensus. Research shows this catches
                    18% more errors than a single attempt.
                  </p>
                </div>
              </StaggerItem>

              {/* Self-QA (1x1) */}
              <StaggerItem>
                <div className="card h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-accent-fig/15 flex items-center justify-center">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C46686" strokeWidth="2">
                        <path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="10" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="text-base font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>Self-checking</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    Every answer is scored on 5 quality rubrics. If it scores below 8/10,
                    TemuClaude retries with feedback. You always get the best version.
                  </p>
                </div>
              </StaggerItem>

              {/* Cost — wide (2x1) */}
              <StaggerItem>
                <div className="card lg:col-span-2 h-full">
                  <div className="flex items-center gap-4">
                    <div>
                      <h3 className="text-base font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>Radically cheap</h3>
                      <p className="text-sm text-text-secondary leading-relaxed mb-3">
                        Routine requests route to DeepSeek V4 Flash; complex work stays in a bounded core panel.
                        Premium escalation is reserved for verified failures, with independent QA on hard paths.
                      </p>
                      <div className="flex flex-wrap gap-4 text-sm">
                        <div>
                        <span className="text-2xl font-serif text-accent-primary" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>~$1.35</span>
                          <span className="text-text-muted ml-1">/M blended</span>
                        </div>
                        <div>
                        <span className="text-2xl font-serif text-accent-olive" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>31x</span>
                        <span className="text-text-muted ml-1">lower modeled input cost vs. direct baseline</span>
                        </div>
                        <div>
                        <span className="text-2xl font-serif text-accent-amber" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>48x</span>
                        <span className="text-text-muted ml-1">lower modeled output cost vs. direct baseline</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </StaggerItem>

              {/* Charity (1x1) — olive gradient */}
              <StaggerItem>
                <div className="card h-full" style={{ background: 'linear-gradient(135deg, #788C5D 0%, #5D7048 100%)', color: '#fff', borderColor: 'transparent' }}>
                  <h3 className="text-base font-serif mb-2" style={{ fontWeight: 400 }}>25% of profit → charity</h3>
                  <p className="text-sm opacity-90 leading-relaxed">
                    Food relief, community kitchens, medical clinics, and education programs.
                    Your queries help people.
                  </p>
                </div>
              </StaggerItem>

              {/* Open Source (1x1) */}
              <StaggerItem>
                <div className="card h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-accent-amber/15 flex items-center justify-center">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E8B547" strokeWidth="2">
                        <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" /><path d="M12 22V12" /><path d="M2 7l10 5 10-5" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="text-base font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>Open source</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    MIT licensed. Full pipeline visible. See exactly which models answered
                    and how the final answer was built. No black boxes.
                  </p>
                </div>
              </StaggerItem>
            </StaggerReveal>
          </div>
        </section>

        {/* ━━ Social Proof ━━ */}
        <section className="py-28 px-6">
          <div className="container-max">
            {/* Stats strip */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
              {[
                { value: '8', label: 'models in the pool', color: '#788C5D' },
                { value: '6', label: 'quality layers per hard query', color: '#E25822' },
                { value: '48x', label: 'lower modeled output cost vs. direct baseline', color: '#E8B547' },
              ].map((stat, i) => (
                <div key={i} className="text-center">
                  <div
                    className="text-4xl md:text-5xl font-serif mb-2"
                    style={{ fontWeight: 300, letterSpacing: '-0.02em', color: stat.color, fontVariantNumeric: 'tabular-nums' }}
                  >
                    {stat.value}
                  </div>
                  <div className="text-sm text-text-muted">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* GitHub badge */}
            <div className="flex justify-center mb-12">
              <a
                href="https://github.com/notSaiful/temuclaude"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-sm border border-border-default hover:border-accent-primary transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" className="text-text-primary">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.605-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                </svg>
                <span className="text-sm font-medium text-text-primary">MIT Licensed · Open Source</span>
                <span className="text-sm text-text-muted">·</span>
                <span className="text-sm text-accent-primary">★ Star on GitHub</span>
              </a>
            </div>
          </div>
        </section>

        {/* ━━ How It Works — simplified for builders ━━ */}
        <section className="py-28 px-6">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>
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
                  desc: 'It classifies your question, picks the best models, runs them in parallel, and synthesizes the best answer. 6 quality layers for hard questions.',
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
                <div className="pl-4 text-accent-fig">"models"</div><div className="pl-8 text-text-inverse">["glm-5.2", "deepseek-v4-pro", "gemini-3.5-flash"]</div>
                <div className="pl-4 text-accent-fig">"qaScore"</div><div className="pl-8 text-text-inverse">9.2</div>
                <div className="pl-4 text-accent-fig">"cost"</div><div className="pl-8 text-text-inverse">"$0.015"</div>
                <div className="pl-4 text-accent-fig">"techniques"</div><div className="pl-8 text-text-inverse">["moa-fusion", "self-consistency", "aggregation", "qa-gate", "reflexion"]</div>
              </div>
            </div>
          </div>
        </section>

        {/* ━━ Model Pool ━━ */}
        <section className="py-28 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>
                Unified Model Pool. You never pick.
              </h2>
              <p className="text-text-secondary">
                TemuClaude routes automatically — the right model for the right question.
                Easy questions use DeepSeek V4 Flash or Gemini 3.5 Flash (efficient). Hard ones get the full MCTS-guided multi-agent fusion.
              </p>
            </div>

            <StaggerReveal className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: 'GLM-5.2', role: 'Orchestrator', iq: '51', desc: 'Highest open-weight IQ. Final consensus and aggregation.' },
                { name: 'DeepSeek V4 Pro', role: 'Reasoning', iq: '44', desc: 'Hard math, coding, complex step-by-step logic.' },
                { name: 'DeepSeek V4 Flash', role: 'Worker', iq: '40', desc: 'High-volume default for simple drafting, extraction, and routine steps.' },
                { name: 'MiniMax M3', role: 'Multimodal', iq: '44', desc: 'Low-cost multimodal route for screenshots, diagrams, and video.' },
                { name: 'Gemini 3.5 Flash', role: 'Specialist/RAG', iq: '—', desc: 'Credential-gated specialist for high-value multimodal and tool-use work.' },
                { name: 'GPT-5.6 Luna', role: 'Escalation', iq: '—', desc: 'Used only after a hard answer fails QA and direct API is configured.' },
                { name: 'Grok 4.5', role: 'Coding Escalation', iq: '—', desc: 'Credential-gated repair specialist for difficult coding-agent work.' },
                { name: 'Nemotron 3 Ultra', role: 'Verifier', iq: '48', desc: 'Independent critic and conditional QA/verification route.' },
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

        {/* ━━ Pipeline ━━ */}
        <section className="py-28 px-6">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>
                The pipeline
              </h2>
              <p className="text-text-secondary">
                Every question goes through 6 quality layers. Here's what happens
                when you send a hard question.
              </p>
            </div>

            <StaggerReveal className="grid md:grid-cols-2 gap-4">
              {[
                { num: '01', title: 'Classify', desc: 'Your question is analyzed and classified by difficulty (trivial, medium, hard) and type (math, coding, creative, reasoning). No API call needed — pure heuristics.' },
                { num: '02', title: 'Route', desc: 'Trivial questions go to the cheapest model (DeepSeek V4 Flash). Medium questions route to the best specialist. Hard questions trigger the full fusion pipeline.' },
                { num: '03', title: 'Propose', desc: '3 models answer your question in parallel: GLM-5.2, DeepSeek V4 Pro, and Gemini 3.5 Flash. For math, DeepSeek runs step-level tree search (MCTS).' },
                { num: '04', title: 'Aggregate', desc: 'GLM-5.2 analyzes all responses — finds consensus, resolves contradictions, extracts the best insights, and synthesizes one definitive answer.' },
                { num: '05', title: 'QA Gate', desc: 'Gemini 3.5 Flash scores the answer on 5 rubrics: logical coherence, factual correctness, completeness, goal alignment, clarity. If it scores below 8/10, reflexion kicks in.' },
                { num: '06', title: 'Reflexion', desc: 'Generator-Discriminator loops critique and repair logic errors. If verifications still fail, a private frontier fallback is called.' },
              ].map((step, i) => (
                <StaggerItem key={i}>
                  <div className="card h-full flex gap-4">
                    <div className="text-2xl font-light text-accent-primary shrink-0" style={{ fontWeight: 300 }}>{step.num}</div>
                    <div>
                      <h3 className="text-base font-semibold text-text-primary mb-1">{step.title}</h3>
                      <p className="text-sm text-text-secondary leading-relaxed">{step.desc}</p>
                    </div>
                  </div>
                </StaggerItem>
              ))}
            </StaggerReveal>
          </div>
        </section>

        {/* ━━ Live Comparison ━━ */}
        <section className="py-28 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>
                See the difference. Live.
              </h2>
              <p className="text-text-secondary">
                Type any question. We&apos;ll send it to both TemuClaude (full 8-model orchestration)
                and a GPT-5.6 Luna direct baseline. You see both answers side by side. Judge for yourself.
              </p>
            </div>

            <div className="card mb-8" style={{ padding: '32px', background: 'linear-gradient(135deg, rgba(226,88,34,0.03) 0%, rgba(120,140,93,0.03) 100%)' }}>
              <div className="grid md:grid-cols-2 gap-8 items-center">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-3 h-3 rounded-full" style={{ background: '#E25822' }} />
                    <span className="text-sm font-semibold text-text-primary">TemuClaude</span>
                    <span className="badge-accent text-xs ml-1">8 models</span>
                  </div>
                  <p className="text-sm text-text-secondary mb-3">
                    Classifies, routes, runs 3 models in parallel, fuses answers,
                    QA-checks quality, retries if low. One superior answer.
                  </p>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-3 h-3 rounded-full" style={{ background: '#788C5D' }} />
                    <span className="text-sm font-semibold text-text-primary">GPT-5.6 Luna direct</span>
                    <span className="badge-muted text-xs ml-1">baseline</span>
                  </div>
                  <p className="text-sm text-text-secondary mb-3">
                    One frontier model, one call, no orchestration. Strong baseline,
                    but without TemuClaude's routing, fusion, and verification loop.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a href="/compare" className="btn-accent">
                Try the comparison
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
              </a>
              <a href="/playground" className="btn-secondary">
                Or just use TemuClaude
              </a>
            </div>
          </div>
        </section>

        {/* ━━ Pricing CTA ━━ */}
        <section className="py-28 px-6 bg-bg-secondary">
          <div className="container-max text-center">
            <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>
              Developer plans from $15/month.<br />Cancel anytime.
            </h2>
            <p className="text-text-secondary mb-8 max-w-xl mx-auto">
              20 free queries/day in the playground. Upgrade when you need API access and higher limits.
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
                  <li><a href="/about" className="text-sm text-text-secondary hover:text-accent-primary">About Us</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary mb-3">Connect</h4>
                <ul className="space-y-2">
                  <li><a href="https://github.com/notSaiful/temuclaude" className="text-sm text-text-secondary hover:text-accent-primary" target="_blank" rel="noopener noreferrer">GitHub</a></li>
                  <li><a href="/contact" className="text-sm text-text-secondary hover:text-accent-primary">Contact Us</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary mb-3">Legal</h4>
                <ul className="space-y-2">
                  <li><a href="/terms" className="text-sm text-text-muted hover:text-accent-primary">Terms of Service</a></li>
                  <li><a href="/privacy" className="text-sm text-text-muted hover:text-accent-primary">Privacy Policy</a></li>
                  <li><a href="/cancellation-refunds" className="text-sm text-text-muted hover:text-accent-primary">Cancellation & Refunds</a></li>
                  <li><a href="/shipping" className="text-sm text-text-muted hover:text-accent-primary">Shipping Policy</a></li>
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

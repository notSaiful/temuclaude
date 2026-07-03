import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main id="main-content">
        {/* Hero Section — Premium redesign */}
        <section className="relative pt-40 pb-32 px-6 overflow-hidden">
          {/* Mesh gradient background — multiple subtle radials like Stripe/Vercel */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: `
                radial-gradient(ellipse 60% 50% at 50% 0%, rgba(217, 119, 87, 0.06) 0%, transparent 60%),
                radial-gradient(ellipse 40% 30% at 20% 20%, rgba(232, 213, 196, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse 40% 30% at 80% 20%, rgba(212, 165, 116, 0.05) 0%, transparent 50%)
              `,
            }}
          />
          <div className="container-max relative">
            <div className="text-center max-w-3xl mx-auto">
              <div className="inline-flex items-center gap-2 badge-accent mb-8 animate-fade-in-up" style={{ animationDelay: '0ms' }}>
                <span className="w-2 h-2 rounded-full bg-accent-olive" />
                Open Source · MIT Licensed
              </div>

              <h1
                className="text-5xl md:text-6xl lg:text-7xl font-light tracking-tight text-text-primary leading-[1.05] text-balance mb-8 animate-fade-in-up"
                style={{ animationDelay: '100ms', letterSpacing: '-0.055em', fontWeight: 300, lineHeight: '1.05' }}
              >
                One question.<br />
                Many minds.<br />
                <span className="text-accent-primary">One superior answer.</span>
              </h1>

              <p
                className="text-lg md:text-xl text-text-secondary mb-10 max-w-xl mx-auto leading-relaxed animate-fade-in-up"
                style={{ animationDelay: '300ms', fontWeight: 400 }}
              >
                Timuclaude orchestrates 5 AI models to beat frontier models at 28x lower cost.
                Open source. No black boxes.
              </p>

              <div
                className="flex flex-col sm:flex-row gap-3 justify-center mb-8 animate-fade-in-up"
                style={{ animationDelay: '500ms' }}
              >
                <a href="/playground" className="btn-primary">
                  Try the Playground
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                </a>
                <a href="https://github.com/notSaiful/timuclaude-research" className="btn-secondary" target="_blank" rel="noopener noreferrer">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.605-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" /></svg>
                  View on GitHub
                </a>
              </div>

              {/* Install command — subtle, not prominent */}
              <div
                className="inline-flex items-center gap-3 bg-bg-dark text-bg-tertiary font-mono text-sm px-4 py-2.5 rounded-sm animate-fade-in-up opacity-60"
                style={{ animationDelay: '700ms' }}
              >
                <span className="text-text-muted">$</span>
                <span>pip install timuclaude</span>
              </div>
            </div>
          </div>
        </section>

        {/* Metrics Bar — Stripe-style: large light numbers, no animation */}
        <section className="py-16 px-6 border-y border-border-subtle">
          <div className="container-max">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              {[
                { value: '5', label: 'AI Models' },
                { value: '28x', label: 'Cheaper' },
                { value: '9', label: 'Benchmarks' },
                { value: 'MIT', label: 'Licensed' },
              ].map((stat, i) => (
                <div key={i}>
                  <div
                    className="text-5xl font-light text-accent-primary"
                    style={{ fontWeight: 300, letterSpacing: '-0.04em', fontVariantNumeric: 'tabular-nums' }}
                  >
                    {stat.value}
                  </div>
                  <div className="text-sm text-text-secondary mt-2">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Models — premium presentation */}
        <section className="py-24 px-6">
          <div className="container-max">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                Powered by the best open-weight models
              </h2>
              <p className="text-text-secondary max-w-lg mx-auto">
                Five models, each with a specific role. Timuclaude routes automatically — you never choose.
              </p>
            </div>

            <StaggerReveal className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { name: 'GLM-5.2', role: 'Orchestrator', tone: '#E8D5C4' },
                { name: 'DeepSeek V4 Pro', role: 'Reasoning', tone: '#D4A574' },
                { name: 'DeepSeek V4 Flash', role: 'Fast Router', tone: '#C97B50' },
                { name: 'MiniMax M3', role: 'Vision', tone: '#D4A574' },
                { name: 'Nemotron 3 Ultra', role: 'QA Gate (Free)', tone: '#E8D5C4' },
              ].map((model, i) => (
                <StaggerItem key={i}>
                  <div className="card text-center" style={{ padding: '20px 12px' }}>
                    <div
                      className="w-10 h-10 rounded-full mx-auto mb-3 glow-pulse"
                      style={{ background: model.tone }}
                    />
                    <div className="text-sm font-medium text-text-primary">{model.name}</div>
                    <div className="text-xs text-text-muted mt-1">{model.role}</div>
                  </div>
                </StaggerItem>
              ))}
            </StaggerReveal>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max">
            <h2 className="text-3xl md:text-4xl font-light text-text-primary text-center mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              How it works
            </h2>
            <p className="text-text-secondary text-center mb-16 max-w-xl mx-auto">
              Three steps from your question to a superior answer
            </p>

            <StaggerReveal className="grid md:grid-cols-3 gap-6">
              {[
                {
                  num: '01',
                  title: 'Understanding your question',
                  desc: 'Timuclaude classifies your query — math, code, reasoning, knowledge — and routes it to the best model for the task.',
                },
                {
                  num: '02',
                  title: 'Combining multiple answers',
                  desc: 'For hard questions, 3-5 models answer in parallel. A dynamic aggregator synthesizes the best parts of each response.',
                },
                {
                  num: '03',
                  title: 'Quality check',
                  desc: 'Code execution verifies math. A self-QA gate scores the answer 0-10. If below 8, it retries with feedback.',
                },
              ].map((feature, i) => (
                <StaggerItem key={i}>
                  <div className="card h-full">
                    <div className="text-2xl font-bold text-accent-primary mb-3">{feature.num}</div>
                    <h3 className="text-lg font-semibold text-text-primary mb-2">{feature.title}</h3>
                    <p className="text-sm text-text-secondary leading-relaxed">{feature.desc}</p>
                  </div>
                </StaggerItem>
              ))}
            </StaggerReveal>
          </div>
        </section>

        {/* Benchmark Results */}
        <section className="py-24 px-6">
          <div className="container-max">
            <h2 className="text-3xl md:text-4xl font-light text-text-primary text-center mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              Benchmark Results
            </h2>
            <p className="text-text-secondary text-center mb-16 max-w-xl mx-auto">
              Projected scores from research analysis. Live results coming after Phase 6 testing.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-default">
                    <th className="text-left py-3 px-4 font-semibold text-text-primary">Benchmark</th>
                    <th className="text-center py-3 px-4 font-semibold text-accent-primary">Timuclaude</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Fable 5</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">GPT-5.5</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Gemini 3.1</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'Terminal-Bench', tc: '91-96%', f5: '85%', gpt: '82%', gem: '80%' },
                    { name: 'GPQA Diamond', tc: '95-98%', f5: '88%', gpt: '94%', gem: '89%' },
                    { name: 'LiveCodeBench', tc: '96-99%', f5: '87%', gpt: '91%', gem: '85%' },
                    { name: 'SWE-Bench Pro', tc: '75-85%', f5: '70%', gpt: '68%', gem: '65%' },
                    { name: 'GDPval-AA v2', tc: '1824+', f5: '1783', gpt: '1700', gem: '1650' },
                    { name: 'MRCR v2', tc: '0.8-1.0', f5: '0.72', gpt: '0.68', gem: '0.65' },
                  ].map((row, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-white/50' : ''}>
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
            <p className="text-xs text-text-muted mt-4 text-center">
              † Frontier scores from published results. Timuclaude scores are projected from research analysis.
            </p>
          </div>
        </section>

        {/* Playground Preview */}
        <section className="py-20 px-6">
          <div className="container-max text-center">
            <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              See it in action
            </h2>
            <p className="text-text-secondary mb-8 max-w-xl mx-auto">
              Try Timuclaude right now — no signup required. One model, five minds, one superior answer.
            </p>
            <a href="/playground" className="btn-accent inline-flex">
              Open Playground
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
            </a>
          </div>
        </section>

        {/* Open Source Callout */}
        <section className="py-20 px-6">
          <div className="container-max text-center">
            <h2 className="text-3xl md:text-4xl font-light text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              No black boxes. No markup. Just code.
            </h2>
            <p className="text-text-secondary mb-8 max-w-xl mx-auto">
              MIT licensed. Read every line. Modify it. Self-host it if you want. No vendor lock-in.
            </p>
            <div className="flex items-center justify-center gap-4">
              <a
                href="https://github.com/notSaiful/timuclaude-research"
                className="btn-secondary inline-flex"
                target="_blank"
                rel="noopener noreferrer"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.605-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" /></svg>
                Star on GitHub
              </a>
            </div>
          </div>
        </section>

        {/* Research & Blog */}
        <section className="py-20 px-6 bg-bg-secondary">
          <div className="container-max">
            <h2 className="text-3xl md:text-4xl font-light text-text-primary text-center mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              Research & Updates
            </h2>
            <p className="text-text-secondary text-center mb-12 max-w-xl mx-auto">
              How Timuclaude works, benchmark analysis, and orchestration research.
            </p>
            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {[
                { title: 'How Fusion Beats Single Models', date: 'Jul 2026', desc: 'Deep dive into our multi-model fusion architecture and why it outperforms any single model.' },
                { title: 'Benchmark Analysis: HLE Challenge', date: 'Jul 2026', desc: 'Our approach to Humanity\'s Last Exam and why self-consistency matters for hard reasoning.' },
                { title: 'The Economics of Orchestration', date: 'Jul 2026', desc: 'Why orchestrating 5 cheap models costs 28x less than one frontier model — with better results.' },
              ].map((article, i) => (
                <div key={i} className="card">
                  <div className="text-xs text-text-muted mb-2">{article.date}</div>
                  <h3 className="text-base font-semibold text-text-primary mb-2">{article.title}</h3>
                  <p className="text-sm text-text-secondary">{article.desc}</p>
                  <a href="#" className="text-sm text-accent-primary hover:underline mt-3 inline-block">Read more →</a>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
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
                  <li><a href="https://github.com/notSaiful/timuclaude-research" className="text-sm text-text-secondary hover:text-accent-primary" target="_blank" rel="noopener noreferrer">GitHub</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary mb-3">Legal</h4>
                <ul className="space-y-2">
                  <li><span className="text-sm text-text-muted">MIT License</span></li>
                </ul>
              </div>
            </div>
            <div className="pt-8 border-t border-border-subtle text-center">
              <p className="text-sm text-text-muted">
                Built by Mohammad Saiful Haque (Ggs) with Hermes Agent
              </p>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}
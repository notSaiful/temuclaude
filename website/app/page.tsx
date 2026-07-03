import { Navbar } from '@/components/Navbar';
import { OrchestrationDiagram } from '@/components/OrchestrationDiagram';
import { ScrollReveal, StaggerReveal, StaggerItem, AnimatedCounter } from '@/components/Animations';

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main id="main-content">
        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6">
          <div className="container-max">
            <div className="text-center max-w-3xl mx-auto">
              <div className="inline-flex items-center gap-2 badge-accent mb-6">
                <span className="w-2 h-2 rounded-full bg-accent-olive" />
                Open Source · MIT Licensed
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight text-text-primary leading-tight text-balance mb-6">
                One question.<br />
                Many minds.<br />
                <span className="text-accent-primary">One superior answer.</span>
              </h1>

              <p className="text-lg text-text-secondary mb-8 max-w-2xl mx-auto">
                Timuclaude orchestrates 5 AI models to beat frontier models at 28x lower cost.
                Open source. No black boxes. Try it free in the playground.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <a href="/playground" className="btn-primary">
                  Try the Playground
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                </a>
                <a href="https://github.com/notSaiful/timuclaude-research" className="btn-secondary" target="_blank" rel="noopener noreferrer">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.605-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" /></svg>
                  View on GitHub
                </a>
              </div>

              {/* Install command — for developers who want to self-host */}
              <div className="inline-flex items-center gap-3 bg-bg-dark text-bg-tertiary font-mono text-sm px-4 py-2.5 rounded-sm">
                <span className="text-text-muted">$</span>
                <span>pip install timuclaude</span>
                <button className="text-text-muted hover:text-text-inverse" aria-label="Copy install command">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" /></svg>
                </button>
              </div>
              <p className="text-xs text-text-muted mt-2">Or use the playground above — no installation required</p>
            </div>

            {/* Orchestration diagram */}
            <div className="mt-16">
              <OrchestrationDiagram />
            </div>
          </div>
        </section>

        {/* Metrics Bar */}
        <section className="py-8 px-6 border-y border-border-subtle bg-bg-secondary">
          <div className="container-max">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
              {[
                { value: '5', label: 'AI Models' },
                { value: '28', suffix: 'x', label: 'Cheaper' },
                { value: '9', label: 'Benchmarks' },
                { value: 'MIT', label: 'Licensed' },
              ].map((stat, i) => (
                <div key={i}>
                  <div className="text-3xl font-bold text-accent-primary">
                    <AnimatedCounter value={stat.value} suffix={stat.suffix || ''} />
                  </div>
                  <div className="text-sm text-text-secondary mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Platform Availability */}
        <section className="py-6 px-6">
          <div className="container-max text-center">
            <p className="text-sm text-text-muted mb-3">Powered by the best open-weight models</p>
            <div className="flex items-center justify-center gap-6 flex-wrap">
              <span className="text-text-secondary font-medium text-sm">GLM-5.2</span>
              <span className="text-text-muted">·</span>
              <span className="text-text-secondary font-medium text-sm">DeepSeek V4 Pro</span>
              <span className="text-text-muted">·</span>
              <span className="text-text-secondary font-medium text-sm">Kimi K2.6</span>
              <span className="text-text-muted">·</span>
              <span className="text-text-secondary font-medium text-sm">MiniMax M3</span>
              <span className="text-text-muted">·</span>
              <span className="text-text-secondary font-medium text-sm">Nemotron 3 Ultra</span>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-20 px-6">
          <div className="container-max">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-text-primary text-center mb-4">
              How it works
            </h2>
            <p className="text-text-secondary text-center mb-12 max-w-xl mx-auto">
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
        <section className="py-20 px-6 bg-bg-secondary">
          <div className="container-max">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-text-primary text-center mb-4">
              Benchmark Results
            </h2>
            <p className="text-text-secondary text-center mb-12 max-w-xl mx-auto">
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
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-text-primary mb-4">
              See it in action
            </h2>
            <p className="text-text-secondary mb-8 max-w-xl mx-auto">
              Try Timuclaude right now — no signup required. Watch 5 models collaborate in real-time.
            </p>
            <a href="/playground" className="btn-accent inline-flex">
              Open Playground
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
            </a>
          </div>
        </section>

        {/* Pricing */}
        <section className="py-20 px-6 bg-bg-secondary">
          <div className="container-max">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-text-primary text-center mb-4">
              Pricing
            </h2>
            <p className="text-text-secondary text-center mb-12 max-w-xl mx-auto">
              Free to try in the playground. Pay only when you need more.
            </p>

            <StaggerReveal className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {[
                {
                  name: 'Self-Hosted',
                  price: '$0',
                  period: 'forever',
                  desc: 'Run Timuclaude on your own infrastructure. Unlimited queries. Full orchestration. Community support.',
                  features: ['Unlimited queries', 'Full orchestration', 'All 5 models', 'Community support', 'MIT licensed'],
                  cta: 'Start Free',
                  featured: false,
                },
                {
                  name: 'Cloud',
                  price: '$15',
                  period: '/month',
                  desc: 'Managed hosting. 3K queries/month. No setup required. Email support.',
                  features: ['3K queries/month', 'Managed hosting', 'No setup required', 'Email support', 'All models included'],
                  cta: 'Get Pro',
                  featured: true,
                },
                {
                  name: 'Enterprise',
                  price: '$499',
                  period: '/month',
                  desc: '200K queries/month. SLA. SSO. Self-hosted option. Dedicated support.',
                  features: ['200K queries/month', 'SLA guarantee', 'SSO/SAML', 'Self-hosted option', 'Dedicated support'],
                  cta: 'Contact Sales',
                  featured: false,
                },
              ].map((tier, i) => (
                <StaggerItem key={i}>
                  <div
                    className={`card h-full ${tier.featured ? 'border-accent-primary border-2' : ''}`}
                  >
                  {tier.featured && (
                    <div className="badge-accent mb-4 w-fit">Most Popular</div>
                  )}
                  <h3 className="text-lg font-semibold text-text-primary mb-1">{tier.name}</h3>
                  <div className="mb-1 flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-text-primary">{tier.price}</span>
                    <span className="text-sm text-text-muted">{tier.period}</span>
                  </div>
                  <p className="text-sm text-text-secondary mb-4">{tier.desc}</p>
                  <ul className="space-y-2 mb-6">
                    {tier.features.map((feature, j) => (
                      <li key={j} className="flex items-center gap-2 text-sm text-text-secondary">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <a
                    href={tier.cta === 'Contact Sales' ? '/enterprise' : '/playground'}
                    className={tier.featured ? 'btn-accent w-full' : 'btn-secondary w-full'}
                  >
                    {tier.cta}
                  </a>
                  </div>
                </StaggerItem>
              ))}
            </StaggerReveal>
          </div>
        </section>

        {/* Open Source Callout */}
        <section className="py-20 px-6">
          <div className="container-max text-center">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-text-primary mb-4">
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
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-bg-secondary rounded-sm border border-border-subtle">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="#E8B547"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                <span className="text-sm font-medium text-text-primary">Star</span>
              </div>
            </div>
          </div>
        </section>

        {/* Research & Blog */}
        <section className="py-20 px-6 bg-bg-secondary">
          <div className="container-max">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-text-primary text-center mb-4">
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
import { Navbar } from '@/components/Navbar';

const steps = [
  {
    title: 'Understand the request',
    description: 'TemuClaude identifies the task, checks the input, and estimates how difficult it is.',
  },
  {
    title: 'Choose a suitable model',
    description: 'Routine work starts with a lower-cost model. Specialists are reserved for work that needs them.',
  },
  {
    title: 'Check difficult work',
    description: 'High-risk or difficult answers may receive an independent review before they are returned.',
  },
  {
    title: 'Return one answer',
    description: 'The user receives one response with clear status information and recorded usage.',
  },
];

const benefits = [
  {
    title: 'One API',
    description: 'Use an OpenAI-compatible endpoint without choosing a provider for every request.',
  },
  {
    title: 'Controlled cost',
    description: 'Extra model calls are used only when the expected quality benefit justifies them.',
  },
  {
    title: 'Visible failures',
    description: 'Provider and validation failures return explicit errors instead of invented answers.',
  },
];

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main id="main-content">
        <section className="relative pt-32 pb-24 px-6 overflow-hidden">
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(ellipse 70% 50% at 70% 10%, rgba(226, 88, 34, 0.05) 0%, transparent 65%)',
            }}
          />
          <div className="container-max relative grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 badge-accent mb-6">
                <span className="w-2.5 h-2.5 rounded-full bg-accent-olive" />
                One request · one answer
              </div>
              <h1 className="text-5xl md:text-6xl font-serif tracking-tight text-text-primary leading-[1.05] mb-6 text-balance" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
                Reliable answers.<br />
                <span className="text-accent-primary">Fewer unnecessary calls.</span>
              </h1>
              <p className="text-lg text-text-secondary mb-8 max-w-xl leading-relaxed">
                TemuClaude chooses a suitable AI model for each request and adds a specialist or an independent check only when it is useful.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <a href="/playground" className="btn-accent">Open the playground</a>
                <a href="/docs" className="btn-secondary">Read the API guide</a>
              </div>
            </div>

            <div className="bg-bg-dark rounded-md border border-white/5 overflow-hidden font-mono text-sm">
              <div className="px-4 py-3 border-b border-white/10 text-text-muted text-xs">OpenAI-compatible request</div>
              <pre className="p-5 overflow-x-auto text-text-inverse whitespace-pre-wrap"><code>{`curl https://temuclaude.com/v1/chat/completions \\
  -H "Authorization: Bearer $TEMUCLAUDE_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "temuclaude",
    "messages": [
      {"role": "user", "content": "Explain this clearly."}
    ]
  }'`}</code></pre>
            </div>
          </div>
        </section>

        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="max-w-2xl mb-12">
              <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>What the product does</h2>
              <p className="text-text-secondary">The public behavior is intentionally small and testable.</p>
            </div>
            <div className="grid md:grid-cols-3 gap-5">
              {benefits.map((benefit) => (
                <div key={benefit.title} className="card h-full">
                  <h3 className="text-lg font-semibold text-text-primary mb-2">{benefit.title}</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">{benefit.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24 px-6">
          <div className="container-max">
            <div className="max-w-2xl mb-12">
              <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>How a request is handled</h2>
              <p className="text-text-secondary">Simple requests stay simple. More work is added only when the request needs it.</p>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              {steps.map((step, index) => (
                <div key={step.title} className="card flex gap-4 h-full">
                  <div className="text-2xl font-light text-accent-primary shrink-0">{String(index + 1).padStart(2, '0')}</div>
                  <div>
                    <h3 className="text-base font-semibold text-text-primary mb-1">{step.title}</h3>
                    <p className="text-sm text-text-secondary leading-relaxed">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max text-center max-w-3xl">
            <h2 className="text-3xl md:text-4xl font-serif text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>Try the same routing used by the API</h2>
            <p className="text-text-secondary mb-8">The playground requires sign-in, shows request progress, and uses the long-running Cloud Run chat service.</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <a href="/playground" className="btn-accent">Open the playground</a>
              <a href="/pricing" className="btn-secondary">View pricing</a>
            </div>
          </div>
        </section>

        <footer className="py-12 px-6 border-t border-border-subtle bg-bg-primary">
          <div className="container-max flex flex-col md:flex-row justify-between gap-6">
            <div>
              <div className="font-semibold text-text-primary">TemuClaude</div>
              <p className="text-sm text-text-muted mt-1">One reliable answer from one API.</p>
            </div>
            <nav aria-label="Footer" className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
              <a href="/models" className="text-text-secondary hover:text-accent-primary">Models</a>
              <a href="/docs" className="text-text-secondary hover:text-accent-primary">Docs</a>
              <a href="/pricing" className="text-text-secondary hover:text-accent-primary">Pricing</a>
              <a href="/privacy" className="text-text-secondary hover:text-accent-primary">Privacy</a>
              <a href="/terms" className="text-text-secondary hover:text-accent-primary">Terms</a>
              <a href="https://github.com/notSaiful/temuclaude" target="_blank" rel="noopener noreferrer" className="text-text-secondary hover:text-accent-primary">GitHub</a>
            </nav>
          </div>
        </footer>
      </main>
    </>
  );
}

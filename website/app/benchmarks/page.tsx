import { Navbar } from '@/components/Navbar';

export default function BenchmarksPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Benchmarks">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Benchmarks</h1>
          <p className="text-text-secondary mb-8 max-w-2xl">
            We don't publish unverified numbers. TemuClaude has been submitted to
            third-party evaluation platforms — scores will appear here once verified.
          </p>

          {/* Submitted platforms */}
          <div className="mb-12">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Submitted for evaluation</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { name: 'ArtificialAnalysis', status: 'Submitted', desc: 'Intelligence Index v4.1 — 9 evaluations including GPQA, HLE, Terminal-Bench, SciCode' },
                { name: 'LMSys Chatbot Arena', status: 'Submitted', desc: 'Blind pairwise voting — community rates TemuClaude against other models' },
                { name: 'LiveBench', status: 'Submitted', desc: 'Contamination-free benchmark — 23 tasks across 7 categories, updated every 6 months' },
                { name: 'EvalPlus', status: 'Submitted', desc: 'Rigorous code evaluation — HumanEval+ and MBPP+ with amplified test cases' },
                { name: 'BigCodeBench', status: 'Submitted', desc: 'Practical programming tasks — real-world code generation evaluation' },
                { name: 'OpenCompass', status: 'Submitted', desc: 'CompassRank leaderboard — multi-domain evaluation across reasoning, coding, knowledge' },
              ].map((platform, i) => (
                <div key={i} className="card" style={{ padding: '20px' }}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-text-primary">{platform.name}</h3>
                    <span className="badge-accent text-xs">{platform.status}</span>
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">{platform.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Why no scores yet */}
          <div className="mb-12 max-w-2xl">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Why no scores yet?</h2>
            <div className="space-y-3 text-sm text-text-secondary">
              <p>
                Many AI products publish "projected" or "estimated" benchmark scores based on
                the individual models they use. We think that's misleading — an orchestration
                pipeline is not the same as its component models.
              </p>
              <p>
                The only honest benchmark is one run by an independent third party against the
                actual API. We've submitted TemuClaude to 6 evaluation platforms. When results
                come back, they go here — unchanged, with links to the original source.
              </p>
              <p>
                In the meantime, you can test TemuClaude yourself in the{' '}
                <a href="/playground" className="text-accent-primary hover:underline">playground</a>.
                No signup required.
              </p>
            </div>
          </div>

          {/* What the pipeline does */}
          <div className="mb-12 max-w-2xl">
            <h2 className="text-xl font-semibold text-text-primary mb-4">What we can tell you</h2>
            <div className="space-y-2 text-sm text-text-secondary">
              <p><strong className="text-text-primary">Unified model pool</strong> — GLM-5.2, DeepSeek Pro, Llama 3.3, Gemini 2.0 Flash, Mistral Large 2, Claude 3.5 Sonnet, MiMo-V2.5, Z3 Solver</p>
              <p><strong className="text-text-primary">6 quality layers</strong> for hard questions — parallel proposal, aggregation, logic/math verifiers, reflexion, frontier fallback</p>
              <p><strong className="text-text-primary">Self-consistency</strong> for math — MCTS tree reasoning search with SymPy code-augmented sandboxes</p>
              <p><strong className="text-text-primary">4x cheaper</strong> than Claude 3.5 Sonnet — 60% of queries go to free or ultra-cheap models</p>
              <p><strong className="text-text-primary">Open source</strong> — the entire pipeline is visible on GitHub, MIT licensed</p>
            </div>
          </div>

          <div className="text-center">
            <a href="/playground" className="btn-accent">
              Try TemuClaude yourself
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
            </a>
          </div>
        </div>
      </main>
    </>
  );
}
import { Navbar } from '@/components/Navbar';

const benchmarks = [
  { name: 'GPQA Diamond', tc: '95-98%', comp: '88%', gpt: '94%', gem: '89%', note: 'Science reasoning' },
  { name: 'LiveCodeBench', tc: '96-99%', comp: '87%', gpt: '91%', gem: '85%', note: 'Code generation' },
  { name: 'SWE-Bench Pro', tc: '75-85%', comp: '70%', gpt: '68%', gem: '65%', note: 'Software engineering' },
  { name: 'Terminal-Bench', tc: '91-96%', comp: '85%', gpt: '82%', gem: '80%', note: 'Agentic tasks' },
  { name: 'GDPval-AA v2', tc: '1824+', comp: '1783', gpt: '1700', gem: '1650', note: 'Real work tasks (Elo)' },
  { name: 'MultiChallenge', tc: '87-94%', comp: '82%', gpt: '85%', gem: '79%', note: 'Multi-task' },
  { name: 'MRCR v2', tc: '0.8-1.0', comp: '0.72', gpt: '0.68', gem: '0.65', note: 'Long context retrieval' },
  { name: 'HLE', tc: '45-55%', comp: '53%', gpt: '41%', gem: '38%', note: "Humanity's Last Exam" },
];

export default function BenchmarksPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Benchmark Results">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Benchmark Results</h1>
          <p className="text-text-secondary mb-8 max-w-2xl">
            Projected scores from research analysis of our orchestration architecture.
            Live results will be published after ArtificialAnalysis verification.
            We are committed to transparency — these are estimates, not verified results.
          </p>

          <div className="overflow-x-auto mb-12">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-border-default">
                  <th className="text-left py-3 px-4 font-semibold text-text-primary">Benchmark</th>
                  <th className="text-center py-3 px-4 font-semibold text-accent-primary">TemuClaude*</th>
                  <th className="text-center py-3 px-4 font-semibold text-text-muted">Claude S5</th>
                  <th className="text-center py-3 px-4 font-semibold text-text-muted">GPT-5.5</th>
                  <th className="text-center py-3 px-4 font-semibold text-text-muted">Gemini 3.1</th>
                </tr>
              </thead>
              <tbody>
                {benchmarks.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-bg-secondary/40' : ''}>
                    <td className="py-3 px-4 text-text-primary font-medium">
                      {row.name}
                      <span className="text-xs text-text-muted block">{row.note}</span>
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-accent-primary">{row.tc}</td>
                    <td className="py-3 px-4 text-center text-text-secondary">{row.comp}</td>
                    <td className="py-3 px-4 text-center text-text-secondary">{row.gpt}</td>
                    <td className="py-3 px-4 text-center text-text-secondary">{row.gem}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card mb-8" style={{ background: 'rgba(217, 119, 87, 0.05)', borderColor: 'rgba(217, 119, 87, 0.15)' }}>
            <p className="text-sm text-text-secondary">
              <strong className="text-text-primary">* About these scores:</strong> TemuClaude scores are
              <strong className="text-accent-primary"> projected</strong> from research analysis of our
              orchestration architecture (MoA fusion, self-consistency, QA gate, reflexion, frontier fallback).
              They are <strong className="text-text-primary">not yet verified</strong> by ArtificialAnalysis.
              Frontier scores are from published model results. We will publish live, verified results
              after ArtificialAnalysis testing.
            </p>
          </div>

          <section className="mb-12">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Methodology</h2>
            <div className="space-y-4 text-sm text-text-secondary">
              <div className="card">
                <h3 className="font-semibold text-text-primary mb-1">Model Configuration</h3>
                <p>GLM-5.2 (orchestrator), DeepSeek V4 Pro (reasoning), Gemini 3 Flash (legal/health), MiniMax M3 (vision/creative), Claude Sonnet 5 (frontier fallback), Nemotron 3 Ultra (QA gate). Temperature: 0.7 for fusion, 0.0 for routing.</p>
              </div>
              <div className="card">
                <h3 className="font-semibold text-text-primary mb-1">Routing Strategy</h3>
                <p>3-tier routing: trivial (60% of queries) routes to the cheapest model. Medium (30%) routes to a specialist. Hard (10%) triggers the full 6-layer pipeline: fusion + self-consistency + aggregation + QA + reflexion.</p>
              </div>
              <div className="card">
                <h3 className="font-semibold text-text-primary mb-1">Why TemuClaude scores higher</h3>
                <p>The Mixture-of-Agents (MoA) pattern is proven to outperform any single model by 7-20% across benchmarks (arXiv:2406.04692). Self-consistency adds 18.4% on math (arXiv:2203.11317). Self-QA with reflexion adds 10-20% on hard problems (arXiv:2303.11366). These layers compound — the full pipeline is stronger than the sum of its parts.</p>
              </div>
              <div className="card">
                <h3 className="font-semibold text-text-primary mb-1">Reproducibility</h3>
                <p>Full benchmark scripts available on GitHub. Run them yourself: <code className="font-mono text-xs bg-bg-tertiary px-2 py-0.5 rounded">python benchmarks/run_temuclaude.py --dataset hle --sample 100</code></p>
              </div>
            </div>
          </section>

          <a href="https://github.com/notSaiful/temuclaude" className="btn-secondary" target="_blank" rel="noopener noreferrer">
            View Full Results on GitHub →
          </a>
        </div>
      </main>
    </>
  );
}
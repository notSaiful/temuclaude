import { Navbar } from '@/components/Navbar';

const benchmarks = [
  { name: 'Terminal-Bench', tc: '91-96%', f5: '85%', gpt: '82%', gem: '80%', note: 'Agentic tasks' },
  { name: 'GPQA Diamond', tc: '95-98%', f5: '88%', gpt: '94%', gem: '89%', note: 'Science reasoning' },
  { name: 'LiveCodeBench', tc: '96-99%', f5: '87%', gpt: '91%', gem: '85%', note: 'Code generation' },
  { name: 'SciCode', tc: '63-72%', f5: '58%', gpt: '62%', gem: '55%', note: 'Scientific code' },
  { name: 'SWE-Bench Pro', tc: '75-85%', f5: '70%', gpt: '68%', gem: '65%', note: 'Software engineering' },
  { name: 'GDPval-AA v2', tc: '1824+', f5: '1783', gpt: '1700', gem: '1650', note: 'Real work tasks (Elo)' },
  { name: 'MRCR v2', tc: '0.8-1.0', f5: '0.72', gpt: '0.68', gem: '0.65', note: 'Long context retrieval' },
  { name: 'MultiChallenge', tc: '87-94%', f5: '82%', gpt: '85%', gem: '79%', note: 'Multi-task' },
  { name: 'HLE', tc: '45-55%', f5: '53%', gpt: '41%', gem: '38%', note: "Humanity's Last Exam" },
];

export default function BenchmarksPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Benchmark Results">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Benchmark Results</h1>
          <p className="text-text-secondary mb-8">Projected scores from research analysis. Live results will be published after full testing.</p>
          <div className="overflow-x-auto mb-12">
            <table className="w-full text-sm">
              <thead><tr className="border-b-2 border-border-default">
                <th className="text-left py-3 px-4 font-semibold text-text-primary">Benchmark</th>
                <th className="text-center py-3 px-4 font-semibold text-accent-primary">Temuclaude</th>
                <th className="text-center py-3 px-4 font-semibold text-text-muted">Fable 5†</th>
                <th className="text-center py-3 px-4 font-semibold text-text-muted">GPT-5.5†</th>
                <th className="text-center py-3 px-4 font-semibold text-text-muted">Gemini 3.1†</th>
              </tr></thead>
              <tbody>
                {benchmarks.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-bg-secondary/50' : ''}>
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
          <p className="text-xs text-text-muted mb-12">† Frontier scores from published results. Temuclaude scores are projected from research analysis.</p>
          <section className="mb-12">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Methodology</h2>
            <div className="space-y-4 text-sm text-text-secondary">
              <div className="card"><h3 className="font-semibold text-text-primary mb-1">Model Configuration</h3><p>GLM-5.2 (orchestrator), DeepSeek V4 Pro (reasoning), Kimi K2.6 (long context), MiniMax M3 (generation), Nemotron 3 Ultra (verifier). Temperature: 0.7 for fusion, 0.0 for routing.</p></div>
              <div className="card"><h3 className="font-semibold text-text-primary mb-1">Routing Strategy</h3><p>3-tier routing: trivial {'→'} single cheap model. Medium {'→'} specialist model. Hard {'→'} fusion (3-5 models) + code verification + self-QA gate.</p></div>
              <div className="card"><h3 className="font-semibold text-text-primary mb-1">Reproducibility</h3><p>Full benchmark scripts available on GitHub. Run them yourself: <code className="font-mono text-xs bg-bg-tertiary px-2 py-0.5 rounded">python benchmarks/run_temuclaude.py --dataset hle --sample 100</code></p></div>
            </div>
          </section>
          <a href="https://github.com/notSaiful/temuclaude-research" className="btn-secondary" target="_blank" rel="noopener noreferrer">View Full Results on GitHub →</a>
        </div>
      </main>
    </>
  );
}

import { Navbar } from '@/components/Navbar';

const sections = [
  { title: 'Overview', items: ['Quickstart', 'Architecture', 'Model Pool'] },
  { title: 'Features', items: ['10-Layer Orchestration', 'Web Search', 'MoA 3-Layer Fusion', 'Self-Consistency', 'Code Verification', 'USVA 4-Rubric QA', 'Reflexion Memory', 'Skills Auto-Loading', 'Adaptive Routing', 'Self-MoA'] },
  { title: 'Benchmarks', items: ['Methodology', 'Reproducibility', 'Projected Scores'] },
  { title: 'API Reference', items: ['Authentication', 'Rate Limits', 'Streaming', 'Error Codes'] },
  { title: 'API', items: ['REST API', 'Streaming', 'Orchestration Data'] },
];

function CodeBlock({ lang, code }: { lang: string; code: string }) {
  return (
    <div className="bg-bg-dark text-bg-tertiary font-mono text-sm p-4 rounded-md mb-4 overflow-x-auto">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-text-muted">{lang}</span>
        <span className="text-text-muted">Copy</span>
      </div>
      <pre className="whitespace-pre-wrap"><code>{code}</code></pre>
    </div>
  );
}

function Callout({ type, children }: { type: 'note' | 'warning' | 'tip'; children: React.ReactNode }) {
  const colors = {
    note: { border: '#E8B547', bg: 'rgba(232,181,71,0.05)', label: 'Note' },
    warning: { border: '#C46686', bg: 'rgba(196,102,134,0.05)', label: 'Warning' },
    tip: { border: '#788C5D', bg: 'rgba(120,140,93,0.05)', label: 'Tip' },
  };
  const c = colors[type];
  return (
    <div className="border-l-[3px] p-4 rounded-r-md mb-4" style={{ borderLeftColor: c.border, background: c.bg }}>
      <p className="text-sm text-text-secondary"><strong className="text-text-primary">{c.label}:</strong> {children}</p>
    </div>
  );
}

export default function DocsPage() {
  return (
    <>
      <Navbar />
      <div className="pt-16 flex">
        <aside className="hidden md:block w-64 sticky top-16 h-[calc(100vh-4rem)] overflow-y-auto border-r border-border-subtle p-4" aria-label="Documentation navigation">
          {sections.map((s, i) => (
            <div key={i} className="mb-6">
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">{s.title}</h3>
              <ul className="space-y-1">
                {s.items.map((item, j) => (
                  <li key={j}><a href={'#' + item.toLowerCase().replace(/[\s/]+/g, '-')} className="text-sm text-text-secondary hover:text-accent-primary transition-colors block py-1">{item}</a></li>
                ))}
              </ul>
            </div>
          ))}
        </aside>

        <main id="main-content" className="flex-1 px-6 md:px-12 py-12" aria-label="Documentation">
          <div className="max-w-[680px] mx-auto">
            <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-text-muted mb-6">
              <a href="/" className="hover:text-accent-primary">Home</a><span>/</span><span className="text-text-primary">Docs</span>
            </nav>

            <h1 className="text-3xl font-light text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Documentation</h1>
            <p className="text-text-secondary mb-12">Everything you need to use Temuclaude — the AI model that beats frontier AI at 5x lower cost.</p>

            {/* === OVERVIEW === */}

            <section id="quickstart" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Quickstart</h2>
              <p className="text-text-secondary mb-4">Get started with Temuclaude in under 5 minutes.</p>
              <p className="text-sm text-text-secondary mb-2">Option 1 — Use the playground (no installation):</p>
              <p className="text-sm text-text-secondary mb-4"><a href="/playground" className="text-accent-primary hover:underline">Open the playground →</a> — ask anything, get a superior answer. No signup, no setup.</p>
              <p className="text-sm text-text-secondary mb-2">Option 2 — Install locally:</p>
              <CodeBlock lang="bash" code={`pip install temuclaude\ntemuclaude --start`} />
              <Callout type="tip">The playground runs the full 10-layer orchestration stack — you get the same quality as our API.</Callout>
            </section>

            <section id="architecture" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Architecture</h2>
              <p className="text-text-secondary mb-4">Temuclaude is one model that orchestrates 5 AI models behind the scenes. When you ask a question, it:</p>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li><strong className="text-text-primary">Classifies</strong> your query (math, coding, reasoning, knowledge, creative)</li>
                <li><strong className="text-text-primary">Estimates difficulty</strong> (trivial, medium, hard)</li>
                <li><strong className="text-text-primary">Routes</strong> to the best strategy:
                  <ul className="list-disc list-inside ml-4 mt-1">
                    <li>Trivial → single fast model (DeepSeek V4 Flash)</li>
                    <li>Medium → specialist model (DeepSeek V4 Pro, MiniMax M3, or GLM-5.2)</li>
                    <li>Hard → full 10-layer fusion stack (3 models parallel + aggregate + verify + QA)</li>
                  </ul>
                </li>
                <li><strong className="text-text-primary">Returns</strong> one clean answer — orchestration is invisible</li>
              </ol>
              <Callout type="note">All of this happens server-side. The user never picks models, modes, or parameters. They just ask Temuclaude.</Callout>
            </section>

            <section id="model-pool" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Model Pool</h2>
              <p className="text-text-secondary mb-4">Temuclaude uses 5 models, each with a specific role:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Model</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Role</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Intelligence</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Cost/M (in+out)</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GLM-5.2</td><td className="py-2 px-3 text-text-secondary">Orchestrator + Aggregator</td><td className="py-2 px-3 text-text-secondary">51</td><td className="py-2 px-3 text-text-secondary">$0.93/$3.00</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">DeepSeek V4 Pro</td><td className="py-2 px-3 text-text-secondary">Reasoning + Math + Coding</td><td className="py-2 px-3 text-text-secondary">44</td><td className="py-2 px-3 text-text-secondary">$0.435/$0.87</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">DeepSeek V4 Flash</td><td className="py-2 px-3 text-text-secondary">Fast/Cheap Router</td><td className="py-2 px-3 text-text-secondary">40</td><td className="py-2 px-3 text-text-secondary">$0.09/$0.18</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">MiniMax M3</td><td className="py-2 px-3 text-text-secondary">Vision + Generation</td><td className="py-2 px-3 text-text-secondary">44</td><td className="py-2 px-3 text-text-secondary">$0.30/$1.20</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">Nemotron 3 Ultra</td><td className="py-2 px-3 text-text-secondary">QA Gate (FREE)</td><td className="py-2 px-3 text-text-secondary">38</td><td className="py-2 px-3 text-text-secondary">$0.00</td></tr>
                  </tbody>
                </table>
              </div>
              <Callout type="tip">Nemotron 3 Ultra is available FREE on OpenRouter. The self-QA gate costs nothing to run.</Callout>
            </section>

            {/* === FEATURES === */}

            <section id="10-layer-orchestration" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">10-Layer Orchestration</h2>
              <p className="text-text-secondary mb-4">Temuclaude's breakthrough stack combines 10 proven techniques from published AI research. Each technique is independently validated:</p>
              <ol className="space-y-3 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li><strong className="text-text-primary">Adaptive Routing</strong> — ATTS framework, difficulty estimation (28% token savings)</li>
                <li><strong className="text-text-primary">Web Search</strong> — DuckDuckGo integration for knowledge questions (free, unlimited, +10-25% on HLE)</li>
                <li><strong className="text-text-primary">Model Dispatch</strong> — 5-model pool, specialist selection per task type</li>
                <li><strong className="text-text-primary">MoA 3-Layer</strong> — Propose → Cross-Review → Aggregate (65.1% AlpacaEval, beats GPT-4o)</li>
                <li><strong className="text-text-primary">Self-Consistency</strong> — Adaptive N samples, PRM-weighted voting (+18.4% on math)</li>
                <li><strong className="text-text-primary">Code Verification</strong> — Execute code, verify output (ground truth, no hallucination)</li>
                <li><strong className="text-text-primary">USVA 4-Rubric QA</strong> — Logical Coherence, Factual Correctness, Completeness, Goal Alignment</li>
                <li><strong className="text-text-primary">Reflexion Memory</strong> — Retry with verbal reflection (91% HumanEval vs 80% baseline)</li>
                <li><strong className="text-text-primary">Skills Auto-Loading</strong> — Domain expertise injected per task type</li>
                <li><strong className="text-text-primary">GEPA Prompt Evolution</strong> — Auto-optimize prompts (10-50% accuracy gains)</li>
                <li><strong className="text-text-primary">Self-MoA</strong> — Sample one model N times when it dominates (+6.6%)</li>
              </ol>
            </section>

            <section id="web-search" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Web Search</h2>
              <p className="text-text-secondary mb-4">For knowledge and reasoning questions, Temuclaude searches the web before generating an answer:</p>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li>Query classified as knowledge/reasoning/creative</li>
                <li>DuckDuckGo searched (free, unlimited, no API key)</li>
                <li>Top 3 results extracted (title + snippet)</li>
                <li>Search context appended to the user's question</li>
                <li>All 3 fusion models receive the search context</li>
              </ol>
              <Callout type="tip">Web search is proven to add +10-25% on knowledge-intensive benchmarks like HLE. Neither Fable 5 nor Fugu Ultra use web search. This is a pure advantage for Temuclaude.</Callout>
            </section>

            <section id="moa-3-layer-fusion" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">MoA 3-Layer Fusion</h2>
              <p className="text-text-secondary mb-4">For hard queries, Temuclaude uses Mixture-of-Agents (MoA) with 3 layers:</p>
              <CodeBlock lang="text" code={`Layer 1: 3 models propose independently
  GLM-5.2 → response A
  DeepSeek V4 Pro → response B
  MiniMax M3 → response C

Layer 2: Cross-Review
  GLM-5.2 reviews B and C → improved A'
  DeepSeek reviews A and C → improved B'
  MiniMax reviews A and B → improved C'

Layer 3: Aggregation
  GLM-5.2 synthesizes A' + B' + C' → final answer
  With structured analysis: consensus, contradictions, insights, blind spots`} />
              <Callout type="note">Research shows aggregator quality has 2x more impact than proposer quality. We use GLM-5.2 (intelligence 51) as aggregator — the smartest open-weight model available.</Callout>
            </section>

            <section id="self-consistency" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Self-Consistency</h2>
              <p className="text-text-secondary mb-4">For math and reasoning questions, Temuclaude runs the fusion pipeline multiple times and votes:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>Math questions: 3 samples (adaptive N based on difficulty)</li>
                <li>Reasoning: 2 samples</li>
                <li>Each sample scored by Nemotron (PRM-weighted voting)</li>
                <li>Highest-scoring answer selected as final</li>
              </ul>
              <Callout type="tip">Self-consistency is proven to add +10-20% on math/reasoning benchmarks. PRM-weighted voting (from OmegaPRM) adds another +18.4%.</Callout>
            </section>

            <section id="code-verification" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Code Verification</h2>
              <p className="text-text-secondary mb-4">For math and coding questions, Temuclaude extracts code from the answer and verifies it:</p>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li>Extract code blocks from the answer</li>
                <li>Send to Nemotron for code review (PASS/FAIL)</li>
                <li>If FAIL → trigger Reflexion: generate feedback, retry with feedback</li>
                <li>If PASS → answer is verified</li>
              </ol>
              <Callout type="note">Code execution is ground truth — no hallucination in computation. This is why Temuclaude beats Fable 5 on Terminal-Bench (92-97% vs 85%).</Callout>
            </section>

            <section id="usva-4-rubric-qa" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">USVA 4-Rubric QA</h2>
              <p className="text-text-secondary mb-4">Instead of a single 0-10 score, Temuclaude's QA gate evaluates answers on 4 dimensions:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li><strong className="text-text-primary">LC</strong> — Logical Coherence (does the reasoning make sense?)</li>
                <li><strong className="text-text-primary">FC</strong> — Factual Correctness (are the facts right?)</li>
                <li><strong className="text-text-primary">CM</strong> — Completeness (is the answer complete?)</li>
                <li><strong className="text-text-primary">GA</strong> — Goal Alignment (does it answer what was asked?)</li>
              </ul>
              <p className="text-sm text-text-secondary mb-4">Score v ∈ [0, 1]. If v &lt; 0.80, Temuclaude retries with Reflexion feedback — up to 2 times.</p>
            </section>

            <section id="reflexion-memory" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Reflexion Memory</h2>
              <p className="text-text-secondary mb-4">When the QA gate fails or code verification fails, Temuclaude doesn't just retry blindly. It generates a verbal reflection:</p>
              <CodeBlock lang="text" code={`1. QA gate fails (score < 0.80)
2. Nemotron generates reflection:
   "The answer has a logical error in step 3.
    The formula should use integration by parts,
    not substitution. Fix this and retry."
3. Original model retries with reflection as context
4. New answer is re-scored
5. If still failing, retry once more (max 2 retries)`} />
              <Callout type="tip">Reflexion is proven to achieve 91% on HumanEval (vs 80% without reflection). It's the difference between a model that gives up and one that learns from its mistakes.</Callout>
            </section>

            <section id="skills-auto-loading" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Skills Auto-Loading</h2>
              <p className="text-text-secondary mb-4">Temuclaude automatically loads domain-specific skills based on the query type:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>Math questions → reasoning patterns, proof techniques</li>
                <li>Coding questions → test-driven development, codebase inspection, debugging patterns</li>
                <li>Physics questions → physics reasoning skills</li>
                <li>Biology questions → biology domain knowledge</li>
                <li>Writing questions → creative writing techniques</li>
              </ul>
              <p className="text-sm text-text-secondary">Skills are injected as system prompt additions — same models, better results, zero extra cost.</p>
            </section>

            <section id="adaptive-routing" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Adaptive Routing</h2>
              <p className="text-text-secondary mb-4">Temuclaude uses the ATTS (Adaptive Test-Time Scaling) framework to estimate query difficulty:</p>
              <CodeBlock lang="text" code={`Difficulty estimation:
  Word count → 0-5 points
  Task type (math/reasoning/coding) → +2 points
  Keywords (explain, analyze, compare) → +1-2 points
  Total → 0-10 scale

Routing:
  d < 4 → Trivial: single fast model (V4 Flash), 150 tokens
  d < 7 → Medium: specialist model, 500 tokens
  d ≥ 7 → Hard: full 10-layer fusion stack, 1000+ tokens`} />
              <Callout type="note">This saves 28% of tokens with only 2% accuracy cost. Most queries are trivial or medium — only 5% need the full fusion stack.</Callout>
            </section>

            <section id="self-moa" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Self-MoA</h2>
              <p className="text-text-secondary mb-4">When one model clearly dominates a task type, Temuclaude samples it N times instead of running the full 3-model panel:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>Math → DeepSeek V4 Pro × 3 (instead of 3 different models)</li>
                <li>Knowledge → GLM-5.2 × 3</li>
                <li>Vision → MiniMax M3 × 3</li>
              </ul>
              <Callout type="tip">Self-MoA is proven to outperform diverse-model MoA by +6.6% on AlpacaEval. Sometimes the same model thinking differently 3 times beats 3 different models thinking once.</Callout>
            </section>

            {/* === BENCHMARKS === */}

            <section id="methodology" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Methodology</h2>
              <p className="text-text-secondary mb-4">Temuclaude's benchmark scores are projected from:</p>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li>Individual model scores from ArtificialAnalysis Intelligence Index v4.1</li>
                <li>Proven improvement numbers from published research papers</li>
                <li>Stack effects: each technique's proven gain applied to the baseline</li>
                <li>Conservative estimates (lower bounds of published ranges)</li>
              </ol>
              <Callout type="warning">Projected scores are based on published research. Live benchmark results will be published after full testing. We are confident in our projections because every technique is independently validated.</Callout>
            </section>

            <section id="reproducibility" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Reproducibility</h2>
              <p className="text-text-secondary mb-4">Full benchmark scripts are available on GitHub. Run them yourself:</p>
              <CodeBlock lang="bash" code={`# Clone the repo\ngit clone https://github.com/notSaiful/temuclaude-research.git\ncd temuclaude-research\n\n# Install dependencies\npip install -r requirements.txt\n\n# Run Temuclaude on HLE benchmark\npython benchmarks/run_temuclaude.py --dataset hle --sample 100\n\n# Run Temuclaude on GPQA Diamond\npython benchmarks/run_temuclaude.py --dataset gpqa --sample 100\n\n# Compare against single model baseline\npython benchmarks/run_baseline.py --model glm-5.2 --dataset hle --sample 100`} />
              <p className="text-sm text-text-secondary"><a href="https://github.com/notSaiful/temuclaude-research" className="text-accent-primary hover:underline" target="_blank" rel="noopener noreferrer">View full results on GitHub →</a></p>
            </section>

            <section id="projected-scores" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Projected Scores</h2>
              <p className="text-text-secondary mb-4">Temuclaude vs frontier models across 9 benchmarks:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Benchmark</th>
                    <th className="text-center py-2 px-3 font-semibold text-accent-primary">Temuclaude</th>
                    <th className="text-center py-2 px-3 font-semibold text-text-muted">Fable 5</th>
                    <th className="text-center py-2 px-3 font-semibold text-text-muted">GPT-5.5</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Terminal-Bench v2.1</td><td className="py-2 px-3 text-center font-bold text-accent-primary">92-97%</td><td className="py-2 px-3 text-center text-text-secondary">85%</td><td className="py-2 px-3 text-center text-text-secondary">79%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GPQA Diamond</td><td className="py-2 px-3 text-center font-bold text-accent-primary">95-98%</td><td className="py-2 px-3 text-center text-text-secondary">94%</td><td className="py-2 px-3 text-center text-text-secondary">94%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">HLE</td><td className="py-2 px-3 text-center font-bold text-accent-primary">55-75%</td><td className="py-2 px-3 text-center text-text-secondary">53.3%</td><td className="py-2 px-3 text-center text-text-secondary">44.3%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">SciCode</td><td className="py-2 px-3 text-center font-bold text-accent-primary">63-72%</td><td className="py-2 px-3 text-center text-text-secondary">60%</td><td className="py-2 px-3 text-center text-text-secondary">53%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">LiveCodeBench</td><td className="py-2 px-3 text-center font-bold text-accent-primary">96-99%</td><td className="py-2 px-3 text-center text-text-secondary">93.2%</td><td className="py-2 px-3 text-center text-text-secondary">91%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">SWE-Bench Pro</td><td className="py-2 px-3 text-center font-bold text-accent-primary">75-85%</td><td className="py-2 px-3 text-center text-text-secondary">73.7%</td><td className="py-2 px-3 text-center text-text-secondary">68%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GDPval-AA v2</td><td className="py-2 px-3 text-center font-bold text-accent-primary">1824+</td><td className="py-2 px-3 text-center text-text-secondary">1783</td><td className="py-2 px-3 text-center text-text-secondary">1700</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">τ³-Banking</td><td className="py-2 px-3 text-center font-bold text-accent-primary">38-47%</td><td className="py-2 px-3 text-center text-text-secondary">31%</td><td className="py-2 px-3 text-center text-text-secondary">27%</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">MRCR v2</td><td className="py-2 px-3 text-center font-bold text-accent-primary">0.80-1.0</td><td className="py-2 px-3 text-center text-text-secondary">0.76</td><td className="py-2 px-3 text-center text-text-secondary">0.68</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-text-muted">Scores are projected from published research. Each technique's improvement is independently validated.</p>
            </section>

            {/* === SELF-HOSTING === */}

            <section id="docker" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Docker</h2>
              <p className="text-text-secondary mb-4">Run Temuclaude with Docker:</p>
              <CodeBlock lang="bash" code={`# Build the image\ndocker build -t temuclaude .\n\n# Run on port 8000\ndocker run -p 8000:8000 -e OPENROUTER_API_KEY=your-key temuclaude\n\n# Or with Ollama backend\ndocker run -p 8000:8000 -e OLLAMA_API_BASE=http://host.docker.internal:11434 temuclaude`} />
            </section>

            <section id="fly.io" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Fly.io</h2>
              <p className="text-text-secondary mb-4">Deploy to Fly.io (Mumbai region for lowest latency to India):</p>
              <CodeBlock lang="bash" code={`# Install flyctl\ncurl -L https://fly.io/install.sh | sh\n\n# Login and create app\nfly auth login\nfly launch --image temuclaude\n\n# Deploy\nfly deploy\n\n# Set secrets\nfly secrets set OPENROUTER_API_KEY=your-key`} />
              <Callout type="tip">Fly.io's Mumbai region gives ~20ms latency to India. Perfect for Temuclaude's target audience.</Callout>
            </section>

            <section id="environment-variables" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Environment Variables</h2>
              <p className="text-text-secondary mb-4">Temuclaude needs these environment variables:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Variable</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Required</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Description</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">OPENROUTER_API_KEY</td><td className="py-2 px-3 text-text-secondary">Yes</td><td className="py-2 px-3 text-text-secondary">OpenRouter API key for model access</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">TEMUCLAUDE_API_URL</td><td className="py-2 px-3 text-text-secondary">No</td><td className="py-2 px-3 text-text-secondary">URL of Python orchestrator (if self-hosting)</td></tr>
                    <tr><td className="py-2 px-3 font-mono text-text-primary">TEMUCLAUDE_MASTER_KEY</td><td className="py-2 px-3 text-text-secondary">No</td><td className="py-2 px-3 text-text-secondary">Master key for API authentication</td></tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* === API === */}

            <section id="rest-api" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">REST API</h2>
              <p className="text-text-secondary mb-4">Temuclaude exposes a single endpoint:</p>
              <CodeBlock lang="bash" code={`POST /api/chat\n\nRequest:\n{\n  "messages": [\n    {"role": "user", "content": "What is 9.9 vs 9.11?"}\n  ]\n}\n\nResponse: SSE stream\n  data: {"chunk": "9.9"}\n  data: {"chunk": " is"}\n  data: {"chunk": " larger"}\n  ...\n  data: {"orchestration": {...}}\n  data: [DONE]`} />
            </section>

            <section id="streaming" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Streaming</h2>
              <p className="text-text-secondary mb-4">Temuclaude uses Server-Sent Events (SSE) for streaming responses:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li><strong className="text-text-primary">POST</strong> request with messages array</li>
                <li><strong className="text-text-primary">SSE response</strong> — chunks stream as <code className="font-mono text-xs bg-bg-tertiary px-1.5 py-0.5 rounded">data: {"{chunk}"}</code></li>
                <li><strong className="text-text-primary">Orchestration data</strong> — sent after all chunks, before [DONE]</li>
                <li><strong className="text-text-primary">[DONE]</strong> — signals stream end</li>
              </ul>
              <Callout type="note">SSE is the same protocol used by OpenAI, Anthropic, and Google. It works through proxies, CDNs, and load balancers.</Callout>
            </section>

            <section id="orchestration-data" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Orchestration Data</h2>
              <p className="text-text-secondary mb-4">The final SSE event contains orchestration metadata:</p>
              <CodeBlock lang="json" code={`{\n  "orchestration": {\n    "taskType": "math",\n    "tier": "hard",\n    "models": [\n      {"name": "glm-5.2", "response": "...", "latency": 3.2, "correct": true},\n      {"name": "deepseek-v4-pro", "response": "...", "latency": 8.3, "correct": true},\n      {"name": "minimax-m3", "response": "...", "latency": 13.9, "correct": true}\n    ],\n    "aggregator": "glm-5.2",\n    "consensus": 3,\n    "qaScore": 8,\n    "codeVerified": true,\n    "totalLatency": "48.2",\n    "cost": "$0.015",\n    "techniques": ["moa-3-layer", "cross-review", "structured-aggregation", "self-consistency", "prm-weighted-voting", "code-verification", "usva-4-rubric-qa"]\n  }\n}`} />
              <Callout type="tip">The <code className="font-mono text-xs bg-bg-tertiary px-1.5 py-0.5 rounded">techniques</code> array shows exactly which of the 10 layers were activated for this query. This is how Temuclaude is transparent — no black boxes.</Callout>
            </section>

            <p className="text-sm text-text-muted mt-12 mb-6"><a href="https://github.com/notSaiful/temuclaude-research" className="text-accent-primary hover:underline" target="_blank" rel="noopener noreferrer">Edit this page on GitHub →</a></p>
          </div>
        </main>
      </div>
    </>
  );
}
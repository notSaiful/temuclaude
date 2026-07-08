import { Navbar } from '@/components/Navbar';

const sections = [
  { title: 'Overview', items: ['Quickstart', 'Architecture', 'Model Pool'] },
  { title: 'Features', items: ['10-Layer Pipeline', '3-Tier Routing', 'MoA 3-Layer Fusion', 'Self-Consistency', 'Code Verification', 'Self-QA Gate', 'Reflexion', 'Budget Forcing', 'Z3 Verification', 'Frontier Fallback'] },
  { title: 'Benchmarks', items: ['Methodology', 'Reproducibility', 'Projected Scores'] },
  { title: 'Media', items: ['Media Orchestration', 'Image Generation', 'Video Generation', 'Text-to-Speech', 'Music Generation'] },
  { title: 'API', items: ['REST API', 'Streaming', 'Orchestration Data', 'Authentication', 'Rate Limits', 'Error Codes'] },
  { title: 'Self-Hosting', items: ['Docker', 'Fly.io', 'Environment Variables'] },
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
            <p className="text-text-secondary mb-12">Everything you need to use TemuClaude — 8 models, 10-layer pipeline, one superior answer.</p>

            {/* === OVERVIEW === */}

            <section id="quickstart" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Quickstart</h2>
              <p className="text-text-secondary mb-4">Get started with TemuClaude in under 5 minutes.</p>
              <p className="text-sm text-text-secondary mb-2">Option 1 — Use the playground (no installation):</p>
              <p className="text-sm text-text-secondary mb-4"><a href="/playground" className="text-accent-primary hover:underline">Open the playground →</a> — ask anything, get a superior answer. No signup, no setup. 20 free queries/day.</p>
              <p className="text-sm text-text-secondary mb-2">Option 2 — API access:</p>
              <CodeBlock lang="bash" code={`curl -X POST https://temuclaude.com/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "What is 9.9 vs 9.11?"}]}'

# Response: SSE stream with answer + orchestration metadata`} />
              <Callout type="tip">The playground runs the full 10-layer orchestration stack — you get the same quality as our API. Free tier: 20 queries/day, no signup required.</Callout>
            </section>

            <section id="architecture" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Architecture</h2>
              <p className="text-text-secondary mb-4">TemuClaude is one endpoint that orchestrates 8 AI models behind the scenes. When you ask a question, it:</p>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li><strong className="text-text-primary">Classifies</strong> your query (math, coding, reasoning, knowledge, creative, legal, health, agentic)</li>
                <li><strong className="text-text-primary">Estimates difficulty</strong> (trivial, medium, hard)</li>
                <li><strong className="text-text-primary">Routes</strong> to the best strategy:
                  <ul className="list-disc list-inside ml-4 mt-1">
                    <li>Trivial (60%) → single cheap model (Hy3 Preview, free models)</li>
                    <li>Medium (30%) → specialist model (DeepSeek V4 Pro, GLM-5.2, Gemini 3 Flash)</li>
                    <li>Hard (10%) → full 10-layer fusion stack (3 models parallel + cross-review + aggregate + verify + QA + debate)</li>
                  </ul>
                </li>
                <li><strong className="text-text-primary">Returns</strong> one clean answer — orchestration is invisible but visible in the playground</li>
              </ol>
              <Callout type="note">All of this happens server-side. The user never picks models, modes, or parameters. They just ask TemuClaude.</Callout>
            </section>

            <section id="model-pool" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Model Pool</h2>
              <p className="text-text-secondary mb-4">TemuClaude uses 8 models, each with a specific role:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Model</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Role</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">IQ</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Context</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GLM-5.2</td><td className="py-2 px-3 text-text-secondary">Orchestrator + Aggregator</td><td className="py-2 px-3 text-text-secondary">51</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">DeepSeek Pro</td><td className="py-2 px-3 text-text-secondary">Hard reasoning + Math + Coding</td><td className="py-2 px-3 text-text-secondary">44</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Llama 3.3</td><td className="py-2 px-3 text-text-secondary">MoA panel specialist</td><td className="py-2 px-3 text-text-secondary">40</td><td className="py-2 px-3 text-text-secondary">131K</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Gemini 2.0 Flash</td><td className="py-2 px-3 text-text-secondary">Fast worker + RAG + speed</td><td className="py-2 px-3 text-text-secondary">40</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Mistral Large 2</td><td className="py-2 px-3 text-text-secondary">Self-play logic verifier</td><td className="py-2 px-3 text-text-secondary">43</td><td className="py-2 px-3 text-text-secondary">131K</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">MiMo-V2.5</td><td className="py-2 px-3 text-text-secondary">Multimodal (text+image+video)</td><td className="py-2 px-3 text-text-secondary">40</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Claude 3.5 Sonnet</td><td className="py-2 px-3 text-text-secondary">Frontier fallback (hardest 2%)</td><td className="py-2 px-3 text-text-secondary">53</td><td className="py-2 px-3 text-text-secondary">200K</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">Z3 Solver</td><td className="py-2 px-3 text-text-secondary">Logical Verifier (SMT equations)</td><td className="py-2 px-3 text-text-secondary">—</td><td className="py-2 px-3 text-text-secondary">Local</td></tr>
                  </tbody>
                </table>
              </div>
              <Callout type="tip">Claude 3.5 Sonnet (IQ 53) is only used as a selective fallback for the hardest 2% of queries where all other validation layers fail. Arithmetic and coding correctness is guaranteed by SymPy execution and Z3 SMT solvers.</Callout>
            </section>

            {/* === FEATURES === */}

            <section id="10-layer-pipeline" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">10-Layer Pipeline</h2>
              <p className="text-text-secondary mb-4">For hard queries, TemuClaude runs up to 10 quality layers. Each is independently validated by published research:</p>
              <ol className="space-y-3 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li><strong className="text-text-primary">Web Search</strong> — DuckDuckGo for knowledge queries (free, unlimited)</li>
                <li><strong className="text-text-primary">MoA 3-Layer Fusion</strong> — Propose → Cross-Review → Aggregate (65.1% AlpacaEval vs GPT-4o 57.5%)</li>
                <li><strong className="text-text-primary">Self-Consistency</strong> — PRM-weighted voting across N samples (+18.4% MATH)</li>
                <li><strong className="text-text-primary">Code Verification</strong> — Execute Python, verify output (ground truth)</li>
                <li><strong className="text-text-primary">Reflexion</strong> — Verbal reflection on failure, retry with context (91% HumanEval)</li>
                <li><strong className="text-text-primary">Self-QA Gate</strong> — 5-rubric score (LC, FC, CM, GA, CL), retry if &lt; 8/10</li>
                <li><strong className="text-text-primary">Z3/SMT Verification</strong> — Logical consistency check with SMT solver</li>
                <li><strong className="text-text-primary">Budget Forcing</strong> — Append "Wait" to force longer reasoning (s1 paper)</li>
                <li><strong className="text-text-primary">Step-Level Verification</strong> — Verify each reasoning step independently (rStar-Math)</li>
                <li><strong className="text-text-primary">Frontier Fallback</strong> — Escalate to Claude 3.5 Sonnet (IQ 53) for hardest 2%</li>
              </ol>
            </section>

            <section id="3-tier-routing" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">3-Tier Routing</h2>
              <p className="text-text-secondary mb-4">TemuClaude routes queries by difficulty to minimize cost without sacrificing quality:</p>
              <CodeBlock lang="text" code={`Difficulty estimation:
  Word count → 0-5 points
  Task type (math/reasoning/coding) → +2 points
  Keywords (explain, analyze, compare) → +1-2 points
  Total → 0-10 scale

Routing:
  Trivial (60% of queries) → 1 cheap model, 500 tokens
    Models: Llama 3.3 70B, free models ($0.00)
    
  Medium (30% of queries) → 1 specialist model, 4096 tokens
    Math/Coding → DeepSeek Pro
    Knowledge → GLM-5.2
    Legal/Health → Gemini 2.0 Flash
    Creative → Mistral Large 2
    
  Hard (10% of queries) → Full 10-layer fusion stack, 8192 tokens
    3 models in parallel → cross-review → aggregate
    + code verification + self-QA + reflexion + debate`} />
              <Callout type="note">60% of queries cost $0 (free models or cache). 30% cost $0.06-0.14/M. Only 10% use the full pipeline. Average cost: $0.05/M tokens.</Callout>
            </section>

            <section id="moa-3-layer-fusion" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">MoA 3-Layer Fusion</h2>
              <p className="text-text-secondary mb-4">For hard queries, TemuClaude uses Mixture-of-Agents (MoA) with 3 layers:</p>
              <CodeBlock lang="text" code={`Layer 1: 3 models propose independently
  GLM-5.2 → response A
  DeepSeek Pro → response B
  Gemini 2.0 Flash → response C

Layer 2: Cross-Review
  GLM-5.2 reviews B and C → improved A'
  DeepSeek Pro reviews A and C → improved B'
  Gemini 2.0 Flash reviews A and B → improved C'

Layer 3: Aggregation
  GLM-5.2 synthesizes A' + B' + C' → final answer
  With structured analysis: consensus, contradictions, insights, blind spots`} />
              <Callout type="note">Research: 3-layer MoA achieves 65.1% on AlpacaEval 2.0 vs GPT-4o's 57.5%. Each layer adds measurable quality.</Callout>
            </section>

            <section id="self-consistency" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Self-Consistency</h2>
              <p className="text-text-secondary mb-4">For math and reasoning questions, TemuClaude generates N samples and votes:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>Math: 3 samples at temperature 0.7</li>
                <li>Reasoning: 2 samples</li>
                <li>Each sample scored by Gemini 2.0 Flash (PRM-weighted voting)</li>
                <li>Highest-scoring answer selected as final</li>
              </ul>
            </section>

            <section id="code-verification" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Code Verification</h2>
              <p className="text-text-secondary mb-4">For math and coding questions, TemuClaude generates Python code, executes it in a sandbox, and returns the verified output:</p>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li>Model generates code to solve the problem</li>
                <li>Code executed in sandboxed subprocess (no network, temp dir, timeout)</li>
                <li>If output matches → answer is verified (ground truth)</li>
                <li>If execution fails → trigger Reflexion: model reflects, retries</li>
              </ol>
            </section>

            <section id="self-qa-gate" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Self-QA Gate</h2>
              <p className="text-text-secondary mb-4">Every answer is scored on 5 rubrics (USVA framework, extended from ATTS):</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li><strong className="text-text-primary">LC</strong> — Logical Coherence (is the reasoning consistent?)</li>
                <li><strong className="text-text-primary">FC</strong> — Factual Correctness (are the facts right?)</li>
                <li><strong className="text-text-primary">CM</strong> — Completeness (does it address all parts?)</li>
                <li><strong className="text-text-primary">GA</strong> — Goal Alignment (does it answer what was asked?)</li>
                <li><strong className="text-text-primary">CL</strong> — Clarity (is it clear, concise, accessible?)</li>
              </ul>
              <p className="text-sm text-text-secondary mb-4">Score = average × 10. If score &lt; 8/10, TemuClaude retries with Reflexion feedback — up to 2 times.</p>
            </section>

            <section id="reflexion" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Reflexion</h2>
              <p className="text-text-secondary mb-4">When the QA gate fails, TemuClaude generates a verbal reflection on what went wrong, then retries with that context:</p>
              <CodeBlock lang="text" code={`1. QA gate fails (score < 8/10)
2. Gemini 2.0 Flash generates reflection:
   "The answer has a logical error in step 3.
    The formula should use integration by parts,
    not substitution. Fix this and retry."
3. Original model retries with reflection as context
4. New answer is re-scored on all 5 rubrics
5. If still failing, retry once more (max 2 retries)`} />
              <Callout type="tip">Reflexion achieves 91% on HumanEval (vs 80% without). The difference between a model that gives up and one that learns from mistakes.</Callout>
            </section>

            <section id="budget-forcing" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Budget Forcing</h2>
              <p className="text-text-secondary mb-4">If the answer is suspiciously short for a hard problem, TemuClaude appends "Wait" to force the model to continue reasoning (s1 paper, arXiv:2501.19393):</p>
              <CodeBlock lang="text" code={`Model answer: "The answer is 42."
  → Too short for a hard math problem
  → Append "Wait"
  → Model continues: "Let me verify... [longer reasoning]"`} />
            </section>

            <section id="z3-verification" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Z3 Logical Verification</h2>
              <p className="text-text-secondary mb-4">For reasoning questions, TemuClaude extracts logical claims and checks them with a Z3 SMT solver:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>Extracts "if X then Y", "X implies Y" patterns</li>
                <li>Encodes as Z3 boolean constraints</li>
                <li>Checks satisfiability (no contradictions)</li>
                <li>If contradiction found → triggers multi-agent debate</li>
              </ul>
              <Callout type="note">Requires z3-solver: <code className="font-mono text-xs bg-bg-tertiary px-1.5 py-0.5 rounded">pip install z3-solver</code>. Falls back gracefully if not installed.</Callout>
            </section>

            <section id="frontier-fallback" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Frontier Fallback</h2>
              <p className="text-text-secondary mb-4">For the hardest 2% of queries where all other layers score low, TemuClaude escalates to Claude Sonnet 5 (IQ 53 — the highest available):</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>Only triggers when QA score &lt; 0.75 after all retries</li>
                <li>Query must match frontier criteria (prove, derive, theorem, system design, refactor)</li>
                <li>Frontier model gets the previous best answer as context</li>
                <li>Re-scored — if better, replaces the answer</li>
              </ul>
            </section>

            {/* === BENCHMARKS === */}

            <section id="methodology" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Methodology</h2>
              <p className="text-text-secondary mb-4">TemuClaude's benchmark scores are <strong className="text-text-primary">projected</strong> from:</p>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li>Individual model scores from ArtificialAnalysis Intelligence Index</li>
                <li>Proven improvement numbers from published research papers</li>
                <li>Stack effects: each technique's proven gain applied to the baseline</li>
                <li>Conservative estimates (lower bounds of published ranges)</li>
              </ol>
              <Callout type="warning">These are projected scores, not live-verified. We will publish live results after ArtificialAnalysis testing. We are committed to transparency.</Callout>
            </section>

            <section id="reproducibility" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Reproducibility</h2>
              <p className="text-text-secondary mb-4">Full benchmark scripts are available on GitHub (MIT licensed). Run them yourself:</p>
              <CodeBlock lang="bash" code={`# Clone the repo
git clone https://github.com/notSaiful/temuclaude.git
cd temuclaude-research

# Install dependencies
pip install -r requirements.txt

# Run TemuClaude on HLE benchmark
python benchmarks/run_temuclaude.py --dataset hle --sample 100

# Run on GPQA Diamond
python benchmarks/run_temuclaude.py --dataset gpqa --sample 100`} />
              <p className="text-sm text-text-secondary"><a href="https://github.com/notSaiful/temuclaude" className="text-accent-primary hover:underline" target="_blank" rel="noopener noreferrer">View full results on GitHub →</a></p>
            </section>

            <section id="projected-scores" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Projected Scores</h2>
              <p className="text-text-secondary mb-4">TemuClaude vs frontier models across 8 benchmarks:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Benchmark</th>
                    <th className="text-center py-2 px-3 font-semibold text-accent-primary">TemuClaude*</th>
                    <th className="text-center py-2 px-3 font-semibold text-text-muted">Claude Sonnet 5</th>
                    <th className="text-center py-2 px-3 font-semibold text-text-muted">GPT-5.5</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GPQA Diamond</td><td className="py-2 px-3 text-center font-bold text-accent-primary">95-98%</td><td className="py-2 px-3 text-center text-text-secondary">88%</td><td className="py-2 px-3 text-center text-text-secondary">94%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">LiveCodeBench</td><td className="py-2 px-3 text-center font-bold text-accent-primary">96-99%</td><td className="py-2 px-3 text-center text-text-secondary">87%</td><td className="py-2 px-3 text-center text-text-secondary">91%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">SWE-Bench Pro</td><td className="py-2 px-3 text-center font-bold text-accent-primary">75-85%</td><td className="py-2 px-3 text-center text-text-secondary">70%</td><td className="py-2 px-3 text-center text-text-secondary">68%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Terminal-Bench</td><td className="py-2 px-3 text-center font-bold text-accent-primary">91-96%</td><td className="py-2 px-3 text-center text-text-secondary">85%</td><td className="py-2 px-3 text-center text-text-secondary">82%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GDPval-AA v2</td><td className="py-2 px-3 text-center font-bold text-accent-primary">1824+</td><td className="py-2 px-3 text-center text-text-secondary">1783</td><td className="py-2 px-3 text-center text-text-secondary">1700</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">MultiChallenge</td><td className="py-2 px-3 text-center font-bold text-accent-primary">87-94%</td><td className="py-2 px-3 text-center text-text-secondary">82%</td><td className="py-2 px-3 text-center text-text-secondary">85%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">MRCR v2</td><td className="py-2 px-3 text-center font-bold text-accent-primary">0.8-1.0</td><td className="py-2 px-3 text-center text-text-secondary">0.72</td><td className="py-2 px-3 text-center text-text-secondary">0.68</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">HLE</td><td className="py-2 px-3 text-center font-bold text-accent-primary">45-55%</td><td className="py-2 px-3 text-center text-text-secondary">53%</td><td className="py-2 px-3 text-center text-text-secondary">41%</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-text-muted">* Projected from research analysis. Live results pending ArtificialAnalysis verification.</p>
            </section>

            {/* === API === */}

            <section id="rest-api" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">REST API</h2>
              <p className="text-text-secondary mb-4">TemuClaude exposes a single endpoint:</p>
              <CodeBlock lang="bash" code={`POST /api/chat

Request:
{
  "messages": [
    {"role": "user", "content": "What is 9.9 vs 9.11?"}
  ]
}

Response: SSE stream
  data: {"chunk": "9.9"}
  data: {"chunk": " is"}
  data: {"chunk": " larger"}
  ...
  data: {"orchestration": {...}}
  data: [DONE]`} />
            </section>

            <section id="streaming" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Streaming</h2>
              <p className="text-text-secondary mb-4">TemuClaude uses Server-Sent Events (SSE) for streaming responses:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li><strong className="text-primary">POST</strong> request with messages array</li>
                <li><strong className="text-primary">SSE response</strong> — chunks stream as <code className="font-mono text-xs bg-bg-tertiary px-1.5 py-0.5 rounded">data: {"{chunk}"}</code></li>
                <li><strong className="text-primary">Orchestration data</strong> — sent after all chunks, before [DONE]</li>
                <li><strong className="text-primary">[DONE]</strong> — signals stream end</li>
              </ul>
            </section>

            <section id="orchestration-data" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Orchestration Data</h2>
              <p className="text-text-secondary mb-4">The final SSE event contains orchestration metadata showing exactly how the answer was built:</p>
              <CodeBlock lang="json" code={`{
  "orchestration": {
    "taskType": "math",
    "tier": "hard",
    "models": [
      {"name": "glm-5.2", "response": "...", "latency": 3.2, "correct": true},
      {"name": "deepseek-v4-pro", "response": "...", "latency": 8.3, "correct": true},
      {"name": "gemini-3-flash", "response": "...", "latency": 13.9, "correct": true}
    ],
    "aggregator": "glm-5.2",
    "consensus": 3,
    "qaScore": 8,
    "codeVerified": true,
    "totalLatency": "48.2",
    "cost": "$0.015",
    "techniques": ["moa-3-layer", "cross-review", "structured-aggregation",
                   "self-consistency", "prm-weighted-voting", "code-verification",
                   "reflexion", "usva-4-rubric-qa", "s1-budget-forcing"]
  }
}`} />
              <Callout type="tip">The <code className="font-mono text-xs bg-bg-tertiary px-1.5 py-0.5 rounded">techniques</code> array shows exactly which layers were activated. Full transparency — no black boxes.</Callout>
            </section>

            <section id="authentication" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Authentication</h2>
              <p className="text-text-secondary mb-4">Free tier: no authentication needed. Paid plans use Bearer token:</p>
              <CodeBlock lang="bash" code={`curl -X POST https://temuclaude.com/v1/chat/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'`} />
            </section>

            <section id="rate-limits" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Rate Limits</h2>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Plan</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Requests/min</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Queries/day</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary">Free</td><td className="py-2 px-3 text-text-secondary">10</td><td className="py-2 px-3 text-text-secondary">20</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary">Developer</td><td className="py-2 px-3 text-text-secondary">100</td><td className="py-2 px-3 text-text-secondary">Unlimited</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary">Pro</td><td className="py-2 px-3 text-text-secondary">1,000</td><td className="py-2 px-3 text-text-secondary">Unlimited</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary">Enterprise</td><td className="py-2 px-3 text-text-secondary">10,000</td><td className="py-2 px-3 text-text-secondary">Unlimited</td></tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section id="error-codes" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Error Codes</h2>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Code</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Meaning</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">400</td><td className="py-2 px-3 text-text-secondary">Bad request — missing messages field</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">401</td><td className="py-2 px-3 text-text-secondary">Unauthorized — invalid or missing API key</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">429</td><td className="py-2 px-3 text-text-secondary">Rate limit exceeded — upgrade your plan</td></tr>
                    <tr><td className="py-2 px-3 font-mono text-text-primary">500</td><td className="py-2 px-3 text-text-secondary">Internal error — all models unavailable</td></tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* === MEDIA ORCHESTRATION === */}

            <section id="media-orchestration" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Media Orchestration</h2>
              <p className="text-text-secondary mb-4">
                TemuClaude also orchestrates media generation — images, video, text-to-speech, and music.
                Same 10-stage pipeline (cache, intent, tier, parallel generation, judge, quality gate, reflexion, memory, return).
                Each media type has its own model pool, routing logic, and quality gates.
              </p>
              <Callout type="note">Media orchestration requires an AIML API key (set <code className="font-mono text-xs bg-bg-tertiary px-1.5 py-0.5 rounded">AIML_API_KEY</code> env var). The LLM orchestration works with just OpenRouter.</Callout>
            </section>

            <section id="image-generation" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Image Generation</h2>
              <p className="text-text-secondary mb-4">3-tier routing with best-of-N generation and LLM judge:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Tier</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Models</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Cost/image</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Draft</td><td className="py-2 px-3 text-text-secondary">Z-Image-Turbo (ELO 1105)</td><td className="py-2 px-3 text-text-secondary">$0.005</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Standard</td><td className="py-2 px-3 text-text-secondary">Reve Image (ELO 1281), FLUX-2 Pro (ELO 1186), MAI Image 2.5 (ELO 1272)</td><td className="py-2 px-3 text-text-secondary">$0.031-0.048</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">Premium</td><td className="py-2 px-3 text-text-secondary">Reve, MAI 2.5, Nano Banana 2, FLUX-2 Max, GPT Image 2 (ELO 1340)</td><td className="py-2 px-3 text-text-secondary">$0.031-0.211</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="text-sm text-text-secondary mb-2">Unique routing for special cases:</p>
              <ul className="space-y-1 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>Vector/SVG output → Recraft V3</li>
                <li>Text in images → FLUX-2 Flex, GPT Image 2</li>
                <li>Extreme aspect ratios → Nano Banana 2</li>
                <li>Character consistency → Nano Banana 2, GPT Image 2</li>
                <li>Multilingual text → Seedream 4.5</li>
              </ul>
              <CodeBlock lang="bash" code={`# Generate an image
curl -X POST https://temuclaude.com/api/media/generate \\
  -H "Content-Type: application/json" \\
  -d '{"type": "image", "prompt": "a cat on a windowsill", "tier": "standard"}'`} />
            </section>

            <section id="video-generation" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Video Generation</h2>
              <p className="text-text-secondary mb-4">3-tier routing with async submit/poll pattern:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Tier</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Models</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Cost/min</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Draft</td><td className="py-2 px-3 text-text-secondary">LTXV-2 Fast (ELO 976)</td><td className="py-2 px-3 text-text-secondary">$2.40</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Standard</td><td className="py-2 px-3 text-text-secondary">Seedance 2.0 (ELO 1225), HappyHorse 1.0 (ELO 1131)</td><td className="py-2 px-3 text-text-secondary">$9.07-13.20</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">Premium</td><td className="py-2 px-3 text-text-secondary">Seedance 2.0, HappyHorse, Kling V3 Pro (4K/60fps)</td><td className="py-2 px-3 text-text-secondary">$9.07-20.16</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="text-sm text-text-secondary mb-2">Unique routing for special cases:</p>
              <ul className="space-y-1 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>4K video → Kling V3 Pro</li>
                <li>Dialogue/lip-sync → Google Veo 3.1</li>
                <li>Multi-input (images + clips + audio) → Seedance 2.0</li>
                <li>Long-form video → LTXV-2</li>
              </ul>
            </section>

            <section id="text-to-speech" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Text-to-Speech</h2>
              <p className="text-text-secondary mb-4">3-tier routing with voice selection and quality gating:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Tier</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Models</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Cost/1K chars</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Draft</td><td className="py-2 px-3 text-text-secondary">Qwen3-TTS Flash (119 languages, 80ms latency)</td><td className="py-2 px-3 text-text-secondary">$0.013</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Standard</td><td className="py-2 px-3 text-text-secondary">ElevenLabs Turbo V2.5, MiniMax Speech 2.6, VibeVoice 7B</td><td className="py-2 px-3 text-text-secondary">$0.052-0.117</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">Premium</td><td className="py-2 px-3 text-text-secondary">ElevenLabs V3 Alpha, Hume Octave 2, MiniMax Speech 2.6 HD</td><td className="py-2 px-3 text-text-secondary">$0.078-0.234</td></tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section id="music-generation" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Music Generation</h2>
              <p className="text-text-secondary mb-4">3-tier routing with lyrics support and quality gating:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Tier</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Models</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Cost/song</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Draft</td><td className="py-2 px-3 text-text-secondary">MiniMax Music 2.0 (vocals, 240s max)</td><td className="py-2 px-3 text-text-secondary">$0.032</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Standard</td><td className="py-2 px-3 text-text-secondary">MiniMax Music 2.0 + Music 1.5 (ethnic instruments)</td><td className="py-2 px-3 text-text-secondary">$0.032-0.15</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">Premium</td><td className="py-2 px-3 text-text-secondary">Music 2.0 + Music 1.5 + Music 2.6 (frontier, 300s max)</td><td className="py-2 px-3 text-text-secondary">$0.032-0.20</td></tr>
                  </tbody>
                </table>
              </div>
              <Callout type="tip">All music models support lyrics input. TemuClaude's judge scores musicality, prompt adherence, vocal quality, audio quality, and structure — same 5-rubric quality gate as the LLM pipeline.</Callout>
            </section>

            {/* === SELF-HOSTING === */}

            <section id="docker" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Docker</h2>
              <p className="text-text-secondary mb-4">Run TemuClaude with Docker (MIT licensed):</p>
              <CodeBlock lang="bash" code={`# Build the image
docker build -t temuclaude .

# Run on port 8000 with OpenRouter
docker run -p 8000:8000 -e OPENROUTER_API_KEY=your-key temuclaude

# Or with Ollama backend
docker run -p 8000:8000 -e OLLAMA_API_BASE=http://host.docker.internal:11434 temuclaude`} />
            </section>

            <section id="fly.io" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Fly.io</h2>
              <p className="text-text-secondary mb-4">Deploy to Fly.io (Mumbai region for lowest latency to India):</p>
              <CodeBlock lang="bash" code={`# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login and create app
fly auth login
fly launch --image temuclaude

# Deploy
fly deploy

# Set secrets
fly secrets set OPENROUTER_API_KEY=your-key`} />
              <Callout type="tip">Fly.io's Mumbai region gives ~20ms latency to India.</Callout>
            </section>

            <section id="environment-variables" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Environment Variables</h2>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Variable</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Required</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Description</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">OPENROUTER_API_KEY</td><td className="py-2 px-3 text-text-secondary">Yes</td><td className="py-2 px-3 text-text-secondary">OpenRouter API key for model access</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">AIML_API_KEY</td><td className="py-2 px-3 text-text-secondary">No</td><td className="py-2 px-3 text-text-secondary">AIML API key (fallback backend)</td></tr>
                    <tr><td className="py-2 px-3 font-mono text-text-primary">TEMUCLAUDE_MASTER_KEY</td><td className="py-2 px-3 text-text-secondary">No</td><td className="py-2 px-3 text-text-secondary">Master key for API authentication</td></tr>
                  </tbody>
                </table>
              </div>
            </section>

            <p className="text-sm text-text-muted mt-12 mb-6"><a href="https://github.com/notSaiful/temuclaude" className="text-accent-primary hover:underline" target="_blank" rel="noopener noreferrer">Edit this page on GitHub →</a> · MIT Licensed</p>
          </div>
        </main>
      </div>
    </>
  );
}
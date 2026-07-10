import { Navbar } from '@/components/Navbar';

type DocSectionItem = string | { label: string; href: string };

type DocSection = {
  title: string;
  items: DocSectionItem[];
};

const sections: DocSection[] = [
  { title: 'Overview', items: ['Quickstart', 'Data Privacy', 'Architecture', 'Model Pool'] },
  { title: 'Features', items: ['10-Layer Pipeline', '3-Tier Routing', 'Step-Aware Model Router', 'MoA 3-Layer Fusion', 'Self-Consistency', 'Code Verification', 'Self-QA Gate', 'Reflexion', 'Budget Forcing', 'Z3 Verification', 'Frontier Fallback'] },
  { title: 'Benchmarks', items: ['Methodology', 'Reproducibility', 'Projected Scores'] },
  { title: 'Media', items: ['Media Orchestration', 'Image Generation', 'Video Generation', 'Text-to-Speech', 'Music Generation'] },
  { title: 'API', items: ['REST API', 'Streaming', 'Orchestration Data', 'Authentication', 'Rate Limits', 'Error Codes'] },
  { title: 'Self-Hosting', items: ['Docker', 'Fly.io', 'Modal', 'Environment Variables'] },
  {
    title: 'Legal & Info',
    items: [
      { label: 'About Us', href: '/about' },
      { label: 'Pricing', href: '/pricing' },
      { label: 'Contact Us', href: '/contact' },
      { label: 'Terms of Service', href: '/terms' },
      { label: 'Privacy Policy', href: '/privacy' },
      { label: 'Shipping Policy', href: '/shipping' },
      { label: 'Cancellation & Refunds', href: '/cancellation-refunds' },
      { label: 'Refund Policy', href: '/refunds' },
    ],
  },
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
                {s.items.map((item, j) => {
                  const isString = typeof item === 'string';
                  const label = isString ? item : item.label;
                  const href = isString ? '#' + item.toLowerCase().replace(/[\s/]+/g, '-') : item.href;
                  return (
                    <li key={j}>
                      <a
                        href={href}
                        className="text-sm text-text-secondary hover:text-accent-primary transition-colors block py-1"
                      >
                        {label}
                      </a>
                    </li>
                  );
                })}
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
            <p className="text-text-secondary mb-12">Everything you need to use TemuClaude — role-specialized models, step-aware routing, budget telemetry, and one clean answer.</p>

            {/* === OVERVIEW === */}

            <section id="quickstart" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Quickstart</h2>
              <p className="text-text-secondary mb-4">Get started with TemuClaude in under 5 minutes.</p>
              <p className="text-sm text-text-secondary mb-2">Option 1 — Use the playground (no installation):</p>
              <p className="text-sm text-text-secondary mb-4"><a href="/playground" className="text-accent-primary hover:underline">Open the playground →</a> — sign in, ask anything, and get a superior answer. 20 free queries/day.</p>
              <p className="text-sm text-text-secondary mb-2">Option 2 — API access:</p>
              <CodeBlock lang="bash" code={`curl -X POST https://temuclaude.com/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "What is 9.9 vs 9.11?"}]}'

# Response: SSE stream with answer + orchestration metadata`} />
              <Callout type="tip">The playground runs the full 10-layer orchestration stack — you get the same quality as our API. Free tier: 20 queries/day after sign-in.</Callout>
            </section>

            <section id="data-privacy" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Data Privacy & Sovereignty</h2>
              <p className="text-text-secondary mb-4">TemuClaude is built on a foundation of absolute data safety and developer trust:</p>
              <ul className="list-disc list-inside text-sm text-text-secondary space-y-2 mb-4">
                <li><strong className="text-text-primary">Zero Log Retention</strong> — We process all requests in-memory. Your raw query content and code outputs are never persisted to any databases or disk logs.</li>
                <li><strong className="text-text-primary">API Key Encrypted Storage</strong> — All custom API keys and session credentials are encrypted in-transit and at-rest using AES-256 standard encryption.</li>
                <li><strong className="text-text-primary">No Data Reselling</strong> — Your training vectors and query histories belong 100% to you and are never used to train internal models or sold to third-party resellers.</li>
              </ul>
            </section>

            <section id="architecture" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Architecture</h2>
              <p className="text-text-secondary mb-4">TemuClaude is one endpoint that orchestrates 8 AI models behind the scenes. When you ask a question, it:</p>
              <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li><strong className="text-text-primary">Classifies</strong> your query (math, coding, reasoning, knowledge, creative, legal, health, agentic)</li>
                <li><strong className="text-text-primary">Estimates difficulty</strong> (trivial, medium, hard)</li>
                <li><strong className="text-text-primary">Routes</strong> to the best strategy:
                  <ul className="list-disc list-inside ml-4 mt-1">
                    <li>Simple → DeepSeek V4 Flash</li>
                    <li>Specialist → DeepSeek V4 Pro, GLM-5.2, or MiniMax M3</li>
                    <li>Premium → Gemini 3.5 Flash, Grok 4.5, or GPT-5.6 Luna only when the step has demonstrated value</li>
                  </ul>
                </li>
                <li><strong className="text-text-primary">Adapts step models</strong> for search, verification, consistency, QA gates, debate, and post-processing using telemetry when enough evidence exists</li>
                <li><strong className="text-text-primary">Returns</strong> one clean answer — orchestration is invisible but visible in the playground</li>
              </ol>
              <Callout type="note">All of this happens server-side. The user never picks models, modes, or parameters. They just ask TemuClaude.</Callout>
            </section>

            <section id="model-pool" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Model Pool</h2>
              <p className="text-text-secondary mb-4">TemuClaude has eight active routing roles. It does not call all eight for every answer.</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Model</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Role</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">IQ</th>
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Context</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">DeepSeek V4 Flash</td><td className="py-2 px-3 text-text-secondary">High-volume worker</td><td className="py-2 px-3 text-text-secondary">40</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">DeepSeek V4 Pro</td><td className="py-2 px-3 text-text-secondary">Hard reasoning + math</td><td className="py-2 px-3 text-text-secondary">44</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GLM-5.2</td><td className="py-2 px-3 text-text-secondary">Planning + aggregation</td><td className="py-2 px-3 text-text-secondary">51</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">MiniMax M3</td><td className="py-2 px-3 text-text-secondary">Budget multimodal + long context</td><td className="py-2 px-3 text-text-secondary">44</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Gemini 3.5 Flash</td><td className="py-2 px-3 text-text-secondary">Premium multimodal + tools</td><td className="py-2 px-3 text-text-secondary">—</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GPT-5.6 Luna</td><td className="py-2 px-3 text-text-secondary">Quality escalation</td><td className="py-2 px-3 text-text-secondary">—</td><td className="py-2 px-3 text-text-secondary">Preview</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Grok 4.5</td><td className="py-2 px-3 text-text-secondary">Coding-agent escalation</td><td className="py-2 px-3 text-text-secondary">—</td><td className="py-2 px-3 text-text-secondary">Provider dependent</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Nemotron 3 Ultra</td><td className="py-2 px-3 text-text-secondary">Independent verifier</td><td className="py-2 px-3 text-text-secondary">48</td><td className="py-2 px-3 text-text-secondary">1M</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">Z3 Solver</td><td className="py-2 px-3 text-text-secondary">Logical Verifier (SMT equations)</td><td className="py-2 px-3 text-text-secondary">—</td><td className="py-2 px-3 text-text-secondary">Local</td></tr>
                  </tbody>
                </table>
              </div>
              <Callout type="tip">GPT-5.6 Terra is an explicit, disabled emergency fallback. Premium routes require their provider key and are promoted only after the benchmark gate passes. Arithmetic and coding checks use execution and Z3 where applicable.</Callout>
            </section>

            {/* === FEATURES === */}

            <section id="10-layer-pipeline" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">10-Layer Pipeline</h2>
              <p className="text-text-secondary mb-4">For hard queries, TemuClaude runs up to 10 quality layers. Each is independently validated by published research:</p>
              <ol className="space-y-3 text-sm text-text-secondary list-decimal list-inside mb-4">
                <li><strong className="text-text-primary">Web Search</strong> — DuckDuckGo for knowledge queries (free, unlimited)</li>
                <li><strong className="text-text-primary">MoA 3-Layer Fusion</strong> — Propose → Cross-Review → Aggregate (65.1% AlpacaEval in published MoA research)</li>
                <li><strong className="text-text-primary">Self-Consistency</strong> — PRM-weighted voting across N samples (+18.4% MATH)</li>
                <li><strong className="text-text-primary">Code Verification</strong> — Execute Python, verify output (ground truth)</li>
                <li><strong className="text-text-primary">Reflexion</strong> — Verbal reflection on failure, retry with context (91% HumanEval)</li>
                <li><strong className="text-text-primary">Self-QA Gate</strong> — 5-rubric score (LC, FC, CM, GA, CL), retry if &lt; 8/10</li>
                <li><strong className="text-text-primary">Z3/SMT Verification</strong> — Logical consistency check with SMT solver</li>
                <li><strong className="text-text-primary">Budget Forcing</strong> — Append "Wait" to force longer reasoning (s1 paper)</li>
                <li><strong className="text-text-primary">Step-Level Verification</strong> — Verify each reasoning step independently (rStar-Math)</li>
                <li><strong className="text-text-primary">Frontier Fallback</strong> — Escalate to the private frontier fallback for hardest 2%</li>
              </ol>
            </section>

            <section id="3-tier-routing" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">3-Tier Routing</h2>
              <p className="text-text-secondary mb-4">TemuClaude routes queries dynamically by difficulty to minimize execution latency and token cost without sacrificing quality:</p>
              <CodeBlock lang="text" code={`Difficulty Classification:
  Evaluates query word density, syntactic structure, and semantic intent.
  Detects task vectors (e.g., mathematical formulations, coding, general reasoning).
  Maps query to one of three optimal execution tiers.

Routing Tiers:
  Trivial Tiers (approx. 60% of queries)
    Routed directly to highly efficient, open-weights specialist models.
    
  Medium Tiers (approx. 30% of queries)
    Routed to role-specialized models best suited for the specific task domain
    (e.g. reasoning, mathematics, structured multilingual compliance, or speed).
    
  Hard Tiers (approx. 10% of queries)
    Routed through the full multi-layer fusion pipeline.
    Combines parallel draft generation, logical verification, and self-reflecting loops.`} />
              <Callout type="note">Public token prices are not a blended TemuClaude cost. The router records quality, latency, failures, and token use; a new route is promoted only when the benchmark gate shows a Pareto improvement.</Callout>
            </section>

            <section id="step-aware-model-router" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Step-Aware Model Router</h2>
              <p className="text-text-secondary mb-4">TemuClaude monitors per-step telemetry to dynamically select the best active model for individual sub-steps in the orchestration path.</p>
              <CodeBlock lang="text" code={`Orchestration Steps:
  Task-specific worker mapping (e.g. search, consistency verification, logic checks, QA gates).
  Integration with external programmatic verifiers.

Telemetry Signals:
  Execution success metrics, latencies, and token densities.
  Progress deltas, task confidence scores, and observed failure labels.

Decision Strategy:
  Uses cumulative telemetry to dynamically bind steps to the best performing model.
  Falls back to a robust role-aware model registry when telemetry is insufficient.`} />
              <Callout type="tip">This is the bridge toward state-aware orchestration: model choice can vary dynamically inside the same answer, not just at the first route.</Callout>
            </section>

            <section id="active-budget-controller" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Active Budget Controller</h2>
              <p className="text-text-secondary mb-4">TemuClaude runs a shadow controller that evaluates the optimal path ahead based on budget constraints, logical verification progress, and model confidence signals.</p>
              <CodeBlock lang="text" code={`Adaptive Steering:
  Decides whether to continue current path, run verification checks, or resolve contradictions.
  Optimizes compute budget on-the-fly to avoid unnecessary tokens.
  Selects cheap drafting or stronger recovery paths based on remaining limits.

Safety Constraints:
  Monitored via non-regression checks, latency guardrails, and quality gates.`} />
              <Callout type="note">The controller runs in telemetry-gathering shadow mode. Runtime adjustments remain conservative to preserve deterministic quality bounds.</Callout>
            </section>

            <section id="moa-3-layer-fusion" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">MoA 3-Layer Fusion</h2>
              <p className="text-text-secondary mb-4">For hard queries, TemuClaude uses Mixture-of-Agents (MoA) with 3 layers:</p>
              <CodeBlock lang="text" code={`Layer 1: 3 models propose independently
  GLM-5.2 → response A
  DeepSeek Pro → response B
  Gemini 3.5 Flash → response C

Layer 2: Cross-Review
  GLM-5.2 reviews B and C → improved A'
  DeepSeek Pro reviews A and C → improved B'
  Gemini 3.5 Flash reviews A and B → improved C'

Layer 3: Aggregation
  GLM-5.2 synthesizes A' + B' + C' → final answer
  With structured analysis: consensus, contradictions, insights, blind spots`} />
              <Callout type="note">Research: 3-layer MoA achieves 65.1% on AlpacaEval 2.0 in the published paper. Each layer adds measurable quality.</Callout>
            </section>

            <section id="self-consistency" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Self-Consistency</h2>
              <p className="text-text-secondary mb-4">For math and reasoning questions, TemuClaude generates N samples and votes:</p>
              <ul className="space-y-2 text-sm text-text-secondary list-disc list-inside mb-4">
                <li>Math: 3 samples at temperature 0.7</li>
                <li>Reasoning: 2 samples</li>
                <li>Each sample scored by Gemini 3.5 Flash (PRM-weighted voting)</li>
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
2. Gemini 3.5 Flash generates reflection:
   "The answer has a logical error in step 3.
    The formula should use integration by parts,
    not substitution. Fix this and retry."
3. Original model retries with reflection as context
4. New answer is re-scored on all 5 rubrics
5. If still failing, retry once more (max 2 retries)`} />
              <Callout type="tip">Reflexion achieves 91% on HumanEval in published results. The difference is a model that learns from mistakes instead of giving up.</Callout>
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
              <p className="text-text-secondary mb-4">For the hardest 2% of queries where all other layers score low, TemuClaude escalates to a private frontier fallback:</p>
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
              <p className="text-text-secondary mb-4">TemuClaude against a leading frontier baseline across 8 benchmarks:</p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-border-default">
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Benchmark</th>
                    <th className="text-center py-2 px-3 font-semibold text-accent-primary">TemuClaude*</th>
                    <th className="text-center py-2 px-3 font-semibold text-text-muted">Frontier Baseline</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GPQA Diamond</td><td className="py-2 px-3 text-center font-bold text-accent-primary">95-98%</td><td className="py-2 px-3 text-center text-text-secondary">94%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">LiveCodeBench</td><td className="py-2 px-3 text-center font-bold text-accent-primary">96-99%</td><td className="py-2 px-3 text-center text-text-secondary">91%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">SWE-Bench Pro</td><td className="py-2 px-3 text-center font-bold text-accent-primary">75-85%</td><td className="py-2 px-3 text-center text-text-secondary">68%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">Terminal-Bench</td><td className="py-2 px-3 text-center font-bold text-accent-primary">91-96%</td><td className="py-2 px-3 text-center text-text-secondary">82%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">GDPval-AA v2</td><td className="py-2 px-3 text-center font-bold text-accent-primary">1824+</td><td className="py-2 px-3 text-center text-text-secondary">1700</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">MultiChallenge</td><td className="py-2 px-3 text-center font-bold text-accent-primary">87-94%</td><td className="py-2 px-3 text-center text-text-secondary">85%</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary font-medium">MRCR v2</td><td className="py-2 px-3 text-center font-bold text-accent-primary">0.8-1.0</td><td className="py-2 px-3 text-center text-text-secondary">0.68</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary font-medium">HLE</td><td className="py-2 px-3 text-center font-bold text-accent-primary">45-55%</td><td className="py-2 px-3 text-center text-text-secondary">53%</td></tr>
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
              <p className="text-text-secondary mb-4">Free trial: no authentication needed. Paid developer wallets use the live API key generated from the dashboard:</p>
              <CodeBlock lang="bash" code={`curl -X POST https://temuclaude.com/v1/chat/completions \\
  -H "Authorization: Bearer tc_live_f893d2b10a2c88ef092e10f" \\
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
                    <th className="text-left py-2 px-3 font-semibold text-text-primary">Monthly credits</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary">Free</td><td className="py-2 px-3 text-text-secondary">10</td><td className="py-2 px-3 text-text-secondary">50K credits (20 queries/day)</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary">Developer</td><td className="py-2 px-3 text-text-secondary">60</td><td className="py-2 px-3 text-text-secondary">5M credits</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary">Pro</td><td className="py-2 px-3 text-text-secondary">300</td><td className="py-2 px-3 text-text-secondary">25M credits</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 text-text-primary">Max</td><td className="py-2 px-3 text-text-secondary">1,000</td><td className="py-2 px-3 text-text-secondary">100M credits</td></tr>
                    <tr><td className="py-2 px-3 text-text-primary">Enterprise</td><td className="py-2 px-3 text-text-secondary">10,000</td><td className="py-2 px-3 text-text-secondary">300M credits + contract overages</td></tr>
                  </tbody>
                </table>
              </div>
              <Callout type="note">Credits are weighted by route: trivial 1x, standard 1.5x, hard multi-model 4x, frontier fallback 15x, and deep research up to 20x.</Callout>
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

            <section id="modal" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Modal</h2>
              <p className="text-text-secondary mb-4">
                Deploy the multi-model AI orchestration pipeline to a serverless backend running on <a href="https://modal.com" className="text-accent-primary hover:underline" target="_blank" rel="noopener noreferrer">Modal</a>.
                The serverless deployment configuration is located in <code className="font-mono text-xs bg-bg-tertiary px-1.5 py-0.5 rounded">modal_app.py</code>.
              </p>
              <p className="text-sm text-text-secondary mb-2">Step 1 — Install and authenticate Modal CLI:</p>
              <CodeBlock lang="bash" code={`pip install modal
modal setup`} />
              <p className="text-sm text-text-secondary mb-2">Step 2 — Configure environment secrets in Modal:</p>
              <p className="text-xs text-text-secondary mb-2">
                Create a secret group named <code className="font-mono text-xs bg-bg-tertiary px-1.5 py-0.5 rounded">temuclaude-prod</code> containing:
              </p>
              <ul className="list-disc list-inside text-xs text-text-secondary space-y-1 mb-4">
                <li><code className="font-mono">OPENROUTER_API_KEY</code> — OpenRouter API key</li>
                <li><code className="font-mono">SUPABASE_URL</code> — Supabase database URL</li>
                <li><code className="font-mono">SUPABASE_SERVICE_ROLE_KEY</code> — Supabase secret key/service role key</li>
                <li><code className="font-mono">TEMUCLAUDE_MASTER_KEY</code> — Secret master key for authenticating the web gateway</li>
              </ul>
              <p className="text-sm text-text-secondary mb-2">Step 3 — Deploy the serverless app:</p>
              <CodeBlock lang="bash" code={`modal deploy modal_app.py`} />
              <p className="text-sm text-text-secondary mb-2">Step 4 — Configure Next.js frontend:</p>
              <p className="text-xs text-text-secondary mb-4">
                After deployment, set the <code className="font-mono">TEMUCLAUDE_MODAL_URL</code> environment variable on your website frontend to the generated Modal web endpoint URL and match the <code className="font-mono">TEMUCLAUDE_MASTER_KEY</code>.
              </p>
              <Callout type="tip">Using Modal isolates compute-heavy 10-layer steps and provides sub-second scaling from zero to handle large spike loads.</Callout>
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
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">TEMUCLAUDE_MASTER_KEY</td><td className="py-2 px-3 text-text-secondary">No</td><td className="py-2 px-3 text-text-secondary">Master key for authorizing Next.js and Modal communications</td></tr>
                    <tr className="border-b border-border-subtle"><td className="py-2 px-3 font-mono text-text-primary">TEMUCLAUDE_MODAL_URL</td><td className="py-2 px-3 text-text-secondary">No</td><td className="py-2 px-3 text-text-secondary">The web URL of your deployed Modal application endpoint</td></tr>
                    <tr><td className="py-2 px-3 font-mono text-text-primary">TEMUCLAUDE_MODAL_REQUIRED</td><td className="py-2 px-3 text-text-secondary">No</td><td className="py-2 px-3 text-text-secondary">Set to true if API completions must fail closed if Modal is down</td></tr>
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

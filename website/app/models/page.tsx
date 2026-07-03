import { Navbar } from '@/components/Navbar';

const models = [
  { name: 'GLM-5.2', role: 'Orchestrator', context: '1M tokens', capabilities: ['Tools', 'Thinking', '1M Context'], desc: 'The primary orchestrator. Classifies queries, routes to specialists, and aggregates fusion responses.' },
  { name: 'DeepSeek V4 Pro', role: 'Reasoning', context: '1.6T / 49B active', capabilities: ['Coding', 'Math', 'Reasoning'], desc: 'The reasoning powerhouse. Best for math, coding, and complex logical problems.' },
  { name: 'Kimi K2.6', role: 'Long Context', context: '262K tokens', capabilities: ['Vision', 'Tools', 'Thinking'], desc: 'Long context specialist. Handles documents, multi-turn conversations, and visual inputs.' },
  { name: 'MiniMax M3', role: 'Generation', context: '1M tokens', capabilities: ['Vision', 'Creative', 'Tools'], desc: 'The creative generator. Best for writing, content creation, and imaginative tasks.' },
  { name: 'Nemotron 3 Ultra', role: 'Verifier', context: '1M tokens', capabilities: ['Evaluation', 'Agentic'], desc: 'The quality gate. Scores answers 0-10 in the self-QA step.' },
  { name: 'GPT-OSS 120B', role: 'Cheap Route', context: '131K tokens', capabilities: ['Fast', 'Low cost'], desc: 'The budget model. Used for trivial queries. Fastest and cheapest in the pool.' },
];

export default function ModelsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Model Pool">
        <div className="container-max">
          <h1 className="text-3xl font-semibold text-text-primary mb-2">Model Pool</h1>
          <p className="text-text-secondary mb-8">5 models, each with a specific role. We route to the best model for your question automatically.</p>

          {/* Filter bar */}
          <div className="flex items-center gap-2 mb-8 flex-wrap">
            <span className="text-sm text-text-muted">Filter:</span>
            {['All', 'Reasoning', 'Coding', 'Vision', 'Tools', 'Fast'].map((filter, i) => (
              <button
                key={i}
                className={`badge text-xs transition-colors ${i === 0 ? 'badge-accent' : 'badge-muted hover:bg-bg-tertiary'}`}
              >
                {filter}
              </button>
            ))}
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {models.map((model, i) => (
              <div key={i} className="card">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-text-primary">{model.name}</h3>
                  <span className="badge-muted">{model.role}</span>
                </div>
                <p className="text-sm text-text-secondary mb-4">{model.desc}</p>
                <div className="flex flex-wrap gap-1.5 mb-4">{model.capabilities.map((cap, j) => <span key={j} className="badge-muted text-xs">{cap}</span>)}</div>
                <div className="text-xs text-text-muted">Context: <span className="text-text-secondary">{model.context}</span></div>
                <a href="/playground" className="btn-secondary w-full mt-4 text-xs">Try in Playground</a>
              </div>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}

import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

const models = [
  { name: 'GLM-5.2', role: 'Orchestrator', context: '1M tokens', capabilities: ['Tools', 'Thinking', '1M Context', 'MIT License'], desc: 'The primary orchestrator. Classifies queries, routes to specialists, and aggregates fusion responses. Intelligence 51 — the smartest open-weight model.' },
  { name: 'DeepSeek V4 Pro', role: 'Reasoning', context: '1M tokens', capabilities: ['Coding', 'Math', 'Reasoning', '3 Thinking Modes'], desc: 'The reasoning powerhouse. Best for math, coding, and complex logical problems. Cheapest smart model at $0.435/$0.87 per M tokens.' },
  { name: 'DeepSeek V4 Flash', role: 'Fast Router', context: '1M tokens', capabilities: ['Fast', 'Low Cost', 'Hybrid Attention'], desc: 'The fast router. 284B/13B MoE — handles trivial queries at 77x lower cost than Fable 5. 1M context with hybrid attention.' },
  { name: 'MiniMax M3', role: 'Vision + Generation', context: '1M tokens', capabilities: ['Vision', 'Creative', 'Tools', 'Best Hallucination Resist'], desc: 'The creative generator and vision specialist. Best GPQA (93%), best instruction following (83%), best hallucination resistance (84%).' },
  { name: 'Nemotron 3 Ultra', role: 'QA Gate (Free)', context: '1M tokens', capabilities: ['Evaluation', 'Agentic', 'FREE'], desc: 'The quality gate. Scores answers on 4 rubrics (USVA). 550B/55B MoE. Completely free — QA costs nothing.' },
];

export default function ModelsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Model Pool">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Model Pool</h1>
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

          <StaggerReveal className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {models.map((model, i) => (
              <StaggerItem key={i}>
                <div className="card h-full">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-text-primary">{model.name}</h3>
                    <span className="badge-muted">{model.role}</span>
                  </div>
                  <p className="text-sm text-text-secondary mb-4">{model.desc}</p>
                  <div className="flex flex-wrap gap-1.5 mb-4">{model.capabilities.map((cap, j) => <span key={j} className="badge-muted text-xs">{cap}</span>)}</div>
                  <div className="text-xs text-text-muted">Context: <span className="text-text-secondary">{model.context}</span></div>
                  <a href="/playground" className="btn-secondary w-full mt-4 text-xs">Try in Playground</a>
                </div>
              </StaggerItem>
            ))}
          </StaggerReveal>
        </div>
      </main>
    </>
  );
}

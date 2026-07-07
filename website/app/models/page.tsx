import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

const models = [
  { name: 'GLM-5.2', role: 'Orchestrator', context: '1M tokens', iq: '51', capabilities: ['Tools', 'Thinking', '1M Context'], desc: 'The primary orchestrator and fusion aggregator. Highest open-weight IQ (51). Routes queries, aggregates multi-model responses, handles general knowledge at lowest cost.' },
  { name: 'DeepSeek V4 Pro', role: 'Hard Reasoning', context: '1M tokens', iq: '44', capabilities: ['Math', 'Coding', '#1 Finance'], desc: 'The reasoning powerhouse. Best for hard math, coding, and complex logical problems. #1 in Finance on OpenRouter. Used only when needed.' },
  { name: 'Hy3 Preview', role: 'Trivial Router', context: '262K tokens', iq: '—', capabilities: ['Cheapest', '#6 Academia', 'Agentic'], desc: 'The cheapest model on OpenRouter ($0.063/$0.21). Handles 60% of queries — trivial questions routed here for maximum cost efficiency.' },
  { name: 'Gemini 3 Flash', role: 'Legal/Health Specialist', context: '1M tokens', iq: '50', capabilities: ['#1 Legal', '#2 Health', 'Multimodal'], desc: 'Google near-Pro reasoning model. #1 in Legal, #2 in Health. Multimodal (text+image+audio+video+PDF). IQ 50 — nearly matches GLM-5.2.' },
  { name: 'MiniMax M3', role: 'Vision + Creative', context: '1M tokens', iq: '44', capabilities: ['Vision', 'Creative', 'Best Hallucination Resist'], desc: 'The creative generator and vision specialist. Best GPQA (93%), best instruction following (83%), best hallucination resistance (84%).' },
  { name: 'MiMo-V2.5', role: 'Multimodal', context: '1M tokens', iq: '40', capabilities: ['Vision', 'Image', 'Video', 'Omnimodal'], desc: 'Native omnimodal model from Xiaomi. Processes text, images, and video. Pro-level agentic performance at half the cost.' },
  { name: 'Claude Sonnet 5', role: 'Frontier Fallback', context: '1M tokens', iq: '53', capabilities: ['IQ 53', 'Frontier', 'Coding', 'Adaptive'], desc: 'The frontier model for the hardest 2% of queries. IQ 53 — highest in our pool. Used only when fusion + verification + QA all score low.' },
  { name: 'Nemotron 3 Ultra', role: 'QA Gate (Free)', context: '128K tokens', iq: '38', capabilities: ['Evaluation', '550B MoE', 'FREE'], desc: 'The quality gate. Scores answers on 5 rubrics (USVA). 550B/55B hybrid MoE. Completely free — QA and verification costs nothing.' },
];

export default function ModelsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Model Pool">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Model Pool</h1>
          <p className="text-text-secondary mb-8 max-w-2xl">
            8 frontier models, each with a specific role. TemuClaude routes to the best model
            for your question automatically — you never have to choose.
          </p>

          <StaggerReveal className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {models.map((model, i) => (
              <StaggerItem key={i}>
                <div className="card h-full">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-text-primary">{model.name}</h3>
                    <div className="flex items-center gap-2">
                      {model.iq !== '—' && (
                        <span className="text-xs font-mono text-text-muted">IQ {model.iq}</span>
                      )}
                      <span className="badge-muted">{model.role}</span>
                    </div>
                  </div>
                  <p className="text-sm text-text-secondary mb-4">{model.desc}</p>
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {model.capabilities.map((cap, j) => (
                      <span key={j} className="badge-muted text-xs">{cap}</span>
                    ))}
                  </div>
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
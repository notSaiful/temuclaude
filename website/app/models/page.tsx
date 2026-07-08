import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

const models = [
  { name: 'GLM-5.2', role: 'Orchestrator', context: '1M tokens', iq: '51', capabilities: ['Tools', 'Thinking', '1M Context'], desc: 'The primary orchestrator and fusion aggregator. Highest open-weight IQ (51). Routes queries, aggregates multi-model responses, and handles general knowledge.' },
  { name: 'DeepSeek Pro', role: 'Hard Reasoning', context: '1M tokens', iq: '44', capabilities: ['Math', 'Coding', 'Reasoning'], desc: 'The reasoning powerhouse. Best for hard math, coding, and complex logical problems. Generates step-by-step reasoning hints.' },
  { name: 'Llama 3.3', role: 'Specialist', context: '131K tokens', iq: '40', capabilities: ['Open Weights', 'Logic', 'Agentic'], desc: 'High-quality 70B open-weights model. Acts as a core expert in the MoA proposal panels and generator in self-play.' },
  { name: 'Gemini 2.0 Flash', role: 'Worker/RAG', context: '1M tokens', iq: '40', capabilities: ['Multimodal', 'Speed', 'Search'], desc: 'Google next-gen utility model. High speed, multimodal vision capabilities, and deep real-time search integration.' },
  { name: 'Mistral Large 2', role: 'Logic Specialist', context: '131K tokens', iq: '43', capabilities: ['Multilingual', 'Structured', 'Logic'], desc: 'Mistral flagship model. Best for structured instruction compliance and serves as the critic/discriminator in self-play.' },
  { name: 'Claude 3.5 Sonnet', role: 'Frontier Fallback', context: '200K tokens', iq: '53', capabilities: ['Frontier', 'Coding', 'Ultimate'], desc: 'The frontier fallback for failing hard-tier queries. Used selectively when intermediate verifiers fail validation checks.' },
  { name: 'MiMo-V2.5', role: 'Multimodal', context: '1M tokens', iq: '40', capabilities: ['Vision', 'Image', 'Video'], desc: 'Xiaomi omnimodal model. Specialized for multimodal analysis, image-to-text, and video-based queries.' },
  { name: 'Z3 Solver', role: 'Logical Verifier', context: 'Local', iq: '—', capabilities: ['SMT', 'Logic', 'Zero-Error'], desc: 'Programmatic verifier that parses logical steps into SMT constraint formulas, verifying reasoning correctness.' },
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
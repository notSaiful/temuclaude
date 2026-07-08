import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

const models = [
  { name: 'GLM-5.2', role: 'Orchestrator', context: '1M tokens', iq: '51', capabilities: ['Tools', 'Thinking', '1M Context'], desc: 'The primary orchestrator and fusion aggregator. Highest open-weight IQ (51). Routes queries, aggregates multi-model responses, and handles general knowledge.' },
  { name: 'DeepSeek V4 Pro', role: 'Hard Reasoning', context: '1M tokens', iq: '44', capabilities: ['Math', 'Coding', 'Reasoning'], desc: 'The reasoning powerhouse. Best for hard math, coding, and complex logical problems. Generates step-by-step reasoning hints.' },
  { name: 'Llama 3.3', role: 'Specialist', context: '131K tokens', iq: '40', capabilities: ['Open Weights', 'Logic', 'Agentic'], desc: 'High-quality 70B open-weights model. Acts as a core expert in the MoA proposal panels and generator in self-play.' },
  { name: 'Gemini 2.5 Flash', role: 'Worker/RAG', context: '1M tokens', iq: '40', capabilities: ['Multimodal', 'Speed', 'Search'], desc: 'Google fast utility model. High speed, multimodal vision capabilities, and deep real-time search integration.' },
  { name: 'Mistral Large 3', role: 'Logic Specialist', context: '262K tokens', iq: '43', capabilities: ['Multilingual', 'Structured', 'Logic'], desc: 'Mistral flagship model. Best for structured instruction compliance and serves as the critic/discriminator in self-play.' },
  { name: 'Claude Sonnet 4.6', role: 'Frontier Fallback', context: '1M tokens', iq: '53', capabilities: ['Frontier', 'Coding', 'Ultimate'], desc: 'The frontier fallback for failing hard-tier queries. Used selectively when intermediate verifiers fail validation checks.' },
  { name: 'MiMo-V2.5', role: 'Multimodal', context: '1M tokens', iq: '40', capabilities: ['Vision', 'Image', 'Video'], desc: 'Xiaomi omnimodal model. Specialized for multimodal analysis, image-to-text, and video-based queries.' },
  { name: 'Z3 Solver', role: 'Logical Verifier', context: 'Local', iq: '—', capabilities: ['SMT', 'Logic', 'Zero-Error'], desc: 'Programmatic verifier that parses logical steps into SMT constraint formulas, verifying reasoning correctness.' },
];

const routerSignals = [
  { label: 'Search', value: 'DeepSeek V4 Pro', detail: 'Tree search and MCTS policy model' },
  { label: 'Code Verification', value: 'DeepSeek V4 Pro', detail: 'Generates executable checks for math and coding' },
  { label: 'QA / PRM', value: 'Nemotron 3 Ultra', detail: 'Default quality gate and process verifier' },
  { label: 'Consistency', value: 'Task aggregator', detail: 'Math/coding use DeepSeek; knowledge uses GLM' },
  { label: 'Budget State', value: 'Tracked', detail: 'Initial budget, remaining budget, spent tokens' },
  { label: 'Failure Labels', value: 'Tracked', detail: 'Timeouts, model errors, contradictions, failed verification' },
  { label: 'Step Recommendations', value: 'Telemetry gated', detail: 'Switches only after enough observed evidence' },
];

export default function ModelsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Model Pool">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Model Pool</h1>
          <p className="text-text-secondary mb-8 max-w-2xl">
            A role-specialized model pool plus a step-aware router. TemuClaude selects models for
            the task, then adapts high-value steps like search, verification, consistency, and QA
            gates from telemetry.
          </p>

          <div className="mb-10">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Step-Aware Router</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {routerSignals.map((signal, i) => (
                <div key={i} className="border border-border-subtle rounded-md p-4">
                  <div className="text-xs text-text-muted uppercase tracking-wide mb-1">{signal.label}</div>
                  <div className="text-sm font-semibold text-text-primary mb-1">{signal.value}</div>
                  <p className="text-xs text-text-secondary">{signal.detail}</p>
                </div>
              ))}
            </div>
          </div>

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

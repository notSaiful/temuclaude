import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

const models = [
  { name: 'DeepSeek V4 Flash', role: 'High-volume Worker', context: '1M tokens', iq: '40', capabilities: ['Drafting', 'Extraction', 'Tools'], desc: 'The low-cost default for routine steps. TemuClaude begins here whenever the confidence and risk policy permit.' },
  { name: 'DeepSeek V4 Pro', role: 'Reasoning Specialist', context: '1M tokens', iq: '44', capabilities: ['Math', 'Coding', 'Reasoning'], desc: 'The reasoning route for hard math, technical analysis, and code verification.' },
  { name: 'GLM-5.2', role: 'Planner + Aggregator', context: '1M tokens', iq: '51', capabilities: ['Planning', 'Thinking', 'Tools'], desc: 'The primary open-weight planner and synthesis model for long-horizon work.' },
  { name: 'MiniMax M3', role: 'Budget Multimodal', context: '1M tokens', iq: '44', capabilities: ['Vision', 'Video', 'Long Context'], desc: 'The low-cost multimodal route for screenshots, diagrams, video, and long context.' },
  { name: 'Gemini 3.5 Flash', role: 'Premium Multimodal', context: '1M tokens', iq: '—', capabilities: ['UI Control', 'Tools', 'Multimodal'], desc: 'Credential-gated specialist for high-value multimodal and tool-use work; never the blanket default.' },
  { name: 'GPT-5.6 Luna', role: 'Quality Escalation', context: 'Preview access', iq: '—', capabilities: ['Reasoning', 'Coding', 'Fallback'], desc: 'Used only after a hard answer fails QA and only when direct API access is configured.' },
  { name: 'Grok 4.5', role: 'Coding-Agent Escalation', context: 'Provider dependent', iq: '—', capabilities: ['Coding', 'Repair', 'Agents'], desc: 'Credential-gated repair specialist for difficult coding-agent work.' },
  { name: 'Nemotron 3 Ultra', role: 'Independent Verifier', context: '1M tokens', iq: '48', capabilities: ['Verification', 'Reasoning', 'Open Weights'], desc: 'A conditional independent critic and QA route, rather than a permanent ensemble member.' },
];

export default function ModelsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Model Pool">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Model Pool</h1>
          <p className="text-text-secondary mb-8 max-w-2xl">
            Eight active routing roles, selected per step rather than called as an always-on ensemble. Premium routes require explicit provider access and are promoted only after quality, cost, latency, and reliability evaluation.
          </p>

          <div className="mb-8 border border-border-subtle rounded-sm bg-bg-secondary/60 p-5 max-w-3xl">
            <h2 className="text-lg font-semibold text-text-primary mb-2">TemuClaude Lite profile</h2>
            <p className="text-sm text-text-secondary">The Playground Lite option is a separate cost-bounded cascade: DeepSeek V4 Flash by default, Qwen3 235B Thinking for hard reasoning, Qwen 3.7 Plus for multimodal and agentic work, and Nemotron 3 Ultra only for conditional independent verification.</p>
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
                </div>
              </StaggerItem>
            ))}
          </StaggerReveal>
        </div>
      </main>
    </>
  );
}

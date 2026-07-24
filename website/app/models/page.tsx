import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

const models = [
  { name: 'DeepSeek V4 Flash', role: 'Lite Worker', context: '1M tokens', iq: '—', capabilities: ['Drafting', 'Extraction', 'Tools'], desc: 'The explicit Lite and max-savings worker; it is not a silent Pro downgrade.' },
  { name: 'DeepSeek V4 Pro', role: 'Reasoning Specialist', context: '1M tokens', iq: '44', capabilities: ['Math', 'Coding', 'Reasoning'], desc: 'The reasoning route for hard math, technical analysis, and code verification.' },
  { name: 'GLM-5.2', role: 'Planner + Aggregator', context: '1M tokens', iq: '51', capabilities: ['Planning', 'Thinking', 'Tools'], desc: 'The primary open-weight planner and synthesis model for long-horizon work.' },
  { name: 'Kimi K2.6', role: 'UI/UX Implementation', context: '262K tokens', iq: '—', capabilities: ['UI/UX Code', 'Multimodal', 'Multi-Agent'], desc: 'Coding-driven UI/UX generation, interaction state, and multi-agent implementation specialist.' },
  { name: 'MiniMax M3', role: 'Multimodal + Long Context', context: '1M tokens', iq: '—', capabilities: ['Vision', 'Video', 'Long Context'], desc: 'Image/video understanding, creative product review, and long-context consistency.' },
  { name: 'Gemini 3.5 Flash', role: 'Visual UI Reviewer', context: '1M tokens', iq: '—', capabilities: ['UI Control', 'Accessibility', 'Tools'], desc: 'Visual interaction, accessibility, multimodal, and tool-use reviewer.' },
  { name: 'GPT-5.6 Luna', role: 'Fast GPT Worker', context: '1.05M tokens', iq: '—', capabilities: ['Independent Draft', 'Tools', 'Long Context'], desc: 'A fast independent GPT-family proposal path that adds diversity without being mislabeled as the frontier tier.' },
  { name: 'GPT-5.6 Sol', role: 'Frontier Adjudicator', context: '1.05M tokens', iq: '—', capabilities: ['Reasoning', 'Coding', 'Professional Work'], desc: 'The GPT-5.6 frontier tier for complex professional work and corrective adjudication.' },
  { name: 'Grok 4.5', role: 'Coding-Agent Escalation', context: 'Provider dependent', iq: '—', capabilities: ['Coding', 'Repair', 'Agents'], desc: 'Credential-gated repair specialist for difficult coding-agent work.' },
  { name: 'Nemotron 3 Ultra', role: 'Independent Verifier', context: '1M tokens', iq: '—', capabilities: ['Verification', 'Reasoning', 'Open Weights'], desc: 'The independent critic and QA route for nontrivial Pro and Lite work.' },
];

export default function ModelsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Model Pool">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Model Pool</h1>
          <p className="text-text-secondary mb-8 max-w-2xl">
            Nine maximum-quality roles: eight complementary specialists and an independent verifier. Artifact work runs the advisory specialists in bounded batches, then synthesizes and verifies the result.
          </p>

          <div className="mb-8 border border-border-subtle rounded-sm bg-bg-secondary/60 p-5 max-w-3xl">
            <h2 className="text-lg font-semibold text-text-primary mb-2">TemuClaude Lite profile</h2>
            <p className="text-sm text-text-secondary">TemuClaude Lite uses parallel DeepSeek/Qwen drafts for nontrivial work, Qwen synthesis, and Nemotron verification, all inside its cost-bounded allowlist.</p>
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

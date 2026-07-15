export const MODEL_IDS = {
  flash: 'deepseek/deepseek-v4-flash',
  reasoning: 'deepseek/deepseek-v4-pro',
  planner: 'z-ai/glm-5.2',
  creative: 'minimax/minimax-m3',
  multimodal: 'google/gemini-3.5-flash',
  qualityEscalation: 'openai/gpt-5.6-luna',
  emergencyEscalation: 'openai/gpt-5.6-terra',
  codeRepair: 'x-ai/grok-4.5',
  verifier: 'nvidia/nemotron-3-ultra-550b-a55b',
  liteReasoning: 'qwen/qwen3.7-plus',
} as const;

export const PUBLIC_API_MODELS = {
  default: 'temuclaude/temuclaude',
  pro: 'temuclaude/temuclaude-pro',
  lite: 'temuclaude/temuclaude-lite',
} as const;

export const PRO_MODEL_POOL = {
  orchestrator: MODEL_IDS.planner,
  reasoning: MODEL_IDS.reasoning,
  fastRoute: MODEL_IDS.flash,
  multimodal: MODEL_IDS.multimodal,
  specialist: MODEL_IDS.creative,
  vision: MODEL_IDS.creative,
  frontier: MODEL_IDS.qualityEscalation,
  codeRepair: MODEL_IDS.codeRepair,
  verifier: MODEL_IDS.verifier,
} as const;

export const LITE_MODEL_IDS = [
  MODEL_IDS.flash,
  MODEL_IDS.liteReasoning,
  MODEL_IDS.verifier,
] as const;

export type LiteModelId = (typeof LITE_MODEL_IDS)[number];

export const LITE_MODEL_POOL = {
  default: MODEL_IDS.flash,
  reasoning: MODEL_IDS.liteReasoning,
  agent: MODEL_IDS.liteReasoning,
  verifier: MODEL_IDS.verifier,
} satisfies Record<string, LiteModelId>;

export const MODEL_STRENGTHS: Record<string, { label: string; best: string[] }> = {
  [MODEL_IDS.planner]: { label: 'GLM-5.2', best: ['architecture', 'synthesis', 'judging', 'general-code', 'agentic'] },
  [MODEL_IDS.reasoning]: { label: 'DeepSeek V4 Pro', best: ['code', 'math', 'algorithms', 'logic-heavy'] },
  [MODEL_IDS.flash]: { label: 'DeepSeek V4 Flash', best: ['planning', 'fast-draft', 'cheap'] },
  [MODEL_IDS.multimodal]: { label: 'Gemini 3.5 Flash', best: ['visual', 'layout', 'theme', 'ui-ux', 'multimodal'] },
  [MODEL_IDS.creative]: { label: 'MiniMax M3', best: ['creative', 'long-context', 'generalist'] },
  [MODEL_IDS.qualityEscalation]: { label: 'GPT-5.6 Luna', best: ['frontier', 'hardest-integration', 'complex-systems'] },
  [MODEL_IDS.codeRepair]: { label: 'Grok 4.5', best: ['debugging', 'repair'] },
  [MODEL_IDS.verifier]: { label: 'Nemotron 3 Ultra', best: ['verification', 'judging', 'scoring'] },
};

export const PUBLIC_MODEL_ROLES = [
  { id: MODEL_IDS.flash, name: 'DeepSeek V4 Flash', role: 'Routine work', description: 'The low-cost default for straightforward requests.' },
  { id: MODEL_IDS.reasoning, name: 'DeepSeek V4 Pro', role: 'Hard reasoning', description: 'Used for difficult math, code, and technical analysis.' },
  { id: MODEL_IDS.planner, name: 'GLM-5.2', role: 'Planning and synthesis', description: 'Used to plan longer work and combine useful findings.' },
  { id: MODEL_IDS.creative, name: 'MiniMax M3', role: 'Creative and long context', description: 'Used when creative work or long input is important.' },
  { id: MODEL_IDS.multimodal, name: 'Gemini 3.5 Flash', role: 'Images and tools', description: 'Used only when visual or tool capability is needed.' },
  { id: MODEL_IDS.qualityEscalation, name: 'GPT-5.6 Luna', role: 'Quality fallback', description: 'An optional fallback after a difficult response fails a check.' },
  { id: MODEL_IDS.codeRepair, name: 'Grok 4.5', role: 'Code repair', description: 'An optional specialist for difficult code repair.' },
  { id: MODEL_IDS.verifier, name: 'Nemotron 3 Ultra', role: 'Independent check', description: 'Reviews selected high-risk or difficult responses.' },
] as const;

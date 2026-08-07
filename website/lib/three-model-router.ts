export type RouteKind = 'general' | 'coding' | 'agentic' | 'repair';

export type ModelRoute = {
  kind: RouteKind;
  model: string;
  fallbacks: string[];
  system: string;
};

export const MODELS = {
  glm: 'z-ai/glm-5.2',
  kimi: 'moonshotai/kimi-k3',
  grok: 'x-ai/grok-4.5',
} as const;

const AGENTIC = /\b(agentic|autonomous|multi[ -]?agent|agent workflow|ai workflow|automate|automation|deploy(?:ment|ing)?|ci\/?cd|tool[ -]?use|orchestrat(?:e|ion)|execute(?:\s+the)?\s+(?:task|plan|workflow))\b/i;
const REPAIR = /\b(debug|fix|repair|regression|incident|vulnerabilit(?:y|ies)|security audit|review(?:\s+this)?\s+code|root cause|failing test|stack trace|refactor)\b/i;
const CODING = /\b(code|program|function|class|api|sdk|repository|codebase|typescript|javascript|python|rust|go|java|sql|html|css|react|next(?:\.js)?|component|build|implement|website|web ?app|script)\b/i;

/**
 * A deliberately small, explainable router. It makes exactly one model call
 * per request; the remaining two models are availability fallbacks only.
 */
export function routePrompt(prompt: string): ModelRoute {
  if (REPAIR.test(prompt)) {
    return {
      kind: 'repair',
      model: MODELS.grok,
      fallbacks: [MODELS.kimi, MODELS.glm],
      system: 'You are TemuClaude\'s code-review and repair specialist. Diagnose the concrete failure, propose the smallest reliable fix, and include tests or verification steps when useful.',
    };
  }
  if (AGENTIC.test(prompt) || CODING.test(prompt)) {
    return {
      kind: AGENTIC.test(prompt) ? 'agentic' : 'coding',
      model: MODELS.kimi,
      fallbacks: [MODELS.grok, MODELS.glm],
      system: 'You are TemuClaude\'s coding and agent-workflow specialist. Produce an actionable, complete result. For implementation requests, write production-ready code; for autonomous workflows, define concrete steps, tools, safeguards, and handoff criteria.',
    };
  }
  return {
    kind: 'general',
    model: MODELS.glm,
    fallbacks: [MODELS.kimi, MODELS.grok],
    system: 'You are TemuClaude\'s general reasoning and planning specialist. Give a precise, self-contained answer, prioritizing correctness, clear tradeoffs, and practical next actions.',
  };
}

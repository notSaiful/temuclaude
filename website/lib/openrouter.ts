export type ChatMessage = {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  name?: string;
  tool_call_id?: string;
};

export type OpenRouterResult = {
  success: boolean;
  content: string;
  tokens: number;
  model: string;
  provider: 'openrouter';
  attemptedModels: string[];
  status?: number;
  error?: string;
};

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';
const APPROVED_MODELS = new Set([
  'moonshotai/kimi-k3',
  'z-ai/glm-5.2',
  'x-ai/grok-4.5',
]);

function unique(models: string[]): string[] {
  return Array.from(new Set(models.filter((model) => APPROVED_MODELS.has(model))));
}

function extractContent(data: any): string {
  const content = data?.choices?.[0]?.message?.content;
  if (typeof content === 'string') return content.trim();
  if (Array.isArray(content)) return content.map((part) => typeof part === 'string' ? part : part?.text || '').join('').trim();
  return '';
}

/** Calls only TemuClaude's approved three-model pool. */
export async function callOpenRouter(
  model: string,
  messages: ChatMessage[],
  options: { temperature?: number; maxTokens?: number; timeoutMs?: number; fallbacks?: string[]; sessionId?: string } = {},
): Promise<OpenRouterResult> {
  const models = unique([model, ...(options.fallbacks || [])]);
  const key = process.env.OPENROUTER_API_KEY || '';
  if (!key || models.length === 0) {
    return { success: false, content: '', tokens: 0, model, provider: 'openrouter', attemptedModels: models, error: !key ? 'OPENROUTER_API_KEY is not configured' : 'Requested model is not approved' };
  }

  let lastError = 'No approved model returned a completion';
  let lastStatus: number | undefined;
  for (const candidate of models) {
    try {
      const response = await fetch(OPENROUTER_URL, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${key}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': process.env.NEXT_PUBLIC_APP_URL || 'https://temuclaude.com',
          'X-OpenRouter-Title': 'TemuClaude',
          ...(options.sessionId ? { 'X-Session-Id': options.sessionId.slice(0, 256) } : {}),
        },
        body: JSON.stringify({
          model: candidate,
          messages,
          temperature: options.temperature ?? 0.4,
          max_tokens: Math.max(64, options.maxTokens ?? 2048),
          stream: false,
          provider: { allow_fallbacks: true, sort: 'throughput' },
        }),
        signal: AbortSignal.timeout(options.timeoutMs ?? 60_000),
      });
      const data = await response.json().catch(() => ({}));
      lastStatus = response.status;
      if (!response.ok) {
        lastError = data?.error?.message || response.statusText;
        continue;
      }
      const actualModel = typeof data?.model === 'string' ? data.model : candidate;
      if (!APPROVED_MODELS.has(actualModel) && !actualModel.startsWith(`${candidate}-`)) {
        lastError = `OpenRouter returned an unapproved model: ${actualModel}`;
        continue;
      }
      const content = extractContent(data);
      if (!content) {
        lastError = 'OpenRouter returned an empty completion';
        continue;
      }
      return {
        success: true,
        content,
        tokens: Number(data?.usage?.completion_tokens || 0),
        model: actualModel,
        provider: 'openrouter',
        attemptedModels: models.slice(0, models.indexOf(candidate) + 1),
      };
    } catch (error) {
      lastError = error instanceof Error ? error.message : 'OpenRouter request failed';
    }
  }
  return { success: false, content: '', tokens: 0, model, provider: 'openrouter', attemptedModels: models, status: lastStatus, error: lastError };
}

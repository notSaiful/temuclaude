import { isApprovedOpenRouterModel, type ChatMessage } from '@/lib/openrouter';
import { LITE_MODEL_IDS, type LiteModelId } from '@/lib/model-catalog';

export { LITE_MODEL_IDS };
export type { LiteModelId };

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

export type LiteOpenRouterResult = {
  success: boolean;
  content: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  /** Provider-reported successful request cost, when available. */
  cost?: number;
  status?: number;
  error?: string;
};

const LITE_MODEL_ALLOWLIST = new Set<string>(LITE_MODEL_IDS);
const MAX_LITE_INPUT_TOKENS = 240_000;

function appUrl(): string {
  return process.env.NEXT_PUBLIC_APP_URL || 'https://temuclaude.com';
}

function extractText(message: unknown): string {
  if (!message || typeof message !== 'object') return '';
  const record = message as Record<string, unknown>;
  if (typeof record.content === 'string') return record.content.trim();
  if (Array.isArray(record.content)) {
    return record.content
      .map((part) => {
        if (typeof part === 'string') return part;
        if (!part || typeof part !== 'object') return '';
        const candidate = part as Record<string, unknown>;
        return typeof candidate.text === 'string' ? candidate.text : '';
      })
      .join('')
      .trim();
  }
  return '';
}

/**
 * Calls exactly one Lite model. OpenRouter may fail over between providers
 * serving the same model, but it cannot substitute a Pro or free-route model.
 */
export async function callOpenRouterLite(
  model: LiteModelId,
  messages: ChatMessage[],
  options: { temperature?: number; maxTokens?: number; timeoutMs?: number; sessionId?: string } = {},
): Promise<LiteOpenRouterResult> {
  if (!LITE_MODEL_ALLOWLIST.has(model)) {
    return {
      success: false,
      content: '',
      model,
      promptTokens: 0,
      completionTokens: 0,
      error: 'Model is not allowed in the TemuClaude Lite profile',
    };
  }

  // Keep both Playground and the OpenAI-compatible endpoint within the
  // smallest approved Lite context window, before a provider request is made.
  const estimatedInputTokens = messages.reduce(
    (total, message) => total + Math.ceil(String(message.content || '').length / 4),
    0,
  );
  if (estimatedInputTokens > MAX_LITE_INPUT_TOKENS) {
    return {
      success: false,
      content: '',
      model,
      promptTokens: 0,
      completionTokens: 0,
      error: `TemuClaude Lite supports up to ${MAX_LITE_INPUT_TOKENS.toLocaleString()} input tokens`,
    };
  }

  const key = process.env.OPENROUTER_API_KEY || '';
  if (!key) {
    return {
      success: false,
      content: '',
      model,
      promptTokens: 0,
      completionTokens: 0,
      error: 'OPENROUTER_API_KEY is not configured',
    };
  }

  try {
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': appUrl(),
        'X-OpenRouter-Title': 'TemuClaude Lite',
        ...(options.sessionId ? { 'x-session-id': options.sessionId.slice(0, 256) } : {}),
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: options.temperature ?? 0.45,
        max_tokens: Math.max(16, Math.min(options.maxTokens ?? 2000, 4096)),
        provider: {
          allow_fallbacks: true,
          require_parameters: true,
        },
        stream: false,
        ...(options.sessionId ? { session_id: options.sessionId.slice(0, 256) } : {}),
      }),
      signal: AbortSignal.timeout(Math.min(options.timeoutMs ?? 12_000, 20_000)),
    });

    const data = await response.json().catch(() => ({}));
    const content = extractText(data?.choices?.[0]?.message);
    const usage = data?.usage || {};
    const actualModel = typeof data?.model === 'string' ? data.model : model;

    if (!response.ok || !content || !isApprovedOpenRouterModel(model, actualModel)) {
      return {
        success: false,
        content: '',
        model: actualModel,
        promptTokens: Number(usage.prompt_tokens) || 0,
        completionTokens: Number(usage.completion_tokens) || 0,
        cost: Number(usage.cost) || 0,
        status: response.status,
        error: !isApprovedOpenRouterModel(model, actualModel)
          ? `OpenRouter returned unapproved model ${actualModel} for TemuClaude Lite`
          : data?.error?.message || data?.message || (content ? response.statusText : 'OpenRouter returned an empty message'),
      };
    }

    return {
      success: true,
      content,
      model: actualModel,
      promptTokens: Number(usage.prompt_tokens) || 0,
      completionTokens: Number(usage.completion_tokens) || 0,
      cost: Number(usage.cost) || 0,
    };
  } catch (error) {
    return {
      success: false,
      content: '',
      model,
      promptTokens: 0,
      completionTokens: 0,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

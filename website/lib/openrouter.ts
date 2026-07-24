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
  provider: 'openrouter' | 'aiml' | 'groq' | 'deepinfra';
  attemptedModels: string[];
  /** Provider-reported successful request cost, when OpenRouter returns it. */
  cost?: number;
  status?: number;
  error?: string;
};

export const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

const AIML_URL = 'https://api.aimlapi.com/v1/chat/completions';
const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const DEEPINFRA_URL = 'https://api.deepinfra.com/v1/openai/chat/completions';

const OPENROUTER_ROLE_FALLBACKS: Record<string, string[]> = {
  'deepseek/deepseek-v4-flash': ['z-ai/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'deepseek/deepseek-v4-pro': ['z-ai/glm-5.2', 'deepseek/deepseek-v4-flash'],
  'z-ai/glm-5.2': ['deepseek/deepseek-v4-pro', 'deepseek/deepseek-v4-flash'],
  'minimax/minimax-m3': ['z-ai/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'moonshotai/kimi-k2.6': ['deepseek/deepseek-v4-pro', 'z-ai/glm-5.2'],
  'google/gemini-3.5-flash': ['minimax/minimax-m3', 'z-ai/glm-5.2'],
  'openai/gpt-5.6-luna': ['deepseek/deepseek-v4-pro', 'z-ai/glm-5.2'],
  'openai/gpt-5.6-sol': ['x-ai/grok-4.5', 'deepseek/deepseek-v4-pro', 'z-ai/glm-5.2'],
  'x-ai/grok-4.5': ['openai/gpt-5.6-sol', 'deepseek/deepseek-v4-pro', 'z-ai/glm-5.2'],
  'openai/gpt-5.6-terra': ['openai/gpt-5.6-sol', 'x-ai/grok-4.5', 'deepseek/deepseek-v4-pro'],
  'google/gemini-2.0-flash': ['google/gemini-2.5-flash', 'google/gemini-3-flash-preview', 'z-ai/glm-5.2'],
  'google/gemini-2.5-flash': ['google/gemini-3-flash-preview', 'z-ai/glm-5.2'],
  'mistralai/mistral-large-2': ['mistralai/mistral-large-2512', 'minimax/minimax-m3', 'deepseek/deepseek-v4-pro'],
  'mistralai/mistral-large-2512': ['minimax/minimax-m3', 'deepseek/deepseek-v4-pro'],
  'anthropic/claude-3.5-sonnet': ['anthropic/claude-sonnet-4.6', 'anthropic/claude-sonnet-4', 'z-ai/glm-5.2'],
  'anthropic/claude-sonnet-4.6': ['anthropic/claude-sonnet-4', 'z-ai/glm-5.2'],
  'nvidia/nemotron-3-ultra-550b-a55b:free': [
    'nvidia/nemotron-3-super-120b-a12b:free',
    'openai/gpt-oss-120b:free',
    'z-ai/glm-5.2',
  ],
  'meta-llama/llama-3.3-70b-instruct': [
    'meta-llama/llama-3.3-70b-instruct:free',
    'tencent/hy3-preview',
    'openai/gpt-oss-120b:free',
  ],
};

const AIML_MODEL_MAP: Record<string, string[]> = {
  'z-ai/glm-5.2': ['zhipu/glm-5.2'],
  'deepseek/deepseek-v4-pro': ['deepseek/deepseek-v4-pro'],
  'deepseek/deepseek-v4-flash': ['deepseek/deepseek-v4-flash'],
  'minimax/minimax-m3': ['minimax/minimax-m3'],
  'moonshotai/kimi-k2.6': ['deepseek/deepseek-v4-pro', 'zhipu/glm-5.2'],
  'openai/gpt-oss-120b': ['openai/gpt-oss-120b'],
  'openai/gpt-oss-120b:free': ['openai/gpt-oss-120b'],
  'nvidia/nemotron-3-ultra-550b-a55b:free': [
    'nvidia/nemotron-3-nano-30b-a3b',
    'openai/gpt-oss-120b',
  ],
  'google/gemini-2.0-flash': ['zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'mistralai/mistral-large-2': ['minimax/minimax-m3', 'deepseek/deepseek-v4-pro'],
  'anthropic/claude-3.5-sonnet': ['zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'google/gemini-2.5-flash': ['zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'mistralai/mistral-large-2512': ['minimax/minimax-m3', 'deepseek/deepseek-v4-pro'],
  'anthropic/claude-sonnet-4.6': ['zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'google/gemini-3.5-flash': ['zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'openai/gpt-5.6-luna': ['zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'openai/gpt-5.6-sol': ['deepseek/deepseek-v4-pro', 'zhipu/glm-5.2'],
  'x-ai/grok-4.5': ['zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'openai/gpt-5.6-terra': ['zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
  'google/gemini-3-flash-preview': ['zhipu/glm-5.2'],
  'anthropic/claude-sonnet-5': ['anthropic/claude-sonnet-4.6', 'zhipu/glm-5.2', 'deepseek/deepseek-v4-pro'],
};

const GROQ_MODEL_MAP: Record<string, string[]> = {
  'meta-llama/llama-3.3-70b-instruct': ['llama-3.3-70b-versatile'],
  'meta-llama/llama-3.3-70b-instruct:free': ['llama-3.3-70b-versatile'],
  'openai/gpt-oss-120b': ['openai/gpt-oss-120b'],
  'openai/gpt-oss-120b:free': ['openai/gpt-oss-120b'],
  'google/gemini-2.0-flash': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'mistralai/mistral-large-2': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'anthropic/claude-3.5-sonnet': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'google/gemini-2.5-flash': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'mistralai/mistral-large-2512': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'anthropic/claude-sonnet-4.6': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'google/gemini-3.5-flash': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'openai/gpt-5.6-luna': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'x-ai/grok-4.5': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'openai/gpt-5.6-terra': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'nvidia/nemotron-3-ultra-550b-a55b:free': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'nvidia/nemotron-3-super-120b-a12b:free': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'openrouter/free': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
  'openrouter/auto': ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
};

const DEEPINFRA_MODEL_MAP: Record<string, string[]> = {
  'meta-llama/llama-3.3-70b-instruct': ['meta-llama/Llama-3.3-70B-Instruct-Turbo'],
  'meta-llama/llama-3.3-70b-instruct:free': ['meta-llama/Llama-3.3-70B-Instruct-Turbo'],
  'google/gemini-2.0-flash': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'mistralai/mistral-large-2': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'anthropic/claude-3.5-sonnet': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'google/gemini-2.5-flash': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'mistralai/mistral-large-2512': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'anthropic/claude-sonnet-4.6': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'google/gemini-3.5-flash': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'openai/gpt-5.6-luna': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'x-ai/grok-4.5': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'openai/gpt-5.6-terra': ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'deepseek-ai/DeepSeek-V3'],
  'nvidia/nemotron-3-ultra-550b-a55b:free': ['meta-llama/Llama-3.3-70B-Instruct-Turbo'],
  'nvidia/nemotron-3-super-120b-a12b:free': ['meta-llama/Llama-3.3-70B-Instruct-Turbo'],
  'openai/gpt-oss-120b:free': ['meta-llama/Llama-3.3-70B-Instruct-Turbo'],
  'openrouter/free': ['meta-llama/Llama-3.3-70B-Instruct-Turbo'],
};

export function resolveOpenRouterModel(model: string): string {
  const replacements: Record<string, string> = {
    'google/gemini-2.0-flash': 'google/gemini-2.5-flash',
    'mistralai/mistral-large-2': 'mistralai/mistral-large-2512',
    'anthropic/claude-3.5-sonnet': 'anthropic/claude-sonnet-4.6',
    'anthropic/claude-sonnet-5': 'anthropic/claude-sonnet-4.6',
  };
  return replacements[model] || model;
}

function appUrl(): string {
  return process.env.NEXT_PUBLIC_APP_URL || 'https://temuclaude.com';
}

function aimlFallbackEnabled(): boolean {
  return ['1', 'true', 'yes', 'on'].includes((process.env.AIML_FALLBACK_ENABLED || '').toLowerCase());
}

function groqFallbackEnabled(): boolean {
  return ['1', 'true', 'yes', 'on'].includes((process.env.GROQ_FALLBACK_ENABLED || '').toLowerCase());
}

function deepinfraFallbackEnabled(): boolean {
  return ['1', 'true', 'yes', 'on'].includes((process.env.DEEPINFRA_FALLBACK_ENABLED || '').toLowerCase());
}

function extractText(message: any): string {
  const content = message?.content;
  if (typeof content === 'string' && content.trim()) return content.trim();
  if (Array.isArray(content)) {
    const text = content
      .map((part) => typeof part === 'string' ? part : part?.text || '')
      .join('');
    if (text.trim()) return text.trim();
  }
  // Reasoning traces are not user deliverables. Treating one as an answer
  // leaked incomplete thought and made a max-token exhaustion look successful.
  return '';
}

/**
 * OpenRouter can return a dated revision of a requested canonical model ID,
 * e.g. `deepseek/deepseek-v4-flash-20260423`. Treat only that exact dated
 * revision as equivalent; never accept a different family such as a free
 * router fallback.
 */
export function isApprovedOpenRouterModel(requested: string, actual: string): boolean {
  if (requested === actual) return true;
  const requestedParts = requested.split(':');
  const actualParts = actual.split(':');
  const requestedVariant = requestedParts.length > 1 ? requestedParts.slice(1).join(':') : '';
  const actualVariant = actualParts.length > 1 ? actualParts.slice(1).join(':') : '';
  if (requestedVariant !== actualVariant) return false;
  const requestedBase = requestedParts[0];
  const actualBase = actualParts[0];
  return actualBase.startsWith(`${requestedBase}-`) && /-\d{8}$/.test(actualBase);
}

async function postOpenRouter(
  model: string,
  messages: ChatMessage[],
  temperature: number,
  maxTokens: number,
  timeoutMs: number,
  sessionId?: string,
  modelFallbacks: string[] = [],
  disableReasoning = false,
  _strictQuality = true,
  responseFormat?: 'json_object',
): Promise<OpenRouterResult> {
  const key = process.env.OPENROUTER_API_KEY || '';
  const resolvedModel = resolveOpenRouterModel(model);
  const models = uniqueModels(modelFallbacks.map(resolveOpenRouterModel))
    .filter((fallback) => fallback !== resolvedModel);
  // GPT-5.6 endpoints expose reasoning controls but not `temperature`.
  // With require_parameters=true, sending temperature makes every otherwise
  // healthy Luna/Sol endpoint ineligible. Omit it whenever the approved
  // primary/fallback chain contains a fixed-sampling GPT-5.6 route.
  const fixedSampling = [resolvedModel, ...models]
    .some((candidate) => candidate.startsWith('openai/gpt-5.6-'));

  if (!key) {
    return {
      success: false,
      content: '',
      tokens: 0,
      model: resolvedModel,
      provider: 'openrouter',
      attemptedModels: [resolvedModel],
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
        'X-OpenRouter-Title': 'TemuClaude',
        'X-OpenRouter-Metadata': 'enabled',
        ...(sessionId ? { 'x-session-id': sessionId.slice(0, 256) } : {}),
      },
      body: JSON.stringify({
        model: resolvedModel,
        ...(models.length ? { models } : {}),
        messages,
        ...(!fixedSampling ? { temperature } : {}),
        // `max_completion_tokens` is not supported by every OpenRouter
        // endpoint. Requiring it made valid approved models look unavailable.
        max_tokens: Math.max(16, maxTokens),
        provider: {
          // A role gets one OpenRouter-managed provider/model recovery path.
          // Layering local candidate loops on top of this turned one panel role
          // into several simultaneous provider calls and caused avoidable 429s.
          allow_fallbacks: true,
          // Structured requests need strict parameter support; ordinary text
          // roles should retain the widest healthy provider pool.
          ...(responseFormat ? { require_parameters: true } : {}),
          // Prefer responsive quality endpoints without excluding a model just
          // because the provider does not advertise a particular quantization.
          sort: 'throughput',
        },
        ...(disableReasoning ? { reasoning: { enabled: false, exclude: true } } : {}),
        ...(responseFormat ? { response_format: { type: responseFormat } } : {}),
        stream: false,
        ...(sessionId ? { session_id: sessionId.slice(0, 256) } : {}),
      }),
      signal: AbortSignal.timeout(timeoutMs),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = data?.error?.message || data?.message || response.statusText;
      return {
        success: false,
        content: '',
        tokens: 0,
        model: resolvedModel,
        provider: 'openrouter',
        attemptedModels: [resolvedModel],
        status: response.status,
        error: message,
      };
    }

    const content = extractText(data?.choices?.[0]?.message);
    const actualModel = typeof data?.model === 'string' ? data.model : resolvedModel;
    const cost = Number(data?.usage?.cost) || 0;
    if (!isApprovedOpenRouterModel(resolvedModel, actualModel) && !models.some((allowed) => isApprovedOpenRouterModel(allowed, actualModel))) {
      return {
        success: false,
        content: '',
        tokens: data?.usage?.total_tokens || 0,
        cost,
        model: actualModel,
        provider: 'openrouter',
        attemptedModels: [resolvedModel],
        error: `OpenRouter returned unapproved model ${actualModel} for requested model ${resolvedModel}`,
      };
    }
    return {
      success: !!content,
      content,
      tokens: data?.usage?.total_tokens || 0,
      cost,
      model: actualModel,
      provider: 'openrouter',
      attemptedModels: [resolvedModel],
      error: content ? undefined : 'OpenRouter returned an empty message',
    };
  } catch (error) {
    return {
      success: false,
      content: '',
      tokens: 0,
      model: resolvedModel,
      provider: 'openrouter',
      attemptedModels: [resolvedModel],
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function postAiml(
  model: string,
  messages: ChatMessage[],
  temperature: number,
  maxTokens: number,
  timeoutMs: number,
): Promise<OpenRouterResult> {
  const key = process.env.AIML_API_KEY || '';

  if (!key) {
    return {
      success: false,
      content: '',
      tokens: 0,
      model,
      provider: 'aiml',
      attemptedModels: [model],
      error: 'AIML_API_KEY is not configured',
    };
  }

  try {
    const response = await fetch(AIML_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
        'User-Agent': 'TemuClaude/1.0',
      },
      body: JSON.stringify({
        model,
        messages,
        temperature,
        max_tokens: Math.max(16, maxTokens),
        stream: false,
      }),
      signal: AbortSignal.timeout(timeoutMs),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      return {
        success: false,
        content: '',
        tokens: 0,
        model,
        provider: 'aiml',
        attemptedModels: [model],
        status: response.status,
        error: data?.error?.message || data?.message || response.statusText,
      };
    }

    const content = extractText(data?.choices?.[0]?.message);
    return {
      success: !!content,
      content,
      tokens: data?.usage?.total_tokens || 0,
      model: data?.model || model,
      provider: 'aiml',
      attemptedModels: [model],
      error: content ? undefined : 'AIML returned an empty message',
    };
  } catch (error) {
    return {
      success: false,
      content: '',
      tokens: 0,
      model,
      provider: 'aiml',
      attemptedModels: [model],
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function postCompatibleProvider(
  provider: 'groq' | 'deepinfra',
  url: string,
  key: string,
  model: string,
  messages: ChatMessage[],
  temperature: number,
  maxTokens: number,
  timeoutMs: number,
): Promise<OpenRouterResult> {
  if (!key) {
    return {
      success: false,
      content: '',
      tokens: 0,
      model,
      provider,
      attemptedModels: [model],
      error: `${provider.toUpperCase()} API key is not configured`,
    };
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
        'User-Agent': 'TemuClaude/1.0',
      },
      body: JSON.stringify({
        model,
        messages,
        temperature,
        max_tokens: Math.max(16, maxTokens),
        stream: false,
      }),
      signal: AbortSignal.timeout(timeoutMs),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      return {
        success: false,
        content: '',
        tokens: 0,
        model,
        provider,
        attemptedModels: [model],
        status: response.status,
        error: data?.error?.message || data?.message || response.statusText,
      };
    }

    const content = extractText(data?.choices?.[0]?.message);
    return {
      success: !!content,
      content,
      tokens: data?.usage?.total_tokens || 0,
      model: data?.model || model,
      provider,
      attemptedModels: [model],
      error: content ? undefined : `${provider} returned an empty message`,
    };
  } catch (error) {
    return {
      success: false,
      content: '',
      tokens: 0,
      model,
      provider,
      attemptedModels: [model],
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

function uniqueModels(models: string[]): string[] {
  const seen = new Set<string>();
  return models.filter((model) => {
    if (!model || seen.has(model)) return false;
    seen.add(model);
    return true;
  });
}

function getOpenRouterFallbacks(model: string, explicitFallbacks?: string[]): string[] {
  // Model fallbacks are a product policy, not an OpenRouter price decision.
  // Every role has an allowlisted, capability-compatible recovery chain so an
  // empty completion or transient provider outage cannot turn into a raw user
  // error. Explicit call-site fallbacks take precedence for artifact delivery.
  const configured = explicitFallbacks && explicitFallbacks.length > 0
    ? explicitFallbacks
    : OPENROUTER_ROLE_FALLBACKS[model] || [];
  return uniqueModels(configured).filter((fallback) => fallback !== model);
}

function getAimlFallbacks(openRouterModels: string[]): string[] {
  return uniqueModels(openRouterModels.flatMap((model) => AIML_MODEL_MAP[model] || []));
}

function getMappedFallbacks(openRouterModels: string[], modelMap: Record<string, string[]>): string[] {
  return uniqueModels(openRouterModels.flatMap((model) => modelMap[model] || []));
}

export async function callOpenRouter(
  model: string,
  messages: ChatMessage[],
  options: {
    temperature?: number;
    maxTokens?: number;
    timeoutMs?: number;
    fallbacks?: string[];
    sessionId?: string;
    /**
     * Cross-provider/model transports are intentionally opt-in. Production
     * Pro/Lite routes use only explicit, profile-approved model fallbacks.
     */
    allowExternalFallbacks?: boolean;
    /** Code deliverables need output tokens, not an exposed thinking trace. */
    disableReasoning?: boolean;
    /**
     * Opt-in JSON mode for structured calls (e.g. the request classifier).
     * Best-effort: models that don't support it ignore it and return text,
     * which the caller must parse with a fallback. No existing Pro/Lite caller
     * sets it; only the deliberation classifier uses JSON mode.
     */
    responseFormat?: 'json_object';
  } = {},
): Promise<OpenRouterResult> {
  const temperature = options.temperature ?? 0.6;
  const maxTokens = options.maxTokens ?? 4096;
  const timeoutMs = options.timeoutMs ?? 60000;
  // `timeoutMs` is the budget for the complete routed call, not for every
  // fallback independently. Reusing the full timeout for each candidate made
  // a three-model route take up to 3x its advertised limit and allowed Vercel
  // to terminate the Playground before it could return a response.
  const deadlineAt = Date.now() + Math.max(1, timeoutMs);
  const remainingTimeoutMs = () => Math.max(0, deadlineAt - Date.now());
  const openRouterModels = uniqueModels([
    resolveOpenRouterModel(model),
    ...getOpenRouterFallbacks(resolveOpenRouterModel(model), options.fallbacks).map(resolveOpenRouterModel),
  ]).slice(0, 2);
  const attemptedModels = [`openrouter:role:${openRouterModels.join(' -> ')}`];
  const attemptTimeoutMs = remainingTimeoutMs();
  const primary = openRouterModels[0];
  const result = attemptTimeoutMs < 250
    ? null
    : await postOpenRouter(
      primary,
      messages,
      temperature,
      maxTokens,
      attemptTimeoutMs,
      options.sessionId,
      openRouterModels.slice(1),
      options.disableReasoning,
      true,
      options.responseFormat,
    );
  if (result?.success) return { ...result, attemptedModels };
  let last: OpenRouterResult | null = result;

  if (options.allowExternalFallbacks && deepinfraFallbackEnabled()) {
    for (const candidate of getMappedFallbacks(openRouterModels, DEEPINFRA_MODEL_MAP)) {
      const attemptTimeoutMs = remainingTimeoutMs();
      if (attemptTimeoutMs < 250) break;
      attemptedModels.push(`deepinfra:${candidate}`);
      const result = await postCompatibleProvider(
        'deepinfra',
        DEEPINFRA_URL,
        process.env.DEEPINFRA_API_KEY || '',
        candidate,
        messages,
        temperature,
        maxTokens,
        attemptTimeoutMs,
      );
      if (result.success) {
        return { ...result, attemptedModels };
      }
      last = result;
    }
  }

  if (options.allowExternalFallbacks && groqFallbackEnabled()) {
    for (const candidate of getMappedFallbacks(openRouterModels, GROQ_MODEL_MAP)) {
      const attemptTimeoutMs = remainingTimeoutMs();
      if (attemptTimeoutMs < 250) break;
      attemptedModels.push(`groq:${candidate}`);
      const result = await postCompatibleProvider(
        'groq',
        GROQ_URL,
        process.env.GROQ_API_KEY || '',
        candidate,
        messages,
        temperature,
        maxTokens,
        attemptTimeoutMs,
      );
      if (result.success) {
        return { ...result, attemptedModels };
      }
      last = result;
    }
  }

  if (options.allowExternalFallbacks && aimlFallbackEnabled()) {
    for (const candidate of getAimlFallbacks(openRouterModels)) {
      const attemptTimeoutMs = remainingTimeoutMs();
      if (attemptTimeoutMs < 250) break;
      attemptedModels.push(`aiml:${candidate}`);
      const result = await postAiml(candidate, messages, temperature, maxTokens, attemptTimeoutMs);
      if (result.success) {
        return { ...result, attemptedModels };
      }
      last = result;
    }
  }

  return {
    ...(last || {
      success: false,
      content: '',
      tokens: 0,
      model: resolveOpenRouterModel(model),
      provider: 'openrouter' as const,
      error: attemptedModels.length > 0 ? 'Model routing deadline exhausted' : 'No providers were attempted',
    }),
    success: false,
    attemptedModels,
  };
}

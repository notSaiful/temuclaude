/** Live connection audit for every active TemuClaude Pro capability role. */

const models = [
  'z-ai/glm-5.2',
  'deepseek/deepseek-v4-pro',
  'moonshotai/kimi-k2.6',
  'minimax/minimax-m3',
  'google/gemini-3.5-flash',
  'openai/gpt-5.6-luna',
  'openai/gpt-5.6-sol',
  'x-ai/grok-4.5',
  'nvidia/nemotron-3-ultra-550b-a55b',
];

if (!process.env.OPENROUTER_API_KEY) {
  console.error('OPENROUTER_API_KEY is required.');
  process.exit(2);
}

function approved(requested, actual) {
  return actual === requested || (actual.startsWith(`${requested}-`) && /-\d{8}$/.test(actual));
}

async function attempt(model, strictQuality) {
  const fixedSampling = model.startsWith('openai/gpt-5.6-');
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': process.env.NEXT_PUBLIC_APP_URL || 'https://temuclaude.com',
      'X-OpenRouter-Title': 'TemuClaude model connection audit',
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: 'Reply with exactly OK.' }],
      ...(!fixedSampling ? { temperature: 0 } : {}),
      max_tokens: 256,
      provider: {
        allow_fallbacks: true,
        require_parameters: true,
        sort: 'throughput',
        ...(strictQuality ? { quantizations: ['bf16', 'fp16', 'fp8'] } : {}),
      },
      stream: false,
    }),
    signal: AbortSignal.timeout(90_000),
  });
  const data = await response.json().catch(() => ({}));
  const content = typeof data?.choices?.[0]?.message?.content === 'string'
    ? data.choices[0].message.content.trim()
    : '';
  return {
    ok: response.ok && approved(model, String(data?.model || '')) && content.length > 0,
    status: response.status,
    actualModel: typeof data?.model === 'string' ? data.model : null,
    hasContent: content.length > 0,
    promptTokens: Number(data?.usage?.prompt_tokens) || 0,
    completionTokens: Number(data?.usage?.completion_tokens) || 0,
    costUsd: Number(data?.usage?.cost) || 0,
    error: data?.error?.message || null,
  };
}

async function audit(model) {
  let result = await attempt(model, true);
  let relaxedPrecisionRetry = false;
  if (!result.ok && result.status !== 401 && result.status !== 403) {
    relaxedPrecisionRetry = true;
    result = await attempt(model, false);
  }
  return { model, relaxedPrecisionRetry, ...result };
}

const results = await Promise.all(models.map(audit));
console.log(JSON.stringify(results, null, 2));
if (results.some((result) => !result.ok)) process.exitCode = 1;

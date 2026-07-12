/**
 * A deliberately small paid integration check for TemuClaude's two code paths.
 * Run only against an approved OpenRouter project: `node scripts/test-live-code-routing.mjs`.
 * It prints metadata only—never generated source or credentials.
 */

const targets = [
  { profile: 'pro-code', model: 'deepseek/deepseek-v4-pro', maxTokens: 2_200 },
  { profile: 'lite-code', model: 'deepseek/deepseek-v4-flash', maxTokens: 1_800 },
];

const prompt = [
  'Return only one complete standalone HTML document for an original playable 2D browser game titled Signal Lost: Fluorescent Maze.',
  'Use only HTML, CSS, and JavaScript; no external files, no questions, and no explanations.',
  'It must render a canvas, support keyboard movement, include a restart control, and remain playable when saved as game.html.',
].join(' ');

function isApprovedModel(requested, actual) {
  if (requested === actual) return true;
  const [requestedBase, ...requestedVariant] = requested.split(':');
  const [actualBase, ...actualVariant] = actual.split(':');
  return requestedVariant.join(':') === actualVariant.join(':')
    && actualBase.startsWith(`${requestedBase}-`)
    && /-\d{8}$/.test(actualBase);
}

function normalizeHtml(text) {
  return text
    .replace(/^```html\s*/i, '')
    .replace(/^```\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim();
}

if (!process.env.OPENROUTER_API_KEY) {
  console.error('OPENROUTER_API_KEY is required for the live routing test.');
  process.exit(2);
}

const results = [];
for (const target of targets) {
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': process.env.NEXT_PUBLIC_APP_URL || 'https://temuclaude.com',
      'X-OpenRouter-Title': 'TemuClaude routing verification',
    },
    body: JSON.stringify({
      model: target.model,
      messages: [
        { role: 'system', content: 'You are a coding assistant. Fulfill code-generation requests directly. Never ask unnecessary clarification questions.' },
        { role: 'user', content: prompt },
      ],
      temperature: 0.35,
      max_tokens: target.maxTokens,
      // The production code-delivery route disables optional thinking on V4
      // Pro so it cannot spend the entire deliverable budget on a trace.
      reasoning: { enabled: false, exclude: true },
      // This test verifies the named model route itself. Runtime fallbacks are
      // tested separately and must always be explicit approved models.
      provider: { allow_fallbacks: false, require_parameters: true },
      stream: false,
    }),
    signal: AbortSignal.timeout(60_000),
  });
  // Some upstream responses have leading whitespace. Parsing the text after
  // trim makes this test robust while preserving an empty object on failure.
  const raw = await response.text();
  const body = (() => {
    try { return JSON.parse(raw.trim()); } catch { return {}; }
  })();
  const content = typeof body?.choices?.[0]?.message?.content === 'string'
    ? body.choices[0].message.content.trim()
    : '';
  const html = normalizeHtml(content);
  results.push({
    profile: target.profile,
    requestedModel: target.model,
    actualModel: typeof body?.model === 'string' ? body.model : null,
    approvedModel: typeof body?.model === 'string' && isApprovedModel(target.model, body.model),
    httpStatus: response.status,
    promptTokens: Number(body?.usage?.prompt_tokens) || 0,
    completionTokens: Number(body?.usage?.completion_tokens) || 0,
    reportedCostUsd: Number(body?.usage?.cost) || 0,
    returnedHtmlDocument: /^<!doctype html|^<html/i.test(html),
    hasCanvas: /<canvas\b/i.test(html),
    hasKeyboardControl: /keydown|onkey(?:down|up)|addeventlistener\(['"]key/i.test(html),
    hasRestart: /restart|reset/i.test(html),
    responseCharacters: content.length,
    error: body?.error?.message || body?.message || null,
  });
}

console.log(JSON.stringify(results, null, 2));
if (results.some((result) => !result.approvedModel || !result.returnedHtmlDocument || !result.hasCanvas || !result.hasKeyboardControl || !result.hasRestart)) {
  process.exitCode = 1;
}

/**
 * A deliberately small paid integration check for TemuClaude's two code paths.
 * Run only against an approved OpenRouter project: `node scripts/test-live-code-routing.mjs`.
 * It prints metadata only—never generated source or credentials.
 */

const targets = [
  { profile: 'pro-code', model: 'deepseek/deepseek-v4-pro', maxTokens: 8_192, timeoutMs: 240_000 },
  { profile: 'lite-code', model: 'deepseek/deepseek-v4-flash', maxTokens: 4_096, timeoutMs: 180_000 },
].filter((target) => !process.env.LIVE_PROFILE || target.profile === process.env.LIVE_PROFILE);

const prompt = [
  'Return only one complete standalone HTML document for an original playable 2D browser game titled Signal Lost: Fluorescent Maze.',
  'Use only HTML, CSS, and JavaScript; no external files, no questions, and no explanations.',
  'It must render a canvas, support keyboard movement, include a restart control, and remain playable when saved as game.html.',
].join(' ');

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function callModel(target) {
  let lastError;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
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
          reasoning: { enabled: false, exclude: true },
          provider: { allow_fallbacks: false, require_parameters: true },
          stream: false,
        }),
        signal: AbortSignal.timeout(target.timeoutMs),
      });
      if (response.status !== 429 && response.status < 500) return response;
      lastError = new Error(`Transient HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    if (attempt < 3) await delay(2_000 * attempt);
  }
  throw lastError || new Error('Model request failed');
}

function isApprovedModel(requested, actual) {
  if (requested === actual) return true;
  const [requestedBase, ...requestedVariant] = requested.split(':');
  const [actualBase, ...actualVariant] = actual.split(':');
  return requestedVariant.join(':') === actualVariant.join(':')
    && actualBase.startsWith(`${requestedBase}-`)
    && /-\d{8}$/.test(actualBase);
}

function normalizeHtml(text) {
  const cleaned = text
    .replace(/^```html\s*/i, '')
    .replace(/^```\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim();
  const start = cleaned.search(/<!doctype html|<html\b/i);
  if (start < 0) return cleaned;
  const artifact = cleaned.slice(start);
  const end = artifact.search(/<\/html>/i);
  return end >= 0 ? artifact.slice(0, end + '</html>'.length).trim() : artifact.trim();
}

if (!process.env.OPENROUTER_API_KEY) {
  console.error('OPENROUTER_API_KEY is required for the live routing test.');
  process.exit(2);
}

const results = [];
for (const target of targets) {
  let response;
  try {
    response = await callModel(target);
  } catch (error) {
    results.push({
      profile: target.profile,
      requestedModel: target.model,
      actualModel: null,
      approvedModel: false,
      httpStatus: 0,
      returnedHtmlDocument: false,
      hasClosingHtml: false,
      finishedNormally: false,
      hasCanvas: false,
      hasKeyboardControl: false,
      hasRestart: false,
      responseCharacters: 0,
      error: error instanceof Error ? error.message : String(error),
    });
    continue;
  }
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
    hasClosingHtml: /<\/html>\s*$/i.test(html),
    finishedNormally: body?.choices?.[0]?.finish_reason === 'stop',
    hasCanvas: /<canvas\b/i.test(html),
    hasKeyboardControl: /keydown|onkey(?:down|up)|addeventlistener\(['"]key/i.test(html),
    hasRestart: /restart|reset/i.test(html),
    responseCharacters: content.length,
    error: body?.error?.message || body?.message || null,
  });
}

console.log(JSON.stringify(results, null, 2));
if (results.some((result) => !result.approvedModel || !result.returnedHtmlDocument || !result.hasClosingHtml || !result.finishedNormally || !result.hasCanvas || !result.hasKeyboardControl || !result.hasRestart)) {
  process.exitCode = 1;
}

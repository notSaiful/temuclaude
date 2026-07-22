import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, '..', '..');
const website = path.join(root, 'website');

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), 'utf8');
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertIncludes(file, needles) {
  const source = read(file);
  for (const needle of needles) {
    assert(source.includes(needle), `${file} is missing required production gate: ${needle}`);
  }
}

async function smokeChatCompletion() {
  const baseUrl = process.env.TEMUCLAUDE_SMOKE_URL?.replace(/\/+$/, '');
  const key = process.env.TEMUCLAUDE_SMOKE_KEY || process.env.TEMUCLAUDE_MASTER_KEY;
  if (!baseUrl || !key) {
    console.log('production-gates: skipped live smoke test (set TEMUCLAUDE_SMOKE_URL and TEMUCLAUDE_SMOKE_KEY).');
    return;
  }

  const response = await fetch(`${baseUrl}/v1/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'temuclaude',
      messages: [{ role: 'user', content: 'Reply with exactly OK.' }],
      temperature: 0,
      max_tokens: 64,
    }),
    signal: AbortSignal.timeout(120000),
  });

  const data = await response.json().catch(() => ({}));
  const content = data?.choices?.[0]?.message?.content;
  assert(response.ok, `live smoke test failed with HTTP ${response.status}: ${JSON.stringify(data).slice(0, 400)}`);
  assert(typeof content === 'string' && content.trim(), 'live smoke test returned an empty assistant message');
  console.log(`production-gates: live smoke test passed (${content.trim().slice(0, 80)})`);
}

assertIncludes('website/app/v1/chat/completions/route.ts', [
  'hasUsableContent',
  'finalRescue',
  'TemuClaude could not produce a non-empty completion',
  'Modal backend returned an empty completion',
  'finalContent',
  'temuclaude/temuclaude-lite',
  "TEMUCLAUDE_USE_MODAL_BACKEND === 'true'",
  "classifiedDifficulty === 'medium' ? 'hard'",
  'all nine Pro roles propose in parallel',
  'call(M_LUNA, messages, temp, maxTok)',
  'call(M_KIMI, messages, temp, maxTok)',
  'call(M_GEMINI, messages, temp, maxTok)',
  'call(M_GROK, messages, temp, maxTok)',
  'if (isCodeGen(text)) return LITE_DEFAULT',
  'Synthesize the strongest complete answer from two independent drafts',
]);

assertIncludes('website/app/api/chat/route.ts', [
  "profile must be either \"pro\" or \"lite\"",
  'runLiteStack',
  'runQualityCodeGeneration',
  'quality-first-code-panel',
  'quality-first-pro-panel',
  'deadlineAt = t0 + 180_000',
  'POOL.frontier',
  'POOL.codeRepair',
  'POOL.multimodal',
  'POOL.uiUx',
  'POOL.gptWorker',
  'reviewOrProposalInputs.length > 0 ? reviewOrProposalInputs : workingProposals',
  'formatProviderCost',
  'recordPlaygroundUsage',
  'disableReasoning: true',
  'lite-parallel-specialist-panel',
  'lite-specialist-synthesis',
]);

assertIncludes('website/lib/openrouter-lite.ts', [
  'LITE_MODEL_ALLOWLIST',
  'nvidia/nemotron-3-ultra-550b-a55b',
  'isApprovedOpenRouterModel(model, actualModel)',
  'OpenRouter returned unapproved model',
  "finishReason === 'length'",
  '120_000',
]);

assertIncludes('website/lib/openrouter.ts', [
  'return uniqueModels(explicitFallbacks || [])',
  'allowExternalFallbacks?: boolean',
  'isApprovedOpenRouterModel',
  'OpenRouter returned unapproved model',
  'Reasoning traces are not user deliverables',
  'disableReasoning',
  "sort: 'throughput'",
  "quantizations: ['bf16', 'fp16', 'fp8']",
  'openrouter:resilience:',
  'result.status !== 401 && result.status !== 403',
  'fixedSampling',
]);

assertIncludes('website/app/playground/page.tsx', [
  'id="model-profile"',
  'HTML deliverable',
  "anchor.download = 'temuclaude-game.html'",
  'Preview · sandboxed',
  'sandbox="allow-scripts"',
  'sandboxPreviewDocument',
  "connect-src 'none'",
  'Run isolated preview',
  'Download .html', // export control (was "Save to project", reworked 2026-07-13)
  'extractHtmlArtifact',
]);

assertIncludes('website/lib/e2b-preview.ts', [
  "from 'e2b'",
  'allowInternetAccess: false',
  "connect-src 'none'",
  'frame-ancestors https://temuclaude.com',
  'sandbox.kill()',
]);

assertIncludes('website/app/api/sandbox/preview/route.ts', [
  'getAuthenticatedSupabaseUser',
  'createIsolatedHtmlPreview',
  'HTML previews are limited to 1 MB',
]);

const navbarSource = read('website/components/Navbar.tsx');
assert(navbarSource.includes('const primaryNavItems'), 'Navbar must use one shared primary navigation list.');
assert((navbarSource.match(/label: 'Playground'/g) || []).length === 1, 'Navbar must render exactly one Playground link.');
assert(!navbarSource.includes('className="btn-primary"'), 'Navbar must not render a duplicate black Playground CTA.');
assert(navbarSource.includes("className={`nav-link ${pathname?.startsWith('/dashboard')"), 'Dashboard must use the shared header-link treatment.');
assert(navbarSource.includes('className="nav-link cursor-pointer border-0 bg-transparent p-0"'), 'Sign Out must use the shared header-link treatment.');
assert(fs.existsSync(path.join(website, 'app', 'login', 'page.tsx')), 'website/app/login/page.tsx is required to prevent header Sign In 404s.');
assert(fs.existsSync(path.join(website, 'app', 'health', 'route.ts')), 'website/app/health/route.ts is required for deployment health checks.');

assertIncludes('website/lib/db.ts', [
  'assertPersistentDbAvailable',
  'ALLOW_EPHEMERAL_DB',
  'Supabase admin credentials are required in production',
]);

assertIncludes('website/.env.example', ['ALLOW_EPHEMERAL_DB=false']);
assertIncludes('.env.example', ['ALLOW_EPHEMERAL_DB=false']);

assert(fs.existsSync(path.join(website, 'next.config.js')), 'website/next.config.js is missing');

await smokeChatCompletion();
console.log('production-gates: source guardrails passed.');

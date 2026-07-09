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
]);

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

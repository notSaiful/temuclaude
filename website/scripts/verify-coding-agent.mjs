import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = (process.env.TEMUCLAUDE_SMOKE_URL || 'http://localhost:3000').replace(/\/+$/, '');
const apiKey = process.env.TEMUCLAUDE_SMOKE_KEY || process.env.TEMUCLAUDE_MASTER_KEY;

if (!apiKey) {
  throw new Error('Set TEMUCLAUDE_SMOKE_KEY or TEMUCLAUDE_MASTER_KEY before running this live coding-agent verification.');
}

const prompt = `You are a coding agent. Build a single, complete, responsive HTML webpage for a fictional developer tool called DeployFlow. Include inline CSS and JavaScript, a hero, three feature cards, and a working "Show deployment status" button. Return only one <!doctype html> document.`;
const response = await fetch(`${baseUrl}/v1/chat/completions`, {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'temuclaude/temuclaude',
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.2,
    max_tokens: 4096,
  }),
  signal: AbortSignal.timeout(180_000),
});

const body = await response.json().catch(() => ({}));
if (!response.ok) throw new Error(`API request failed (${response.status}): ${JSON.stringify(body)}`);
const html = body?.choices?.[0]?.message?.content?.trim();
if (!/^<!doctype html/i.test(html || '') || !/<\/html>\s*$/i.test(html || '')) {
  throw new Error('Coding-agent response was not a complete HTML document.');
}

const outputPath = path.join(process.cwd(), '.tmp-temuclaude-agent-page.html');
await fs.writeFile(outputPath, html, 'utf8');
console.log(JSON.stringify({
  status: 'passed',
  route: response.headers.get('x-temuclaude-route'),
  selected_model: response.headers.get('x-temuclaude-model'),
  output_path: outputPath,
  bytes: Buffer.byteLength(html),
}));

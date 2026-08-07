import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const assert = (value, message) => { if (!value) throw new Error(message); };
const route = read('website/app/v1/chat/completions/route.ts');
const router = read('website/lib/three-model-router.ts');

assert(route.includes('temuclaude/temuclaude'), 'API model identifier is missing.');
assert(!route.includes('temuclaude-lite'), 'Lite must not be exposed by the API.');
for (const model of ['moonshotai/kimi-k3', 'z-ai/glm-5.2', 'x-ai/grok-4.5']) assert(router.includes(model), `Missing approved model: ${model}`);
assert(!fs.existsSync(path.join(root, 'website/app/playground')), 'Playground must not be present.');
console.log('production-gates: three-model API guardrails passed.');

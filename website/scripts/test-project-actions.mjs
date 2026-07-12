import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = await readFile(new URL('../lib/project-actions.ts', import.meta.url), 'utf8');
for (const needle of [
  'APPROVAL_REQUIRED',
  "'agent.run'",
  "'package.install'",
  "'deploy.preview'",
  "'deploy.production'",
  'expires_at <= timestamp',
  'Action must be approved before execution',
]) {
  assert(source.includes(needle), `missing approval guard: ${needle}`);
}
console.log(JSON.stringify({ approvalGuards: true }));

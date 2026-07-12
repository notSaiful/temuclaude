/** Paid integration check for the pinned project-preview template. */
import { Sandbox } from 'e2b';

const apiKey = process.env.E2B_API_KEY?.trim();
if (!apiKey) {
  console.error('E2B_API_KEY is required for the project-preview template test.');
  process.exit(2);
}

const root = '/home/user/project';
const sandbox = await Sandbox.create('temuclaude-project-preview:v1', {
  apiKey,
  secure: true,
  timeoutMs: 5 * 60 * 1000,
  lifecycle: { onTimeout: 'kill' },
  allowInternetAccess: false,
  network: { allowPublicTraffic: true, maskRequestHost: 'localhost:${PORT}' },
  envs: { PORT: '3000' },
  metadata: { product: 'temuclaude-playground', purpose: 'project-template-test' },
});

try {
  await sandbox.files.write(`${root}/index.html`, '<!doctype html><title>Project Preview</title><h1>Ready</h1>');
  await sandbox.commands.run(`node -e "require('node:http').createServer((_,res)=>res.end(require('node:fs').readFileSync('${root}/index.html'))).listen(3000,'0.0.0.0')"`, { background: true, cwd: root });
  const url = `https://${sandbox.getHost(3000)}`;
  let response;
  for (let attempt = 0; attempt < 6; attempt += 1) {
    response = await fetch(url, { signal: AbortSignal.timeout(10_000) }).catch(() => undefined);
    if (response?.ok) break;
    await new Promise((resolve) => setTimeout(resolve, 750));
  }
  if (!response) throw new Error('Project preview did not become reachable.');
  const html = await response.text();
  const result = { httpStatus: response.status, previewReady: response.ok && html.includes('Project Preview') };
  console.log(JSON.stringify(result));
  if (!result.previewReady) process.exitCode = 1;
} finally {
  await sandbox.kill().catch(() => undefined);
}

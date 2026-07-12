/**
 * Paid integration check for the future runnable-project sandbox path.
 * It starts an isolated Node service with no outbound internet or credentials,
 * checks both an HTML surface and a local API, then always destroys the VM.
 */
import { Sandbox } from 'e2b';

if (!process.env.E2B_API_KEY) {
  console.error('E2B_API_KEY is required for the Node workspace test.');
  process.exit(2);
}

const root = '/home/oai/share/temuclaude-node-workspace';
const server = `
import { createServer } from 'node:http';
const server = createServer((request, response) => {
  if (request.url === '/api/status') {
    response.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' });
    response.end(JSON.stringify({ ok: true, runtime: 'isolated-node' }));
    return;
  }
  response.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
  response.end('<!doctype html><title>TemuClaude Node Preview</title><main><h1>Preview ready</h1></main>');
});
server.listen(3000, '0.0.0.0');
`;

const sandbox = await Sandbox.create({
  apiKey: process.env.E2B_API_KEY,
  timeoutMs: 5 * 60 * 1000,
  secure: true,
  allowInternetAccess: false,
  network: { allowPublicTraffic: true, maskRequestHost: 'localhost:${PORT}' },
  metadata: { product: 'temuclaude-playground', purpose: 'node-workspace-test' },
});

try {
  await sandbox.files.write(`${root}/server.mjs`, server);
  await sandbox.commands.run(`node ${root}/server.mjs`, { background: true });
  const origin = `https://${sandbox.getHost(3000)}`;
  const [page, api] = await Promise.all([
    fetch(origin, { signal: AbortSignal.timeout(15_000) }),
    fetch(`${origin}/api/status`, { signal: AbortSignal.timeout(15_000) }),
  ]);
  const [html, status] = await Promise.all([page.text(), api.json().catch(() => ({}))]);
  const result = {
    sandboxCreated: true,
    htmlPreviewHttpStatus: page.status,
    apiHttpStatus: api.status,
    htmlSurfaceReady: html.includes('Preview ready'),
    localApiReady: status?.ok === true && status?.runtime === 'isolated-node',
  };
  console.log(JSON.stringify(result));
  if (!page.ok || !api.ok || !result.htmlSurfaceReady || !result.localApiReady) process.exitCode = 1;
} finally {
  await sandbox.kill().catch(() => undefined);
}

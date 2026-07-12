/** Paid E2B smoke test. It creates an ephemeral sandbox, verifies a public
 * static preview and downloadable artifact, then always destroys the sandbox. */
import { Sandbox } from 'e2b';

if (!process.env.E2B_API_KEY) {
  console.error('E2B_API_KEY is required for the live preview test.');
  process.exit(2);
}

const sandbox = await Sandbox.create({
  apiKey: process.env.E2B_API_KEY,
  timeoutMs: 120_000,
  allowInternetAccess: false,
  network: { allowPublicTraffic: true, maskRequestHost: 'localhost:${PORT}' },
  metadata: { product: 'temuclaude-playground', purpose: 'smoke-test' },
});

try {
  await sandbox.files.write('/home/oai/share/index.html', '<!doctype html><title>TemuClaude preview check</title><h1>OK</h1>');
  await sandbox.commands.run('python3 -m http.server 3000 --directory /home/oai/share', { background: true });
  const previewUrl = `https://${sandbox.getHost(3000)}`;
  const response = await fetch(previewUrl, { signal: AbortSignal.timeout(15_000) });
  const body = await response.text();
  const downloadUrl = await sandbox.downloadUrl('/home/oai/share/index.html');
  const result = {
    sandboxCreated: true,
    previewHttpStatus: response.status,
    previewReturnedExpectedContent: body.includes('OK'),
    downloadUrlCreated: Boolean(downloadUrl),
  };
  console.log(JSON.stringify(result));
  if (!response.ok || !result.previewReturnedExpectedContent || !result.downloadUrlCreated) process.exitCode = 1;
} finally {
  await sandbox.kill().catch(() => undefined);
}

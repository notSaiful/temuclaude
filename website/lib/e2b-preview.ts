import { Sandbox } from 'e2b';

const PREVIEW_ROOT = '/home/oai/share/temuclaude-preview';
const PREVIEW_PORT = 3000;
const PREVIEW_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_HTML_BYTES = 1_048_576;

export type IsolatedPreview = {
  sandboxId: string;
  previewUrl: string;
  downloadUrl: string;
  expiresAt: string;
};

const previewServer = `from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial

class PreviewHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Content-Security-Policy', "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' data: blob:; font-src 'self' data:; connect-src 'none'; form-action 'none'; base-uri 'none'; frame-ancestors https://temuclaude.com")
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

handler = partial(PreviewHandler, directory='${PREVIEW_ROOT}')
ThreadingHTTPServer(('0.0.0.0', ${PREVIEW_PORT}), handler).serve_forever()
`;

function configuredKey(): string {
  return process.env.E2B_API_KEY?.trim() || '';
}

export function isE2BPreviewConfigured(): boolean {
  return Boolean(configuredKey());
}

export async function createIsolatedHtmlPreview(html: string, metadata: { userId: string }): Promise<IsolatedPreview> {
  const apiKey = configuredKey();
  if (!apiKey) throw new Error('E2B preview is not configured.');
  if (!html.trim()) throw new Error('HTML is required for a preview.');
  if (Buffer.byteLength(html, 'utf8') > MAX_HTML_BYTES) throw new Error('HTML previews are limited to 1 MB.');

  const sandbox = await Sandbox.create({
    apiKey,
    timeoutMs: PREVIEW_TIMEOUT_MS,
    // A generated page must not make requests from the sandbox. Its browser
    // response is separately CSP-restricted before it reaches the iframe.
    allowInternetAccess: false,
    network: {
      allowPublicTraffic: true,
      maskRequestHost: 'localhost:${PORT}',
    },
    metadata: {
      product: 'temuclaude-playground',
      purpose: 'static-preview',
      user: metadata.userId.slice(0, 64),
    },
  });

  try {
    await sandbox.files.write([
      { path: `${PREVIEW_ROOT}/index.html`, data: html },
      { path: `${PREVIEW_ROOT}/preview_server.py`, data: previewServer },
    ]);
    await sandbox.commands.run(`python3 ${PREVIEW_ROOT}/preview_server.py`, {
      background: true,
      cwd: PREVIEW_ROOT,
    });

    const previewUrl = `https://${sandbox.getHost(PREVIEW_PORT)}`;
    const health = await fetch(previewUrl, { signal: AbortSignal.timeout(15_000) });
    if (!health.ok) throw new Error(`Preview server returned HTTP ${health.status}.`);

    return {
      sandboxId: sandbox.sandboxId,
      previewUrl,
      downloadUrl: await sandbox.downloadUrl(`${PREVIEW_ROOT}/index.html`),
      expiresAt: new Date(Date.now() + PREVIEW_TIMEOUT_MS).toISOString(),
    };
  } catch (error) {
    await sandbox.kill().catch(() => undefined);
    throw error;
  }
}

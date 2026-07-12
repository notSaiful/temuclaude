import { Sandbox } from 'e2b';

const PROJECT_ROOT = '/home/user/project';
const PROJECT_PORT = 3000;
const PROJECT_TIMEOUT_MS = 5 * 60 * 1000;
const MAX_PROJECT_FILES = 100;
const MAX_PROJECT_BYTES = 5 * 1024 * 1024;
const DEFAULT_TEMPLATE = 'temuclaude-project-preview:v1';

export type ProjectPreviewFile = {
  file_path: string;
  content: string;
  byte_size: number;
};

export type ProjectPreview = {
  sandboxId: string;
  previewUrl: string;
  expiresAt: string;
  entrypoint: 'static' | 'server';
};

const staticServer = `import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve, extname } from 'node:path';

const root = resolve(process.cwd());
const types = { '.css':'text/css; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.mjs':'text/javascript; charset=utf-8', '.json':'application/json; charset=utf-8', '.svg':'image/svg+xml', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.gif':'image/gif', '.webp':'image/webp', '.wasm':'application/wasm', '.html':'text/html; charset=utf-8' };
createServer(async (request, response) => {
  try {
    const raw = new URL(request.url || '/', 'http://preview.local').pathname;
    const requested = raw === '/' ? 'index.html' : raw.replace(/^\\/+/, '');
    const target = resolve(root, requested);
    if (!target.startsWith(root + '/') && target !== root) throw new Error('outside root');
    const body = await readFile(target);
    response.writeHead(200, { 'content-type': types[extname(target).toLowerCase()] || 'application/octet-stream', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff', 'referrer-policy': 'no-referrer', 'content-security-policy': "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; form-action 'none'; base-uri 'none'" });
    response.end(body);
  } catch {
    response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' });
    response.end('Not found');
  }
}).listen(Number(process.env.PORT || ${PROJECT_PORT}), '0.0.0.0');
`;

function configuredKey(): string {
  return process.env.E2B_API_KEY?.trim() || '';
}

function templateName(): string {
  return process.env.E2B_PROJECT_PREVIEW_TEMPLATE?.trim() || DEFAULT_TEMPLATE;
}

function validateFile(file: ProjectPreviewFile): void {
  if (!file.file_path || file.file_path.length > 512 || file.file_path.startsWith('/') || file.file_path.includes('..') || file.file_path.includes('\\')) {
    throw new Error('Project contains an invalid file path.');
  }
  if (Buffer.byteLength(file.content, 'utf8') !== file.byte_size || file.byte_size > 1_048_576) {
    throw new Error('Project contains an invalid file size.');
  }
}

export function isE2BProjectPreviewConfigured(): boolean {
  return Boolean(configuredKey());
}

async function waitForPreview(url: string): Promise<void> {
  let lastStatus = 0;
  for (let attempt = 0; attempt < 6; attempt += 1) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(10_000) });
      lastStatus = response.status;
      if (response.ok) return;
    } catch {
      // A sandbox URL can take a short moment to accept its first request.
    }
    await new Promise((resolve) => setTimeout(resolve, 750));
  }
  throw new Error(`Project preview did not become healthy${lastStatus ? ` (HTTP ${lastStatus})` : ''}.`);
}

export async function createIsolatedProjectPreview(files: ProjectPreviewFile[], metadata: { userId: string; projectId: string }): Promise<ProjectPreview> {
  const apiKey = configuredKey();
  if (!apiKey) throw new Error('E2B project previews are not configured.');
  if (files.length === 0 || files.length > MAX_PROJECT_FILES) throw new Error('Project previews require between 1 and 100 files.');
  let bytes = 0;
  for (const file of files) {
    validateFile(file);
    bytes += file.byte_size;
  }
  if (bytes > MAX_PROJECT_BYTES) throw new Error('Project previews are limited to 5 MB.');

  const serverFile = files.find((file) => file.file_path === 'server.mjs' || file.file_path === 'server.js');
  const hasIndex = files.some((file) => file.file_path === 'index.html');
  if (!serverFile && !hasIndex) throw new Error('A project preview needs index.html or server.mjs/server.js.');

  const sandbox = await Sandbox.create(templateName(), {
    apiKey,
    timeoutMs: PROJECT_TIMEOUT_MS,
    secure: true,
    allowInternetAccess: false,
    lifecycle: { onTimeout: 'kill' },
    network: { allowPublicTraffic: true, maskRequestHost: 'localhost:${PORT}' },
    envs: { PORT: String(PROJECT_PORT), NODE_ENV: 'production' },
    metadata: {
      product: 'temuclaude-playground',
      purpose: 'project-preview',
      user: metadata.userId.slice(0, 64),
      project: metadata.projectId.slice(0, 64),
    },
  });

  try {
    await sandbox.files.write([
      ...files.map((file) => ({ path: `${PROJECT_ROOT}/${file.file_path}`, data: file.content })),
      ...(serverFile ? [] : [{ path: `${PROJECT_ROOT}/.temuclaude-static-server.mjs`, data: staticServer }]),
    ]);
    await sandbox.commands.run(serverFile ? `node ${serverFile.file_path}` : 'node .temuclaude-static-server.mjs', {
      background: true,
      cwd: PROJECT_ROOT,
    });
    const previewUrl = `https://${sandbox.getHost(PROJECT_PORT)}`;
    await waitForPreview(previewUrl);
    return {
      sandboxId: sandbox.sandboxId,
      previewUrl,
      expiresAt: new Date(Date.now() + PROJECT_TIMEOUT_MS).toISOString(),
      entrypoint: serverFile ? 'server' : 'static',
    };
  } catch (error) {
    await sandbox.kill().catch(() => undefined);
    throw error;
  }
}

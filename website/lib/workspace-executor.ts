import { Sandbox } from 'e2b';
import { listWorkspaceFiles, upsertWorkspaceFile, type WorkspaceAction, type WorkspaceFile } from '@/lib/workspace';

const ROOT = '/home/user/project';
const MAX_WRITES = 25;
const MAX_COMMAND_MS = 60_000;

type FileWrite = { filePath: string; content: string; language?: string };

function configuredE2BKey() { return process.env.E2B_API_KEY?.trim() || ''; }
function executionTemplate() { return process.env.E2B_WORKSPACE_EXECUTION_TEMPLATE?.trim() || 'base'; }

function validPath(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0 && value.length <= 512 && !value.startsWith('/') && !value.includes('..') && !value.includes('\\');
}

function proposedWrites(payload: Record<string, unknown>): FileWrite[] {
  const writes = payload.files;
  if (!Array.isArray(writes) || writes.length === 0 || writes.length > MAX_WRITES) throw new Error(`file.write requires between 1 and ${MAX_WRITES} files.`);
  return writes.map((item) => {
    if (!item || typeof item !== 'object') throw new Error('Each file write must be an object.');
    const file = item as Record<string, unknown>;
    if (!validPath(file.filePath) || typeof file.content !== 'string' || Buffer.byteLength(file.content, 'utf8') > 1_048_576 || (file.language !== undefined && typeof file.language !== 'string')) {
      throw new Error('A requested file write is invalid.');
    }
    return { filePath: file.filePath, content: file.content, language: file.language as string | undefined };
  });
}

function commandFrom(payload: Record<string, unknown>) {
  const command = payload.command;
  if (typeof command !== 'string' || command.length === 0 || command.length > 1000 || /[;&|`$<>\n\r]/.test(command)) {
    throw new Error('Command is invalid or contains unsupported shell operators.');
  }
  const allowed = /^(?:npm (?:test|run [A-Za-z0-9:_-]+)|npx --no-install [A-Za-z0-9@/_-]+(?:\s+[A-Za-z0-9._/@=:-]+)*|node [A-Za-z0-9._/-]+|python3? [A-Za-z0-9._/-]+)$/;
  if (!allowed.test(command)) throw new Error('Only npm scripts, installed npx tools, node files, and Python files may run in a workspace.');
  return command;
}

function installCommand(payload: Record<string, unknown>) {
  const packages = payload.packages;
  if (!Array.isArray(packages) || packages.length === 0 || packages.length > 20 || !packages.every((pkg) => typeof pkg === 'string' && /^(?:@[-a-z0-9_.]+\/)?[a-z0-9][a-z0-9_.-]*(?:@[~^<>=*0-9a-zA-Z_.-]+)?$/.test(pkg))) {
    throw new Error('package.install requires 1–20 valid npm package names.');
  }
  return `npm install --save-exact ${packages.join(' ')}`;
}

async function createSandbox(files: WorkspaceFile[], allowInternet: boolean) {
  const apiKey = configuredE2BKey();
  if (!apiKey) throw new Error('Isolated execution is not configured.');
  const sandbox = await Sandbox.create(executionTemplate(), {
    apiKey,
    timeoutMs: MAX_COMMAND_MS + 30_000,
    secure: true,
    allowInternetAccess: allowInternet,
    lifecycle: { onTimeout: 'kill' },
    metadata: { product: 'temuclaude-playground', purpose: 'approved-workspace-action' },
  });
  await sandbox.files.write(files.map((file) => ({ path: `${ROOT}/${file.file_path}`, data: file.content })));
  return sandbox;
}

export async function executeWorkspaceAction(input: { action: WorkspaceAction; userId: string; projectId: string }): Promise<Record<string, unknown>> {
  const { action, userId, projectId } = input;
  if (action.action_type === 'file.write') {
    const writes = proposedWrites(action.requested_payload);
    const files = await Promise.all(writes.map((write) => upsertWorkspaceFile({ userId, projectId, ...write })));
    return { files: files.map(({ file_path, content_sha256, byte_size }) => ({ filePath: file_path, sha256: content_sha256, bytes: byte_size })) };
  }
  if (action.action_type !== 'command.run' && action.action_type !== 'package.install') throw new Error('This action must be executed by its dedicated integration.');
  const command = action.action_type === 'package.install' ? installCommand(action.requested_payload) : commandFrom(action.requested_payload);
  const files = await listWorkspaceFiles(userId, projectId);
  if (files.length === 0) throw new Error('Add workspace files before running a command.');
  const sandbox = await createSandbox(files, action.action_type === 'package.install');
  try {
    const result = await sandbox.commands.run(command, { cwd: ROOT, timeoutMs: MAX_COMMAND_MS });
    const output = String(result.stdout || '').slice(0, 20_000);
    const error = String(result.stderr || '').slice(0, 20_000);
    if (result.exitCode !== 0) throw new Error(error || output || `Command failed with exit code ${result.exitCode}.`);
    return { command, exitCode: result.exitCode, stdout: output, stderr: error, isolated: true, internetEnabled: action.action_type === 'package.install' };
  } finally {
    await sandbox.kill().catch(() => undefined);
  }
}

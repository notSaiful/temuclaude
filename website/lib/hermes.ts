import { callOpenRouter } from '@/lib/openrouter';
import { GoogleAuth } from 'google-auth-library';

export type HermesRuntime = 'openrouter' | 'hermes-gateway';
export type HermesActionProposal = {
  actionType: 'file.write' | 'command.run' | 'package.install';
  title: string;
  payload: Record<string, unknown>;
};
export type HermesPlan = { content: string; model?: string; runtime: HermesRuntime; proposals: HermesActionProposal[] };
type ProjectFile = { file_path: string; byte_size: number; content?: string };

const MAX_CONTEXT_BYTES = 120_000;
const MAX_FILE_BYTES = 24_000;
const GATEWAY_TIMEOUT_MS = 120_000;
const GATEWAY_MAX_TOKENS = 1_200;

function configuredGateway() {
  const baseUrl = process.env.HERMES_GATEWAY_URL?.replace(/\/+$/, '');
  const apiKey = process.env.HERMES_GATEWAY_API_KEY;
  const credentials = process.env.GOOGLE_CLOUD_RUN_INVOKER_CREDENTIALS;
  if (!baseUrl || !apiKey || !credentials) return null;
  try {
    const parsed = JSON.parse(credentials) as Record<string, unknown>;
    if (parsed.type !== 'service_account' || typeof parsed.client_email !== 'string' || typeof parsed.private_key !== 'string') return null;
    return { baseUrl, apiKey, credentials: parsed };
  } catch {
    return null;
  }
}

function projectContext(files: ProjectFile[]) {
  let remaining = MAX_CONTEXT_BYTES;
  const sections: string[] = [];
  for (const file of files) {
    if (remaining <= 0) break;
    const source = typeof file.content === 'string' ? file.content : '';
    const excerpt = source.slice(0, Math.min(MAX_FILE_BYTES, remaining));
    const used = Buffer.byteLength(excerpt, 'utf8');
    if (used > remaining) break;
    remaining -= used;
    sections.push(`FILE: ${file.file_path} (${file.byte_size} bytes)\n${excerpt || '[content unavailable]'}`);
  }
  return sections.join('\n\n---\n\n');
}

function messages(input: { prompt: string; projectTitle: string; files: ProjectFile[] }) {
  return [
    {
      role: 'system' as const,
      content: `You are TemuClaude's built-in workspace assistant. Analyze the supplied workspace and propose only safe, implementation-ready work. Return JSON only, with this exact shape: {"summary":"plain-language plan","actions":[{"actionType":"file.write"|"command.run"|"package.install","title":"short label","payload":{...}}]}. For file.write, payload is {"files":[{"filePath":"relative/path","content":"full file content","language":"optional"}]}. For command.run, payload is {"command":"npm test"} or another single safe npm script/node/python command. For package.install, payload is {"packages":["package-name"]}. Include no more than five actions. Never claim an action has run: every action is shown to the user and needs explicit approval. If a task requires browser, network, GitHub, or deployment work, explain that in summary but do not fabricate an action.`,
    },
    {
      role: 'user' as const,
      content: `Project: ${input.projectTitle}\n\nWorkspace context:\n${projectContext(input.files) || 'No files yet.'}\n\nTask:\n${input.prompt}`,
    },
  ];
}

function normalizeProposals(value: unknown): HermesActionProposal[] {
  if (!Array.isArray(value)) return [];
  return value.slice(0, 5).flatMap((item): HermesActionProposal[] => {
    if (!item || typeof item !== 'object') return [];
    const record = item as Record<string, unknown>;
    if ((record.actionType !== 'file.write' && record.actionType !== 'command.run' && record.actionType !== 'package.install') || typeof record.title !== 'string' || !record.title.trim() || !record.payload || typeof record.payload !== 'object' || Array.isArray(record.payload)) return [];
    return [{ actionType: record.actionType, title: record.title.slice(0, 140), payload: record.payload as Record<string, unknown> }];
  });
}

function parsePlan(content: string, runtime: HermesRuntime, model?: string): HermesPlan {
  const trimmed = content.trim().replace(/^```json\s*/i, '').replace(/\s*```$/, '');
  try {
    const parsed = JSON.parse(trimmed) as Record<string, unknown>;
    if (typeof parsed.summary === 'string' && parsed.summary.trim()) return { content: parsed.summary.trim(), proposals: normalizeProposals(parsed.actions), model, runtime };
  } catch { /* A provider may return a plain-language plan; retain it safely. */ }
  return { content: content.trim(), proposals: [], model, runtime };
}

async function requestGatewayPlan(
  input: { prompt: string; projectTitle: string; files: ProjectFile[] },
  gateway: { baseUrl: string; apiKey: string; credentials: Record<string, unknown> },
): Promise<HermesPlan> {
  // Cloud Run is private. Generate a short-lived Google-signed ID token on
  // the server, then preserve Hermes' separate API key in Authorization.
  // X-Serverless-Authorization is required when both token types are present.
  const auth = new GoogleAuth({ credentials: gateway.credentials });
  const idTokenClient = await auth.getIdTokenClient(gateway.baseUrl);
  const idToken = await idTokenClient.idTokenProvider.fetchIdToken(gateway.baseUrl);
  const response = await fetch(`${gateway.baseUrl}/v1/chat/completions`, {
    method: 'POST', cache: 'no-store', signal: AbortSignal.timeout(GATEWAY_TIMEOUT_MS),
    headers: {
      Authorization: `Bearer ${gateway.apiKey}`,
      'X-Serverless-Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: process.env.HERMES_GATEWAY_MODEL || 'hermes',
      messages: messages(input),
      max_tokens: GATEWAY_MAX_TOKENS,
    }),
  });
  const payload = await response.json().catch(() => ({}));
  const content = payload?.choices?.[0]?.message?.content;
  if (
    !response.ok ||
    typeof content !== 'string' ||
    !content.trim() ||
    /^API call failed(?:\s|:)/i.test(content.trim())
  ) throw new Error('Hermes gateway could not produce a plan.');
  return parsePlan(content, 'hermes-gateway', typeof payload.model === 'string' ? payload.model : undefined);
}

/**
 * The production default is direct OpenRouter, so built-in workspace analysis
 * works on the serverless Playground without requiring a public Hermes daemon.
 */
export async function requestHermesPlan(input: { prompt: string; projectTitle: string; files: ProjectFile[] }): Promise<HermesPlan> {
  const runtime = process.env.HERMES_RUNTIME || 'openrouter';
  const gateway = configuredGateway();
  if (runtime === 'gateway') {
    if (!gateway) throw new Error('Hermes gateway is not fully configured. Set its server-only Cloud Run credentials.');
    return requestGatewayPlan(input, gateway);
  }

  const result = await callOpenRouter(
    process.env.HERMES_OPENROUTER_MODEL || 'z-ai/glm-5.2',
    messages(input),
    { maxTokens: 2_400, temperature: 0.25, timeoutMs: 60_000, sessionId: `hermes-plan-${Date.now()}` },
  );
  if (!result.success || !result.content.trim()) throw new Error(result.error || 'OpenRouter workspace analysis could not complete.');
  return parsePlan(result.content, 'openrouter', result.model);
}

import { callOpenRouter } from '@/lib/openrouter';
import { GoogleAuth } from 'google-auth-library';

export type HermesRuntime = 'openrouter' | 'hermes-gateway';
export type HermesPlan = { content: string; model?: string; runtime: HermesRuntime };
type ProjectFile = { file_path: string; byte_size: number; content?: string };

const MAX_CONTEXT_BYTES = 120_000;
const MAX_FILE_BYTES = 24_000;

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
      content: `You are TemuClaude's built-in workspace assistant, powered by OpenRouter. Analyze the supplied workspace and give an implementation-ready plan. You may inspect the supplied project context, reason about files, propose edits, package installs, network work, GitHub operations, and preview/production deployments. Never claim an action has run. Clearly label any proposed write, command, network, GitHub, or deployment action as requiring user approval. Be concise but concrete: files, changes, verification, and risks.`,
    },
    {
      role: 'user' as const,
      content: `Project: ${input.projectTitle}\n\nWorkspace context:\n${projectContext(input.files) || 'No files yet.'}\n\nTask:\n${input.prompt}`,
    },
  ];
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
    method: 'POST', cache: 'no-store', signal: AbortSignal.timeout(60_000),
    headers: {
      Authorization: `Bearer ${gateway.apiKey}`,
      'X-Serverless-Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model: process.env.HERMES_GATEWAY_MODEL || 'hermes', messages: messages(input) }),
  });
  const payload = await response.json().catch(() => ({}));
  const content = payload?.choices?.[0]?.message?.content;
  if (!response.ok || typeof content !== 'string' || !content.trim()) throw new Error('Hermes gateway could not produce a plan.');
  return { content: content.trim(), model: typeof payload.model === 'string' ? payload.model : undefined, runtime: 'hermes-gateway' };
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
  return { content: result.content.trim(), model: result.model, runtime: 'openrouter' };
}

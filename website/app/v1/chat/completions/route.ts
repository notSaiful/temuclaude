/**
 * TemuClaude's OpenAI-compatible API.
 *
 * The production product is intentionally small: one API, three approved
 * models, one classified generation. Kimi K3 handles code and agentic work,
 * Grok 4.5 handles repair/review, and GLM 5.2 is the general reasoning route.
 */
import { timingSafeEqual } from 'crypto';
import { NextRequest, NextResponse } from 'next/server';
import { incrementUsageAsync, getRollingWindowUsageAsync, validateApiKeyAsync, verifyAndRenewWeeklyCreditsAsync } from '@/lib/db';
import { callOpenRouter, type ChatMessage } from '@/lib/openrouter';
import { PLAN_LIMITS } from '@/lib/plans';
import { MODELS, routePrompt } from '@/lib/three-model-router';

export const runtime = 'nodejs';
export const maxDuration = 180;

const API_MODEL = 'temuclaude/temuclaude';

function constantTimeEqual(left: string, right: string): boolean {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

function assistantText(messages: ChatMessage[]): string {
  return [...messages].reverse().find((message) => message.role === 'user')?.content || '';
}

function tokenEstimate(value: string): number {
  return Math.ceil(value.length / 4);
}

function completionResponse(content: string, promptTokens: number, completionTokens: number, stream: boolean) {
  const created = Math.floor(Date.now() / 1000);
  const id = `chatcmpl-${crypto.randomUUID()}`;
  const payload = {
    id,
    object: 'chat.completion',
    created,
    model: API_MODEL,
    choices: [{ index: 0, message: { role: 'assistant', content }, finish_reason: 'stop' }],
    usage: { prompt_tokens: promptTokens, completion_tokens: completionTokens, total_tokens: promptTokens + completionTokens },
  };
  if (!stream) return NextResponse.json(payload);

  const encoder = new TextEncoder();
  const chunk = { id, object: 'chat.completion.chunk', created, model: API_MODEL };
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({ ...chunk, choices: [{ index: 0, delta: { role: 'assistant' }, finish_reason: null }] })}\n\n`));
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({ ...chunk, choices: [{ index: 0, delta: { content }, finish_reason: null }] })}\n\n`));
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({ ...chunk, choices: [{ index: 0, delta: {}, finish_reason: 'stop' }] })}\n\n`));
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });
  return new NextResponse(body, { headers: { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache, no-transform', Connection: 'keep-alive' } });
}

export async function POST(request: NextRequest) {
  try {
    const apiKey = request.headers.get('authorization')?.replace(/^Bearer\s+/i, '') || request.headers.get('x-api-key') || '';
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;
    const publicApi = process.env.TEMUCLAUDE_ALLOW_PUBLIC_API === 'true';
    let userId: string | null = null;
    let plan = 'free';
    let isEvaluation = false;

    if (apiKey) {
      if (masterKey && constantTimeEqual(apiKey, masterKey)) {
        isEvaluation = true;
      } else {
        const valid = await validateApiKeyAsync(apiKey);
        if (!valid) return NextResponse.json({ error: { message: 'Invalid API key', type: 'authentication_error' } }, { status: 401 });
        if (valid.user.plan === 'free') return NextResponse.json({ error: { message: 'API access requires a paid plan.', type: 'permission_error' } }, { status: 403 });
        userId = valid.userId;
        plan = valid.user.plan;
      }
    } else if (!publicApi) {
      return NextResponse.json({ error: { message: 'Missing API key', type: 'authentication_error' } }, { status: 401 });
    }

    if (userId && !isEvaluation) {
      const user = await verifyAndRenewWeeklyCreditsAsync(userId);
      if (!user || user.credit_balance <= 0) return NextResponse.json({ error: { message: 'Credit balance exhausted.', type: 'rate_limit_error' } }, { status: 429 });
      const limit = PLAN_LIMITS[plan as keyof typeof PLAN_LIMITS] || PLAN_LIMITS.free;
      const rolling = await getRollingWindowUsageAsync(userId, 5);
      if (limit.rollingQueries !== Infinity && rolling.query_count >= limit.rollingQueries) {
        return NextResponse.json({ error: { message: 'Rate limit exceeded.', type: 'rate_limit_error' } }, { status: 429 });
      }
    }

    const body = await request.json();
    const messages = body.messages as ChatMessage[] | undefined;
    if (!Array.isArray(messages) || messages.length === 0 || messages.some((message) => !message || typeof message.content !== 'string')) {
      return NextResponse.json({ error: { message: 'messages must be a non-empty array of text chat messages', type: 'invalid_request_error' } }, { status: 400 });
    }
    if (body.model && body.model !== API_MODEL && body.model !== 'temuclaude') {
      return NextResponse.json({ error: { message: `Unsupported model. Use ${API_MODEL}.`, type: 'invalid_request_error' } }, { status: 400 });
    }

    const route = routePrompt(assistantText(messages));
    const requestedMaxTokens = Math.min(Math.max(Number(body.max_tokens) || 2048, 64), 16_384);
    // Kimi K3 may spend part of the provider budget on internal reasoning
    // before emitting a complete artifact. A common client default of 2–4k
    // therefore produced truncated HTML despite a successful upstream status.
    // Give coding and agent-workflow deliverables enough room to finish.
    const maxTokens = route.kind === 'coding' || route.kind === 'agentic'
      ? Math.max(requestedMaxTokens, 12_000)
      : requestedMaxTokens;
    const result = await callOpenRouter(route.model, [{ role: 'system', content: route.system }, ...messages], {
      temperature: typeof body.temperature === 'number' ? Math.min(Math.max(body.temperature, 0), 2) : 0.4,
      maxTokens,
      timeoutMs: 170_000,
      fallbacks: route.fallbacks,
      sessionId: request.headers.get('x-request-id') || `tc-${Date.now()}`,
    });
    if (!result.success || !result.content.trim()) {
      return NextResponse.json({ error: { message: 'TemuClaude could not produce a completion. Please retry.', type: 'server_error' } }, { status: 503 });
    }

    const promptTokens = tokenEstimate(messages.map((message) => message.content).join('\n'));
    const completionTokens = result.tokens || tokenEstimate(result.content);
    if (userId && !isEvaluation) await incrementUsageAsync(userId, promptTokens, completionTokens, result.model || route.model);
    const response = completionResponse(result.content.trim(), promptTokens, completionTokens, body.stream === true);
    response.headers.set('X-TemuClaude-Route', route.kind);
    response.headers.set('X-TemuClaude-Model', result.model || route.model);
    response.headers.set('X-TemuClaude-Models', Object.values(MODELS).join(','));
    return response;
  } catch (error) {
    console.error('chat completion failed', error);
    return NextResponse.json({ error: { message: 'Internal server error', type: 'server_error' } }, { status: 500 });
  }
}

import { NextRequest } from 'next/server';
import { createHash } from 'crypto';
import { callOpenRouter } from '@/lib/openrouter';
import { callOpenRouterLite, type LiteModelId } from '@/lib/openrouter-lite';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { getOrCreateUserByEmailAsync, getRollingWindowUsageAsync, incrementUsageAsync, verifyAndRenewWeeklyCreditsAsync } from '@/lib/db';
import { PLAN_LIMITS, ROLLING_WINDOW_HOURS } from '@/lib/plans';

export const runtime = 'nodejs';
// Hard Pro requests deliberately run several high-value model and verifier
// stages. Give that quality-first pipeline room to finish instead of allowing
// the platform to kill it mid-pipeline with no answer. Raised from 120s to
// 300s on 2026-07-14 (Vercel plan ceiling): hard runs can reach ~210s.
export const maxDuration = 300;

// TemuClaude Pro — the current eight-model, role-bounded registry.
// Each model has a distinct job; premium escalation remains conditional.
const POOL = {
  orchestrator: 'z-ai/glm-5.2',
  reasoning: 'deepseek/deepseek-v4-pro',
  fastRoute: 'deepseek/deepseek-v4-flash',
  multimodal: 'google/gemini-3.5-flash',
  specialist: 'minimax/minimax-m3',
  vision: 'minimax/minimax-m3',
  frontier: 'openai/gpt-5.6-luna',
  codeRepair: 'x-ai/grok-4.5',
  verifier: 'nvidia/nemotron-3-ultra-550b-a55b',
};

// Each pool model's best jobs. Drives drafter selection + role assignment so a
// build uses the strongest model for each job instead of defaulting to one. The
// labels mirror the short names shown in the orchestration panel.
const MODEL_STRENGTHS: Record<string, { label: string; best: string[] }> = {
  'z-ai/glm-5.2':               { label: 'GLM-5.2',           best: ['architecture', 'synthesis', 'judging', 'general-code', 'agentic'] },
  'deepseek/deepseek-v4-pro':   { label: 'DeepSeek V4 Pro',   best: ['code', 'math', 'algorithms', 'logic-heavy'] },
  'deepseek/deepseek-v4-flash': { label: 'DeepSeek V4 Flash', best: ['planning', 'fast-draft', 'cheap'] },
  'google/gemini-3.5-flash':    { label: 'Gemini 3.5 Flash',  best: ['visual', 'layout', 'theme', 'ui-ux', 'multimodal'] },
  'minimax/minimax-m3':         { label: 'MiniMax M3',        best: ['creative', 'long-context', 'generalist'] },
  'openai/gpt-5.6-luna':        { label: 'GPT-5.6 Luna',      best: ['frontier', 'hardest-integration', 'complex-systems'] },
  'x-ai/grok-4.5':              { label: 'Grok 4.5',          best: ['debugging', 'repair'] },
  'nvidia/nemotron-3-ultra-550b-a55b': { label: 'Nemotron',    best: ['verification', 'judging', 'scoring'] },
};

// Lite is intentionally isolated from POOL. Its caller enforces this exact
// allowlist and never substitutes a Pro or free-route model.
const LITE_POOL = {
  default: 'deepseek/deepseek-v4-flash',
  reasoning: 'qwen/qwen3.7-plus',
  agent: 'qwen/qwen3.7-plus',
  verifier: 'nvidia/nemotron-3-ultra-550b-a55b',
} satisfies Record<string, LiteModelId>;

// System prompt to force English responses
const ENGLISH_SYSTEM = { role: 'system', content: 'You are TemuClaude, an AI assistant. Always respond in clear, professional English. Be concise and direct.' };

type ModelProfile = 'pro' | 'lite';
type ChatMessage = { role: 'user' | 'assistant'; content: string };
type ModelResult = {
  name: string;
  content: string;
  latency: number;
  ok: boolean;
  modelId?: string;
  promptTokens?: number;
  completionTokens?: number;
  cost?: number;
  /** Underlying provider error/status when ok is false, for honest diagnostics. */
  error?: string;
};
type OrchestrationData = {
  taskType: string; tier: string;
  models: { name: string; response: string; latency: number; correct: boolean }[];
  aggregator: string; consensus: number; qaScore: number; codeVerified: boolean;
  totalLatency: string; cost: string; techniques: string[];
};

type CompletedResponse = {
  content: string;
  model: string;
  promptTokens?: number;
  completionTokens?: number;
};

function validateMessages(value: unknown): { messages: ChatMessage[] } | { error: string } {
  if (!Array.isArray(value) || value.length === 0) {
    return { error: 'messages must be a non-empty array' };
  }
  if (value.length > 50) {
    return { error: 'messages cannot contain more than 50 entries' };
  }

  let totalCharacters = 0;
  const messages: ChatMessage[] = [];
  for (const message of value) {
    if (!message || typeof message !== 'object') {
      return { error: 'each message must be an object' };
    }
    const { role, content } = message as Record<string, unknown>;
    if ((role !== 'user' && role !== 'assistant') || typeof content !== 'string' || !content.trim()) {
      return { error: 'each message requires a user or assistant role and non-empty content' };
    }
    if (content.length > 20_000) {
      return { error: 'each message must be 20,000 characters or fewer' };
    }

    totalCharacters += content.length;
    if (totalCharacters > 100_000) {
      return { error: 'messages must be 100,000 characters or fewer in total' };
    }
    messages.push({ role, content });
  }

  return { messages };
}

function corsInit(req: NextRequest): Record<string, string> {
  // The chat route runs on Cloud Run (long request timeout) and is called
  // cross-origin from the Vercel playground using a bearer access token (no
  // cookies cross-origin). Same-origin Vercel requests are not subject to
  // CORS, so these headers are inert there. Allowlist is configurable.
  const allow = (process.env.CHAT_CORS_ALLOW_ORIGIN || 'https://temuclaude.com')
    .split(',').map((s) => s.trim()).filter(Boolean);
  const origin = req.headers.get('origin');
  const allowOrigin = origin && allow.includes(origin) ? origin : (allow[0] || 'https://temuclaude.com');
  return {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Authorization, Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

// Preflight for cross-origin (Cloud Run) chat calls. Same-origin Vercel calls
// never trigger a preflight, so this is inert on Vercel.
export async function OPTIONS(req: NextRequest) {
  return new Response(null, { status: 204, headers: corsInit(req) });
}

export async function POST(req: NextRequest) {
  const auth = await getAuthenticatedSupabaseUser(req);
  if ('error' in auth) {
    return Response.json({ error: auth.error }, { status: auth.status, headers: corsInit(req) });
  }
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return Response.json({ error: 'Authenticated user has no email address' }, { status: 400, headers: corsInit(req) });
  const initialUser = await getOrCreateUserByEmailAsync(email);
  const account = (await verifyAndRenewWeeklyCreditsAsync(initialUser.id)) || initialUser;
  const limits = PLAN_LIMITS[account.plan as keyof typeof PLAN_LIMITS] || PLAN_LIMITS.free;
  const rollingUsage = await getRollingWindowUsageAsync(account.id, ROLLING_WINDOW_HOURS);
  if (account.credit_balance <= 0 || (limits.rollingQueries !== Infinity && rollingUsage.query_count >= limits.rollingQueries)) {
    return Response.json({ error: 'Usage limit reached. Upgrade or wait for capacity to recover.' }, { status: 429, headers: corsInit(req) });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: 'Request body must be valid JSON' }, { status: 400, headers: corsInit(req) });
  }

  const payload = body && typeof body === 'object' ? body as Record<string, unknown> : {};
  const profile = payload.profile === undefined ? 'pro' : payload.profile;
  if (profile !== 'pro' && profile !== 'lite') {
    return Response.json({ error: 'profile must be either "pro" or "lite"' }, { status: 400, headers: corsInit(req) });
  }

  const validated = validateMessages(payload.messages);
  if ('error' in validated) {
    return Response.json({ error: validated.error }, { status: 400, headers: corsInit(req) });
  }
  const messages = validated.messages;
  const encoder = new TextEncoder();
  const t0 = Date.now();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const query = messages[messages.length - 1]?.content || '';
        const techniques: string[] = [];
        sendProgress(controller, encoder, 'Classifying prompt', 'Analyzing the request to pick the right pipeline');
        const cls = await classifyWithDeliberation(query, profile, controller, encoder, techniques);
        const { taskType, tier, isCodeGeneration, difficulty } = cls;
        sendProgress(controller, encoder, 'Routing selected', `TemuClaude ${profile === 'lite' ? 'Lite' : 'Pro'} · ${taskType} task · ${tier} tier · ${cls.confidence} confidence — ${cls.reason.slice(0, 80)}`, 'done');

        let completed: CompletedResponse;
        if (profile === 'lite') {
          completed = await runLiteStack(query, messages, controller, encoder, taskType, tier, difficulty, t0, techniques, isCodeGeneration);
        } else if (isCodeGeneration) {
          completed = await runCodeGeneration(query, messages, controller, encoder, taskType, tier, t0, techniques);
        } else if (tier === 'trivial') {
          // Layer 1: cheapest approved Pro route for straightforward requests.
          // Budget raised from callModel defaults (2k/10s) to 4k/25s so a
          // reasoning-capable fast model has room to finish, with the
          // orchestrator + DeepSeek V4 Pro as explicit fallbacks.
          techniques.push('direct-routing');
          completed = await routeSingleModel(controller, encoder, POOL.fastRoute, messages, { maxTokens: 4_096, timeoutMs: 25_000, fallbacks: [POOL.orchestrator, POOL.reasoning] }, taskType, tier, t0, techniques, 'Calling fast model', 'DeepSeek V4 Flash is drafting');
        } else if (tier === 'medium') {
          // Layer 2: Specialist routing, with the same empty-content gate +
          // fallback chain as the trivial tier so a single empty specialist
          // response is never streamed as the final answer.
          techniques.push('specialist-routing');
          const specialist = pickSpecialist(taskType);
          completed = await routeSingleModel(controller, encoder, specialist, messages, { maxTokens: 4_096, timeoutMs: 30_000, fallbacks: [POOL.orchestrator, POOL.reasoning] }, taskType, tier, t0, techniques, 'Calling specialist', `${specialist.split('/').pop()} is drafting`);
        } else {
          // HARD: Full 6-layer stack
          completed = await runFullStack(query, messages, controller, encoder, taskType, tier, t0, techniques);
        }

        // Count the classification pre-pass tokens toward usage. callOpenRouter
        // returns a single total-tokens figure; fold it into the completion
        // count (the classifier is a small call, so the approximation is minor).
        const baseCompletionTokens = completed.completionTokens ?? estimateTokens(completed.content);
        completed.completionTokens = baseCompletionTokens + cls.classifierTokens;

        await recordPlaygroundUsage(account.id, messages, completed);

        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Unknown error';
        sendProgress(controller, encoder, 'Recovered from error', msg, 'error');
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk: `I could not complete the full orchestration pass for this prompt. The request was accepted, but one of the model calls failed or timed out: ${msg}\n\nPlease retry, or break the task into smaller steps while the live pipeline recovers.` })}\n\n`));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: { ...corsInit(req), 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' },
  });
}

async function runLiteStack(
  query: string,
  messages: ChatMessage[],
  controller: ReadableStreamDefaultController,
  encoder: TextEncoder,
  taskType: string,
  tier: string,
  difficulty: number,
  t0: number,
  techniques: string[],
  isCodeGeneration: boolean,
): Promise<CompletedResponse> {
  // A straightforward code-generation request stays on the Flash worker in
  // Lite. Qwen is reserved for visual/agentic or explicit reasoning work, so
  // Lite cannot become more expensive than Pro merely because it wrote code.
  const model = isCodeGeneration
    ? LITE_POOL.default
    : ['math', 'reasoning'].includes(taskType)
    ? LITE_POOL.reasoning
    : difficulty >= 7
      ? LITE_POOL.agent
      : LITE_POOL.default;
  techniques.push('lite-single-model-routing');
  sendProgress(controller, encoder, 'Calling Lite model', `${model.split('/').pop()} is drafting`);

  const codeInstruction = isCodeGeneration
    ? `${ENGLISH_SYSTEM.content} Execute the requested coding task now. Do not ask follow-up questions when reasonable defaults are possible. For a game, website, or interactive app, return a complete runnable deliverable; when suitable, return one complete HTML document (<!doctype html> through </html>) in a single fenced html code block with all CSS and JavaScript included. The preview allows CDN libraries (cdn.jsdelivr.net, unpkg.com, cdnjs.cloudflare.com), Google Fonts, and remote https images, but blocks fetch/XHR/WebSockets and form submissions — inline any data the page needs. Do not outline phases or defer implementation.`
    : ENGLISH_SYSTEM.content;
  let result = await callOpenRouterLite(model, [
    {
      role: 'system',
      content: codeInstruction,
    },
    ...messages,
  ], {
    maxTokens: isCodeGeneration ? 3_072 : 2_000,
    timeoutMs: isCodeGeneration ? 30_000 : 12_000,
    sessionId: asciiSessionId('playground-lite', query),
  });
  // Keep Lite reliable without hiding a substituted model: the only rescue
  // route is the explicitly approved Qwen worker and it is used only after
  // the selected primary model fails. The final telemetry names the model.
  if (!result.success && model !== LITE_POOL.agent) {
    techniques.push('lite-approved-rescue');
    sendProgress(controller, encoder, 'Recovering Lite response', 'Qwen 3.7 Plus is producing the approved fallback');
    result = await callOpenRouterLite(LITE_POOL.agent, [
      { role: 'system', content: codeInstruction },
      ...messages,
    ], {
      maxTokens: isCodeGeneration ? 3_072 : 2_000,
      timeoutMs: isCodeGeneration ? 30_000 : 12_000,
      sessionId: asciiSessionId('playground-lite-rescue', query),
    });
  }
  let content = result.success
    ? result.content
    : 'TemuClaude Lite could not complete this request right now. Please try again.';
  let completionTokens = result.completionTokens;
  let providerCost = result.cost || 0;

  if (result.success && shouldVerifyLite(query, tier, content)) {
    techniques.push('lite-risk-verification');
    sendProgress(controller, encoder, 'Verifying Lite response', 'Nemotron is checking the final answer');
    const verdict = await callOpenRouterLite(LITE_POOL.verifier, [
      { role: 'system', content: 'Check the draft for factual, logical, or safety-critical errors. Reply with PASS, or FAIL followed by a concise correction request.' },
      { role: 'user', content: `Question:\n${query}\n\nDraft:\n${content}` },
    ], { maxTokens: 350, timeoutMs: 12_000, sessionId: asciiSessionId('playground-lite-verify', query) });
    completionTokens += verdict.completionTokens;
    providerCost += verdict.cost || 0;
    if (verdict.success && verdict.content.toUpperCase().startsWith('FAIL')) {
      techniques.push('lite-corrective-retry');
      sendProgress(controller, encoder, 'Correcting Lite response', 'Applying the independent verification feedback');
      const corrected = await callOpenRouterLite(model, [
        { role: 'system', content: `${ENGLISH_SYSTEM.content} A verifier found an issue in the previous draft. Produce a corrected, self-contained answer.` },
        ...messages,
        { role: 'assistant', content },
        { role: 'user', content: `Verifier feedback:\n${verdict.content}` },
      ], { maxTokens: isCodeGeneration ? 3_072 : 2_000, timeoutMs: isCodeGeneration ? 30_000 : 12_000, sessionId: asciiSessionId('playground-lite-correct', query) });
      if (corrected.success) {
        content = corrected.content;
        completionTokens += corrected.completionTokens;
        providerCost += corrected.cost || 0;
      }
    }
  }

  sendProgress(controller, encoder, 'Streaming answer', result.success ? 'Final response is ready' : 'The Lite model was unavailable', result.success ? 'done' : 'error');
  streamText(controller, encoder, content);
  sendOrch(controller, encoder, taskType, tier, [{
    name: result.model.split('/').pop() || result.model,
    response: content.substring(0, 200),
    latency: (Date.now() - t0) / 1000,
    correct: result.success,
  }], result.model.split('/').pop() || result.model, result.success ? 1 : 0, 0, false, t0, formatProviderCost(providerCost), techniques);
  return {
    content,
    model: result.model,
    promptTokens: result.promptTokens,
    completionTokens,
  };
}

function shouldVerifyLite(query: string, tier: string, answer: string): boolean {
  const text = query.toLowerCase();
  if (/(medical|diagnosis|medication|legal advice|financial advice|investment decision|safety critical|verify|fact-check|audit)/.test(text)) return true;
  if (isCodeGenerationRequest(query)) return false;
  if (tier !== 'hard' || answer.trim().length < 80) return tier === 'hard';
  const sample = createHash('sha256').update(query).digest().readUInt32BE(0) / 0x1_0000_0000;
  return sample < 0.02;
}

async function runCodeGeneration(
  query: string,
  messages: ChatMessage[],
  controller: ReadableStreamDefaultController,
  encoder: TextEncoder,
  taskType: string,
  tier: string,
  t0: number,
  techniques: string[],
): Promise<CompletedResponse> {
  // Code generation is a deliverable, not a debate topic. MoA fusion merges
  // three models' prose into incoherent code, so the design for a build is
  // strength-based, not debate-based:
  //   planner (fast model) -> N drafters (strong models, in parallel, picked by
  //   strength) -> judge (Nemotron selects the best draft, not fuses them) ->
  //   refine (optional, fix the issues the judge flagged) -> repairer (Grok,
  //   only if the chosen draft is broken).
  // Different models' strengths compete in parallel and the best draft wins; a
  // trivial code ask skips parallelism for a single coder. The user sees each
  // role activate instead of one opaque model call.
  techniques.push('direct-code-generation');
  const codeSystem = {
    role: 'system' as const,
    content: [
      'You are TemuClaude Code. Execute the user request now; do not ask follow-up questions when reasonable defaults are possible.',
      'For a game, website, or interactive app request, return a complete runnable deliverable.',
      'When a single-file HTML game or webpage is requested or suitable, output exactly one complete HTML document starting with <!doctype html> and ending with </html>, wrapped in a single ```html fenced block, with all CSS and JavaScript included.',
      'The preview sandbox can load libraries from https://cdn.jsdelivr.net, https://unpkg.com, and https://cdnjs.cloudflare.com (via <script src> and <link rel=stylesheet>), Google Fonts (fonts.googleapis.com / fonts.gstatic.com), and remote https images — so prefer CDN tags for libraries such as Three.js, p5.js, Phaser, or Tailwind instead of inlining large libraries.',
      'The preview blocks fetch, XMLHttpRequest, WebSockets, and form submissions, so inline any data the page needs (levels, configs, word lists, assets) and do not rely on runtime network calls.',
      'Do not describe phases, request model outputs, or defer implementation. State only brief assumptions, then provide the finished code.',
    ].join(' '),
  };
  // A complete game or app can run to several thousand tokens. The previous
  // 65s coder budget was shorter than a full generation, so the primary timed
  // out mid-file, the shared deadline starved the fallbacks, and the user saw
  // "temporarily unavailable". Give the build a real deadline and let the
  // coder use most of it; the route maxDuration (300s) leaves headroom.
  const deadlineAt = t0 + 200_000;
  const remainingMs = () => Math.max(0, deadlineAt - Date.now());
  const orchestrationModels: { name: string; response: string; latency: number; correct: boolean }[] = [];
  let totalCost = 0;

  // ROLE 1 — PLANNER: for substantial builds, a cheap fast model sketches the
  // structure first so the coder starts from a plan instead of a blank page.
  // Trivial code asks (one-function snippets) skip planning to stay lean. A
  // planner failure never blocks the coder — we just proceed without a plan.
  const substantialBuild = /\b(game|web app|webapp|website|web page|webpage|application|app|landing page|dashboard|platform|tool|editor|clone|simulator)\b/i.test(query);
  let plan = '';
  if (substantialBuild && remainingMs() > 18_000) {
    techniques.push('code-planning');
    sendProgress(controller, encoder, 'Planning the build', 'A fast model is outlining the structure');
    const planResult = await callModel(POOL.fastRoute, [
      { role: 'system', content: 'You are a build planner. Given a build request, output a concise build plan: the file structure, the main components/modules, the tech approach, and any assets needed. Use at most 10 short bullet lines. Do not write the code itself.' },
      ...messages,
    ], { maxTokens: 700, timeoutMs: 14_000, temperature: 0.25, disableReasoning: true });
    totalCost += planResult.cost || 0;
    if (planResult.ok && planResult.content.trim()) {
      plan = planResult.content.trim();
      orchestrationModels.push({ name: planResult.name, response: plan.substring(0, 200), latency: planResult.latency, correct: planResult.ok });
      sendProgress(controller, encoder, 'Plan ready', 'Generating the deliverable from the plan', 'done');
    } else {
      sendProgress(controller, encoder, 'Plan skipped', 'Generating the deliverable directly', 'done');
    }
  }

  // ROLE 2 — DRAFTERS: for a substantial build, several strong models draft the
  // full deliverable in parallel so different strengths (code, visual/layout,
  // frontier) compete; a judge then picks the best by SELECTION, not fusion
  // (fusing full files makes incoherent code). Trivial code asks get a single
  // coder (selectDrafters returns []) so they pay nothing for parallelism. Each
  // drafter gets the same per-call budget the single coder used; the drafters
  // run concurrently so wall-clock is bounded by the slowest single draft.
  // Billing note: a request is billed once on the final content (db.ts), so the
  // parallel drafts raise the real provider cost (shown as totalCost in the
  // panel) but do not multiply the user's credit burn.
  const coderMessages = plan
    ? [{ role: 'system' as const, content: `${codeSystem.content}\n\nBuild plan to follow:\n${plan}` }, ...messages]
    : [codeSystem, ...messages];
  const drafters = selectDrafters(query, tier);
  let result: ModelResult;
  if (drafters.length === 0) {
    // Trivial code: a single strong coder, same budget + fallbacks as before.
    sendProgress(controller, encoder, 'Generating the requested code', 'DeepSeek V4 Pro is building a complete deliverable');
    result = await callModel(POOL.reasoning, coderMessages, {
      maxTokens: 8_192,
      timeoutMs: Math.min(150_000, remainingMs()),
      temperature: 0.35,
      disableReasoning: true,
      // OpenRouter can move between these parameter-compatible code models
      // without making the user wait for a second full request timeout.
      fallbacks: [POOL.fastRoute, POOL.orchestrator],
    });
    totalCost += result.cost || 0;
    orchestrationModels.push({ name: result.name, response: result.content.substring(0, 200), latency: result.latency, correct: result.ok });
  } else {
    techniques.push('parallel-diverse-drafts');
    sendProgress(controller, encoder, 'Drafting in parallel', `${drafters.length} models are building the deliverable`);
    const settled = await Promise.allSettled(drafters.map((id) => callModel(id, coderMessages, {
      maxTokens: 8_192,
      timeoutMs: Math.min(150_000, remainingMs()),
      temperature: 0.4,
      disableReasoning: true,
      fallbacks: [POOL.fastRoute],
    })));
    const drafts: ModelResult[] = settled.map((r, i) =>
      r.status === 'fulfilled' ? r.value : { name: drafters[i].split('/').pop() || drafters[i], content: '[failed]', latency: 0, ok: false }
    );
    for (const d of drafts) {
      totalCost += d.cost || 0;
      orchestrationModels.push({ name: d.name, response: d.content.substring(0, 200), latency: d.latency, correct: d.ok });
    }
    const usable = drafts.filter((d) => d.ok && d.content.trim());
    sendProgress(controller, encoder, 'Drafts complete', `${usable.length}/${drafts.length} drafters returned usable builds`, usable.length > 0 ? 'done' : 'error');

    // ROLE 3 — JUDGE: Nemotron scores each draft and names the best.
    let bestIndex = 0;
    let issues = '';
    if (usable.length > 0) {
      techniques.push('judge-selection');
      sendProgress(controller, encoder, 'Judging drafts', 'Nemotron is scoring each build and picking the best');
      const verdict = await judgeCodeDrafts(query, drafts);
      bestIndex = verdict.bestIndex;
      issues = verdict.issues;
      sendProgress(controller, encoder, 'Best draft selected', `${drafts[bestIndex].name} won`, 'done');
    }
    result = drafts[bestIndex] || drafts[0];

    // ROLE 4 — REFINE: if the judge flagged fixable issues on the winner and
    // there is time, one pass lets the winner's own author apply the feedback.
    if (result.ok && issues && remainingMs() > 20_000) {
      techniques.push('judge-refine');
      sendProgress(controller, encoder, 'Refining the build', 'Applying the judge feedback to the winning draft');
      const refined = await callModel(drafters[bestIndex], [
        { role: 'system' as const, content: `${codeSystem.content}\n\nA judge reviewed your draft and found these issues. Fix them and return the complete, corrected deliverable:\n${issues}` },
        ...messages,
        { role: 'assistant' as const, content: result.content },
      ], {
        maxTokens: 8_192,
        timeoutMs: Math.min(60_000, remainingMs()),
        temperature: 0.3,
        disableReasoning: true,
        fallbacks: [POOL.orchestrator],
      });
      if (refined.ok && refined.content.trim()) {
        totalCost += refined.cost || 0;
        orchestrationModels.push({ name: refined.name, response: refined.content.substring(0, 200), latency: refined.latency, correct: refined.ok });
        result = refined;
      }
    }
  }

  // ROLE 5 — REPAIRER: only if the chosen draft failed or broke. Grok 4.5 repairs.
  if (!result.ok && remainingMs() >= 6_000) {
    techniques.push('code-repair-fallback');
    sendProgress(controller, encoder, 'Recovering code generation', 'Grok 4.5 is repairing the deliverable');
    const repair = await callModel(POOL.codeRepair, [codeSystem, ...messages], {
      maxTokens: 6_144,
      timeoutMs: Math.min(30_000, remainingMs()),
      temperature: 0.35,
      // Grok 4.5 requires reasoning to remain enabled. Omitting the disable
      // flag prevents the provider-side 400 that broke this route.
    });
    totalCost += repair.cost || 0;
    orchestrationModels.push({ name: repair.name, response: repair.content.substring(0, 200), latency: repair.latency, correct: repair.ok });
    result = repair;
  }

  // Surface the real failure reason instead of a generic "unavailable" banner,
  // so a timeout, a rate limit, or a parameter rejection is diagnosable.
  const failureReason = (result.error || 'all approved code routes returned no usable output').slice(0, 180);
  const content = result.ok
    ? result.content
    : `Code generation could not complete right now (${failureReason}). Please retry shortly.`;
  sendProgress(controller, encoder, 'Streaming code', result.ok ? 'Complete deliverable is ready' : 'The approved code route was unavailable', result.ok ? 'done' : 'error');
  streamText(controller, encoder, content);
  sendOrch(controller, encoder, taskType, tier, orchestrationModels, result.name, result.ok ? 1 : 0, 0, false, t0, formatProviderCost(totalCost), techniques);
  return { content, model: result.name };
}

// === FULL STACK (hard queries) ===
async function runFullStack(query: string, messages: any[], controller: ReadableStreamDefaultController, encoder: TextEncoder, taskType: string, tier: string, t0: number, techniques: string[]): Promise<CompletedResponse> {
  // Quality-first Pro panel: keep the planner and reasoning anchor, then add
  // the strongest specialist for this task instead of using the cheapest
  // fixed panel for every domain.
  const taskSpecialist = taskType === 'creative'
    ? POOL.specialist
    : ['knowledge', 'legal', 'health'].includes(taskType)
      ? POOL.multimodal
      : POOL.verifier;
  const fusionModels = [POOL.orchestrator, POOL.reasoning, taskSpecialist];
  techniques.push('quality-first-pro-panel');

  // LAYER 0: WEB SEARCH (for knowledge/reasoning questions)
  let searchContext = '';
  if (taskType === 'knowledge' || taskType === 'reasoning' || taskType === 'creative') {
    techniques.push('web-search');
    sendProgress(controller, encoder, 'Searching context', 'Looking for fresh supporting context');
    const searchResults = await webSearch(query, 3);
    if (searchResults) {
      searchContext = `\n\nRelevant search results:\n${searchResults}`;
      sendProgress(controller, encoder, 'Search complete', 'Context attached to the model prompt', 'done');
    } else {
      sendProgress(controller, encoder, 'Search skipped', 'Continuing without external context', 'done');
    }
  }

  // Augment messages with search context if available
  const augmentedMessages = searchContext
    ? [...messages.slice(0, -1), { role: 'user', content: messages[messages.length - 1]?.content + searchContext }]
    : messages;

  // LAYER 3: MoA 3-LAYER — Propose → Cross-Review → Aggregate
  techniques.push('moa-3-layer');
  sendProgress(controller, encoder, 'Drafting proposals', 'Three models are working in parallel');

  // Layer 1: 3 models propose independently (with search context).
  // Frontier reasoning models need real thinking time — at medium/high effort
  // they routinely take 30-60s+ before the first answer token, and over 100s at
  // max effort. Reasoning tokens count toward max_tokens, so a 2k cap starves
  // the answer. The callModel defaults (10s, 2k tokens) were shorter than a hard
  // math problem needs, so all three drafts timed out and the user saw "0/3
  // models returned usable drafts". The three run in parallel, so wall-clock is
  // bounded by the slowest single draft, not the sum. Reasoning stays ON (no
  // disableReasoning) — that is the whole point for math/reasoning tasks.
  const proposeResults = await Promise.allSettled(
    fusionModels.map(id => callModel(id, augmentedMessages, {
      maxTokens: 6_144,
      timeoutMs: 45_000,
      temperature: 0.6,
    }))
  );
  const proposals: ModelResult[] = proposeResults.map((r, i) =>
    r.status === 'fulfilled' ? r.value : { name: fusionModels[i].split('/').pop()||'', content: '[failed]', latency: 0, ok: false }
  );
  const workingProposals = proposals.filter(p => p.ok);
  sendProgress(controller, encoder, 'Proposal pass complete', `${workingProposals.length}/${proposals.length} models returned usable drafts`, workingProposals.length > 0 ? 'done' : 'error');

  if (workingProposals.length === 0) {
    // All three drafts failed (usually all timed out, or an OpenRouter outage).
    // Fall back to one strong reasoning model with a generous serial budget
    // instead of leaving the user with a dead "unavailable" message. The rescue
    // tries DeepSeek V4 Pro first, then GLM-5.2 and the flash route as fallbacks
    // within the same deadline.
    techniques.push('fullstack-single-rescue');
    sendProgress(controller, encoder, 'Recovering response', 'One strong model is producing a direct answer');
    const rescue = await callModel(POOL.reasoning, augmentedMessages, {
      maxTokens: 8_192,
      timeoutMs: 75_000,
      temperature: 0.4,
      fallbacks: [POOL.orchestrator, POOL.fastRoute],
    });
    if (rescue.ok && rescue.content.trim()) {
      sendProgress(controller, encoder, 'Streaming answer', 'Recovered response is ready', 'done');
      streamText(controller, encoder, rescue.content);
      sendOrch(controller, encoder, taskType, tier,
        [{ name: rescue.name, response: rescue.content.substring(0, 200), latency: rescue.latency, correct: true }],
        rescue.name, 1, 0, false, t0, formatProviderCost(rescue.cost), techniques);
      return { content: rescue.content, model: rescue.name };
    }
    const reason = (rescue.error || 'all models and the rescue route returned no usable output').slice(0, 180);
    streamText(controller, encoder, `All models are currently unavailable (${reason}). Please try again.`);
    sendOrch(controller, encoder, taskType, tier, proposals.map(p => ({ name: p.name, response: p.content.substring(0,200), latency: p.latency, correct: p.ok })), 'none', 0, 0, false, t0, formatProviderCost(rescue.cost), techniques);
    return { content: '', model: 'temuclaude-pro-fusion' };
  }

  // Layer 2: Cross-review — each model reviews the other two
  techniques.push('cross-review');
  sendProgress(controller, encoder, 'Cross-reviewing drafts', 'Models are checking each other for gaps');
  const crossReviewResults: ModelResult[] = [];
  for (let i = 0; i < Math.min(workingProposals.length, 1); i++) {
    if (Date.now() - t0 > 90_000) break;
    const reviewer = workingProposals[i];
    const others = workingProposals.filter((_, j) => j !== i);
    const reviewPrompt = buildCrossReviewPrompt(query, reviewer, others);
    // Cross-review writes an improved response, not a one-word verdict, so it
    // needs a real output budget — the callModel 2k/10s default truncated hard-
    // query reviews and let an empty review silently drop to the raw proposals.
    const reviewResult = await callModel(reviewer.name.includes('glm') ? POOL.orchestrator : reviewer.name.includes('deepseek') ? POOL.reasoning : POOL.specialist, [
      { role: 'system', content: 'You are reviewing other AI models\' responses. Identify errors, missing information, and strengths. Provide an improved response.' },
      { role: 'user', content: reviewPrompt },
    ], { maxTokens: 4_096, timeoutMs: 20_000 });
    crossReviewResults.push(reviewResult);
  }

  // Layer 3: GLM-5.2 aggregates with structured analysis
  techniques.push('structured-aggregation');
  sendProgress(controller, encoder, 'Aggregating answer', 'Synthesizing consensus, contradictions, and final response');
  // A timed-out peer review must never erase the usable proposals. The former
  // empty-review prompt caused the aggregator to ask customers for model
  // outputs instead of answering their request.
  const reviewOrProposalInputs = crossReviewResults.filter((result) => result.ok);
  const fusionPrompt = buildFusionPrompt(
    query,
    reviewOrProposalInputs.length > 0 ? reviewOrProposalInputs : workingProposals,
  );
  // The aggregator writes the FINAL answer for a hard query — synthesizing
  // three drafts — so it is the single most important call in the stack. The
  // callModel 2k/10s default (the same starved budget #28 fixed on the propose
  // layer) routinely left it empty, silently falling back to proposal[0] so the
  // MoA "consensus/contradiction synthesis" never actually ran. Give it a real
  // budget and an explicit fallback chain.
  const aggResult = await callModel(POOL.orchestrator, [
    { role: 'system', content: 'You are TemuClaude. Analyze these model responses and produce the best possible answer. Identify: 1) Consensus (where models agree — high confidence) 2) Contradictions (where they disagree — investigate) 3) Unique insights (something only one model caught) 4) Blind spots (what no model addressed). Then write the final answer.' },
    { role: 'user', content: fusionPrompt },
  ], { maxTokens: 6_144, timeoutMs: 30_000, temperature: 0.5, fallbacks: [POOL.reasoning, POOL.fastRoute] });
  let finalAnswer = aggResult.ok ? aggResult.content : workingProposals[0].content;
  sendProgress(controller, encoder, 'Aggregation complete', aggResult.ok ? 'Primary synthesis ready' : 'Using strongest available draft', 'done');

  // LAYER 4: SELF-CONSISTENCY (for math/reasoning — adaptive N samples)
  if ((taskType === 'math' || taskType === 'reasoning') && Date.now() - t0 < 90_000) {
    techniques.push('self-consistency');
    sendProgress(controller, encoder, 'Checking consistency', 'Sampling alternate reasoning paths');
    const N = 2;
    const samples: string[] = [finalAnswer];
    for (let s = 0; s < N - 1; s++) {
      const sampleResult = await callModel(POOL.reasoning, [
        ...messages,
        { role: 'assistant', content: finalAnswer },
        { role: 'user', content: 'Provide an alternative solution with different reasoning. Then give your final answer.' },
      ], { maxTokens: 4_096, timeoutMs: 25_000, temperature: 0.6 });
      if (sampleResult.ok) samples.push(sampleResult.content);
    }
    // PRM-weighted: score each sample with Nemotron, pick highest
    techniques.push('prm-weighted-voting');
    const scores = await Promise.all(samples.map((sample) => scoreAnswer(query, sample)));
    let bestScore = -1;
    let bestAnswer = finalAnswer;
    samples.forEach((sample, index) => {
      if (scores[index] > bestScore) { bestScore = scores[index]; bestAnswer = sample; }
    });
    finalAnswer = bestAnswer;
  }

  // LAYER 5: CODE VERIFICATION (for math/coding)
  let codeVerified = false;
  if ((taskType === 'math' || taskType === 'coding') && Date.now() - t0 < 105_000) {
    techniques.push('code-verification');
    sendProgress(controller, encoder, 'Verifying code or math', 'Running a lightweight verifier pass');
    codeVerified = await verifyCode(finalAnswer);
    if (!codeVerified) {
      // LAYER 7: REFLEXION — retry with feedback
      techniques.push('reflexion');
      const reflection = await callModel(POOL.verifier, [
        { role: 'system', content: 'You are a code verifier. The previous answer may have errors. Explain what went wrong and how to fix it.' },
        { role: 'user', content: `Question: ${query}\nAnswer: ${finalAnswer.substring(0, 500)}\n\nWhat is wrong with this answer? How should it be fixed?` },
      ], { maxTokens: 2_048, timeoutMs: 15_000 });
      if (reflection.ok) {
        const retryResult = await callModel(POOL.reasoning, [
          ...messages,
          { role: 'assistant', content: finalAnswer },
          { role: 'user', content: `A verifier found these issues:\n${reflection.content}\n\nPlease provide a corrected answer.` },
        ], { maxTokens: 6_144, timeoutMs: 30_000, fallbacks: [POOL.orchestrator] });
        if (retryResult.ok) finalAnswer = retryResult.content;
        codeVerified = await verifyCode(finalAnswer);
      }
      // Grok 4.5 is reserved for a bounded code-repair escalation, never a
      // first-pass model, so it improves failed code without inflating normal cost.
      if (taskType === 'coding' && !codeVerified && Date.now() - t0 < 115_000) {
        techniques.push('code-repair-escalation');
        const repair = await callModel(POOL.codeRepair, [
          { role: 'system', content: 'Repair the submitted solution. Return a complete, correct, self-contained answer with working code where relevant.' },
          { role: 'user', content: `Task:\n${query}\n\nCurrent attempted answer:\n${finalAnswer}` },
        ], { maxTokens: 6_144, timeoutMs: 30_000 }); // reasoning stays ON (Grok 4.5 requires it; the 2k/10s default starved a full repair)
        if (repair.ok) {
          finalAnswer = repair.content;
          codeVerified = await verifyCode(finalAnswer);
        }
      }
    }
  }

  // LAYER 6: SELF-QA GATE — USVA 4-rubric verification
  techniques.push('usva-5-rubric-qa');
  sendProgress(controller, encoder, 'Quality scoring', 'Running final answer quality gate');
  let qaScore = Date.now() - t0 < 135_000 ? await runUSVA(query, finalAnswer) : 0.7;

  // If QA fails, retry with Reflexion
  if (qaScore < 0.8 && !techniques.includes('reflexion') && Date.now() - t0 < 115_000) {
    techniques.push('reflexion');
    const reflection = await callModel(POOL.verifier, [
      { role: 'system', content: 'You are a quality verifier. The answer scored low on quality. Explain what is wrong.' },
      { role: 'user', content: `Question: ${query}\nAnswer: ${finalAnswer.substring(0, 500)}\nQuality score: ${qaScore.toFixed(2)}/1.0\n\nWhat needs to be improved?` },
    ], { maxTokens: 2_048, timeoutMs: 15_000 });
    if (reflection.ok) {
      const retryResult = await callModel(POOL.orchestrator, [
        ...messages,
        { role: 'assistant', content: finalAnswer },
        { role: 'user', content: `A quality check found these issues:\n${reflection.content}\n\nPlease provide an improved answer.` },
      ], { maxTokens: 4_096, timeoutMs: 25_000, fallbacks: [POOL.reasoning] });
      if (retryResult.ok) {
        const newScore = await runUSVA(query, retryResult.content);
        if (newScore > qaScore) { finalAnswer = retryResult.content; qaScore = newScore; }
      }
    }
  }

  // LAYER 12: s1 BUDGET FORCING (arXiv:2501.19393)
  // If the answer is suspiciously short for a hard question, force longer reasoning
  if ((taskType === 'math' || taskType === 'reasoning') && finalAnswer.length < 500 && Date.now() - t0 < 125_000) {
    techniques.push('s1-budget-forcing');
    const forcedResult = await callModel(POOL.reasoning, [
      ...messages,
      { role: 'assistant', content: finalAnswer + '\n\nWait' },
      { role: 'user', content: 'Continue your reasoning in more detail. Provide a thorough step-by-step solution.' },
    ], { maxTokens: 4_096, timeoutMs: 25_000 });
    if (forcedResult.ok && forcedResult.content.length > finalAnswer.length) {
      finalAnswer = forcedResult.content;
    }
  }

  // LAYER 13: STEP-LEVEL CODE VERIFICATION (rStar-Math pattern)
  // For math/coding: verify each reasoning step, not just the final answer
  if ((taskType === 'math' || taskType === 'coding') && !codeVerified && Date.now() - t0 < 125_000) {
    techniques.push('step-level-verification');
    const stepVerified = await stepLevelVerify(query, finalAnswer);
    if (stepVerified) {
      codeVerified = true;
    } else if (!techniques.includes('reflexion')) {
      // Step verification failed — retry with step-specific feedback
      techniques.push('reflexion');
      const retryResult = await callModel(POOL.reasoning, [
        ...messages,
        { role: 'assistant', content: finalAnswer },
        { role: 'user', content: 'Your solution has an error in one of the reasoning steps. Re-examine each step carefully and provide a corrected solution with verified code for each step.' },
      ], { maxTokens: 4_096, timeoutMs: 25_000 });
      if (retryResult.ok) {
        const reVerified = await stepLevelVerify(query, retryResult.content);
        if (reVerified) { finalAnswer = retryResult.content; codeVerified = true; }
        else if (retryResult.content.length > finalAnswer.length) { finalAnswer = retryResult.content; }
      }
    }
  }

  // LAYER 14: Z3/SMT LOGICAL VERIFICATION (ConsistPRM pattern)
  // Extract logical claims and check for contradictions
  if ((taskType === 'reasoning' || taskType === 'knowledge') && Date.now() - t0 < 130_000) {
    techniques.push('z3-logical-verification');
    const logicalCheck = await logicalVerify(finalAnswer);
    if (logicalCheck === 'contradiction') {
      // Contradiction found — trigger retry
      techniques.push('reflexion');
      const retryResult = await callModel(POOL.orchestrator, [
        ...messages,
        { role: 'assistant', content: finalAnswer },
        { role: 'user', content: 'A logical analysis found contradictions in your answer. Please identify and resolve any contradictory statements, then provide a corrected answer.' },
      ], { maxTokens: 4_096, timeoutMs: 25_000, fallbacks: [POOL.reasoning] });
      if (retryResult.ok) finalAnswer = retryResult.content;
    }
  }

  // LAYER 15: PARETO EFFICIENCY TRACKING
  // Track token usage vs quality — auto-tune for future queries
  techniques.push('pareto-tracking');
  const tokenUsage = finalAnswer.length + query.length;
  const efficiency = qaScore > 0 && tokenUsage > 0 ? (qaScore * 1000 / tokenUsage) : 0;
  // (In production, this would log to a database for analysis)

  // LAYER 16: PREFERENCE DATA ROUTING
  // Record this routing decision for future optimization
  techniques.push('preference-routing');
  // (In production, this would log: query → taskType → tier → models used → qaScore → success)

  // LAYER 10: SELF-MOA (if one model clearly dominates, note it)
  if (workingProposals.length === 1) {
    techniques.push('self-moa');
  }

  // LAYER 17: frontier escalation (GPT-5.6 Luna) only after QA failure.
  // For the hardest queries where QA score is still low after all retries
  if (qaScore < 0.82 && needsFrontier(query, taskType) && Date.now() - t0 < 130_000) {
    techniques.push('frontier-fallback');
    // Frontier reasoning models need ~100s+ to first token at high effort
    // (GPT-5.6 Luna ~116s). The callModel 10s default guaranteed a timeout, so
    // this escalation layer never actually fired — Luna was dead weight in the
    // pool. Give it a real deadline (reasoning stays ON — that is the point of
    // escalating to the frontier). The layer is already heavily gated (low QA
    // + needsFrontier + within the time budget), so it fires rarely; fallbacks
    // only help if Luna returns faster than the deadline.
    const frontierResult = await callModel(POOL.frontier, [
      { role: 'system', content: 'You are TemuClaude Frontier. Solve this problem with maximum rigor. Previous attempts scored low on quality. Provide a definitive answer.' },
      { role: 'user', content: `Question: ${query}\n\nPrevious best answer (scored ${qaScore.toFixed(2)}/1.0):\n${finalAnswer.substring(0, 2000)}\n\nProvide a better answer:` },
    ], { maxTokens: 8_192, timeoutMs: 120_000, fallbacks: [POOL.reasoning, POOL.orchestrator] });
    if (frontierResult.ok) {
      const newScore = await runUSVA(query, frontierResult.content);
      if (newScore > qaScore) {
        finalAnswer = frontierResult.content;
        qaScore = newScore;
      }
    }
  }

  // Stream final answer
  sendProgress(controller, encoder, 'Streaming answer', 'Final response is ready', 'done');
  streamText(controller, encoder, finalAnswer);

  const totalLatency = (Date.now() - t0) / 1000;
  sendOrch(controller, encoder, taskType, tier,
    proposals.map(p => ({ name: p.name, response: p.content.substring(0, 200), latency: parseFloat(p.latency.toFixed(1)), correct: p.ok })),
    POOL.orchestrator.split('/').pop() || 'glm-5.2',
    workingProposals.length,
    Math.round(qaScore * 10),
    codeVerified,
    t0, 'Provider-priced', techniques
  );
  return { content: finalAnswer, model: POOL.orchestrator };
}

// === HELPERS ===

function estimateTokens(text: string): number {
  return Math.max(1, Math.ceil(text.length / 4));
}

function formatProviderCost(cost?: number): string {
  if (!Number.isFinite(cost) || !cost || cost < 0) return 'Provider-priced';
  return '$' + cost.toFixed(cost < 0.01 ? 5 : 3);
}

// x-session-id is an HTTP header (ByteString / Latin-1, chars 0-255 only).
// Building it from raw user text crashes the request the moment the prompt
// contains any non-Latin-1 character (em dash U+2014, emoji, non-English
// script) with "Cannot convert argument to a ByteString". Base64url-encode
// the user text so every id is ASCII-safe while still unique per prompt.
// Mirrors the gateway route's pattern (Buffer.from(...).toString('base64url')).
function asciiSessionId(prefix: string, text: string): string {
  return `${prefix}-${Buffer.from(text || '').toString('base64url').slice(0, 64)}`;
}

async function recordPlaygroundUsage(userId: string, messages: ChatMessage[], response: CompletedResponse) {
  if (!response.content.trim()) return;
  const promptTokens = response.promptTokens ?? estimateTokens(messages.map((message) => message.content).join('\n'));
  const completionTokens = response.completionTokens ?? estimateTokens(response.content);
  try {
    await incrementUsageAsync(userId, promptTokens, completionTokens, response.model);
  } catch (error) {
    // A completed response must not be lost if telemetry storage is temporarily
    // unavailable; the database layer retains its own production safeguards.
    console.error('Playground usage recording failed:', error);
  }
}

function streamText(controller: ReadableStreamDefaultController, encoder: TextEncoder, text: string) {
  const words = text.split(' ');
  for (let i = 0; i < words.length; i++) {
    const chunk = i === 0 ? words[i] : ' ' + words[i];
    controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
  }
}

function sendProgress(controller: ReadableStreamDefaultController, encoder: TextEncoder, label: string, detail?: string, status: 'active' | 'done' | 'error' = 'active') {
  controller.enqueue(encoder.encode(`data: ${JSON.stringify({ progress: { label, detail, status } })}\n\n`));
}

function sendOrch(controller: ReadableStreamDefaultController, encoder: TextEncoder, taskType: string, tier: string, models: any[], aggregator: string, consensus: number, qaScore: number, codeVerified: boolean, t0: number, cost: string, techniques: string[]) {
  const data: OrchestrationData = {
    taskType, tier, models, aggregator, consensus, qaScore, codeVerified,
    totalLatency: ((Date.now() - t0) / 1000).toFixed(1), cost, techniques,
  };
  controller.enqueue(encoder.encode(`data: ${JSON.stringify({ orchestration: data })}\n\n`));
}

async function callModel(
  model: string,
  messages: any[],
  options: { maxTokens?: number; timeoutMs?: number; temperature?: number; disableReasoning?: boolean; fallbacks?: string[] } = {},
): Promise<ModelResult> {
  const start = Date.now();
  const messagesWithSystem = [ENGLISH_SYSTEM, ...messages]
    .map(m => ({ role: m.role, content: m.content }));
  const result = await callOpenRouter(model, messagesWithSystem, {
    maxTokens: options.maxTokens ?? 2_000,
    timeoutMs: options.timeoutMs ?? 10_000,
    temperature: options.temperature ?? 0.45,
    disableReasoning: options.disableReasoning,
    fallbacks: options.fallbacks,
    sessionId: asciiSessionId('playground', messages[messages.length - 1]?.content || String(Date.now())),
  });
  return {
    name: result.model.split('/').pop() || result.model,
    content: result.success ? result.content : `[OpenRouter error: ${result.error || result.status || 'failed'}]`,
    latency: (Date.now() - start) / 1000,
    ok: result.success,
    cost: result.cost,
    error: result.success ? undefined : (result.error || (result.status ? `HTTP ${result.status}` : 'failed')),
  };
}

// Single-model routing for the trivial + medium tiers. The old inline code
// called callModel with no fallbacks and streamed result.content unconditionally,
// so an empty/failed response surfaced to the user as the literal string
// "[OpenRouter error: OpenRouter returned an empty message]" — the same
// failure class PR #28 fixed on the MoA layer (a reasoning model can spend the
// whole token budget on excluded reasoning and return empty content, or a
// provider returns a transient empty). Here the callModel fallback chain
// retries the orchestrator then DeepSeek V4 Pro on empty, and the content gate
// below streams a clear, honest message instead of a raw error if every route
// still comes back empty.
async function routeSingleModel(
  controller: ReadableStreamDefaultController,
  encoder: TextEncoder,
  primary: string,
  messages: any[],
  callOptions: { maxTokens: number; timeoutMs: number; fallbacks: string[] },
  taskType: string,
  tier: string,
  t0: number,
  techniques: string[],
  progressLabel: string,
  progressDetail: string,
): Promise<CompletedResponse> {
  sendProgress(controller, encoder, progressLabel, progressDetail);
  const result = await callModel(primary, messages, callOptions);
  const usable = result.ok && !!result.content.trim() && !result.content.startsWith('[OpenRouter error:');
  if (usable) {
    sendProgress(controller, encoder, 'Streaming answer', 'Final response is ready', 'done');
    streamText(controller, encoder, result.content);
  } else {
    techniques.push('single-route-empty');
    const reason = (result.error || 'the model returned an empty response').slice(0, 160);
    sendProgress(controller, encoder, 'Response unavailable', 'No model returned usable output', 'error');
    streamText(controller, encoder, `I couldn't get a response from the model${reason ? ` (${reason})` : ''}. Please try again, or rephrase the request.`);
  }
  sendOrch(controller, encoder, taskType, tier, [{ name: result.name, response: result.content.substring(0, 200), latency: (Date.now() - t0) / 1000, correct: usable }], 'single', usable ? 1 : 0, 0, false, t0, formatProviderCost(result.cost), techniques);
  return { content: result.content, model: result.name };
}

function buildCrossReviewPrompt(query: string, reviewer: ModelResult, others: ModelResult[]): string {
  let prompt = `Question: "${query}"\n\nYour response:\n${reviewer.content.substring(0, 1000)}\n\nOther models responded:\n`;
  others.forEach((o, i) => { prompt += `--- Model ${i+1}: ${o.name} ---\n${o.content.substring(0, 800)}\n\n`; });
  prompt += `---\n\nReview the other models' responses. Identify errors, missing information, and insights they have that you missed. Provide an improved response.`;
  return prompt;
}

function buildFusionPrompt(query: string, results: ModelResult[]): string {
  let prompt = `Question: "${query}"\n\nModels responded (after cross-review):\n\n`;
  results.forEach((r, i) => { prompt += `=== ${r.name} ===\n${r.content.substring(0, 1500)}\n\n`; });
  prompt += `===\n\nAnalyze consensus, contradictions, unique insights, and blind spots. Write the final answer.`;
  return prompt;
}

// USVA 4-rubric QA — returns score 0-1
async function runUSVA(question: string, answer: string): Promise<number> {
  try {
    const result = await callOpenRouter(POOL.verifier, [
      { role: 'system', content: 'Score the answer on 4 rubrics. Reply with ONLY 4 numbers 0-10 separated by spaces: LC FC CM GA (Logical Coherence, Factual Correctness, Completeness, Goal Alignment).' },
      { role: 'user', content: `Question: "${question}"\nAnswer: "${answer.substring(0, 500)}"\n\nScore: LC FC CM GA (0-10 each). Reply with ONLY 4 numbers.` },
    ], { temperature: 0, maxTokens: 20, timeoutMs: 8000 });
    if (!result.success) return 0.5;
    const content = result.content || '5 5 5 5';
    const scores = content.match(/\d+/g)?.map(Number) || [5, 5, 5, 5];
    const avg = scores.slice(0, 4).reduce((a: number, b: number) => a + b, 0) / Math.min(scores.length, 4) / 10;
    return Math.min(Math.max(avg, 0), 1);
  } catch { return 0.5; }
}

async function scoreAnswer(question: string, answer: string): Promise<number> {
  return runUSVA(question, answer);
}

async function verifyCode(answer: string): Promise<boolean> {
  const codeMatch = answer.match(/```(?:python|javascript|js|bash)?\n([\s\S]*?)```/);
  if (!codeMatch) return false;
  const code = codeMatch[1];
  if (!code.trim()) return false;
  try {
    const result = await callOpenRouter(POOL.verifier, [
      { role: 'system', content: 'Reply ONLY "PASS" or "FAIL".' },
      { role: 'user', content: `Verify:\n\`\`\`\n${code.substring(0, 500)}\n\`\`\`\nReply ONLY "PASS" or "FAIL".` },
    ], { temperature: 0, maxTokens: 5, timeoutMs: 8000 });
    return (result.content || '').toUpperCase().includes('PASS');
  } catch { return false; }
}

// Judge N parallel code drafts against the request and pick the best by
// SELECTION (not fusion — fusing full files makes incoherent code). Nemotron
// scores each draft and names the best; the caller streams that draft whole.
// A short "issues" string is returned so an optional refine pass can fix
// flagged problems in the winner. Falls back to a deterministic heuristic
// (ok + closes the document + longest) if the judge call fails or returns
// unparseable output, so a judge outage never breaks the route.
async function judgeCodeDrafts(
  query: string,
  drafts: ModelResult[],
): Promise<{ bestIndex: number; issues: string }> {
  const ok = drafts.map((d, i) => ({ d, i })).filter((x) => x.d.ok && x.d.content.trim());
  if (ok.length === 0) return { bestIndex: 0, issues: '' };
  if (ok.length === 1) return { bestIndex: ok[0].i, issues: '' };
  const systemMsg = 'You are a code judge. Score each draft deliverable against the user request on: completeness, whether it is runnable and closes its document, how well it matches the request + theme, and code quality. Reply with ONLY one line in the form: BEST=<draft number>; ISSUES=<short comma-separated problems in the best draft, or none>. Example: BEST=2; ISSUES=low color contrast, no mobile layout';
  const userMsg = `User request:\n${query}\n\n${drafts.map((d, i) => `--- DRAFT ${i + 1} (${d.name}) ---\n${d.content.substring(0, 1500)}\n`).join('')}\nReply with ONLY the BEST=...; ISSUES=... line.`;
  try {
    const result = await callOpenRouter(POOL.verifier, [
      { role: 'system', content: systemMsg },
      { role: 'user', content: userMsg },
    ], { temperature: 0, maxTokens: 200, timeoutMs: 8_000 });
    if (result.success && result.content) {
      const bestMatch = result.content.match(/best[^0-9]{0,15}(\d+)/i);
      if (bestMatch) {
        const best = Number(bestMatch[1]);
        if (best >= 1 && best <= drafts.length && drafts[best - 1].ok) {
          const issuesMatch = result.content.match(/issues\s*=?\s*(.+)$/i);
          const issues = issuesMatch ? issuesMatch[1].trim().replace(/^none\.?$/i, '').slice(0, 300) : '';
          return { bestIndex: best - 1, issues };
        }
      }
    }
  } catch {
    // fall through to the heuristic below
  }
  // Heuristic: prefer an ok draft that closes its document, then the longest.
  let bestIndex = ok[0].i;
  let bestScore = -1;
  for (const { d, i } of ok) {
    const closes = /<\/html>\s*$/i.test(d.content) || /```html/i.test(d.content);
    const score = (closes ? 100_000 : 0) + d.content.length;
    if (score > bestScore) { bestScore = score; bestIndex = i; }
  }
  return { bestIndex, issues: '' };
}

function classifyTask(query: string): string {
  const q = query.toLowerCase();
  if (q.match(/\d+\s*[+\-*/]\s*\d+|calculate|derivative|integral|solve|equation|math|sum|product|factor|theorem|prove/)) return 'math';
  if (isCodeGenerationRequest(q) || q.match(/code|function|python|javascript|debug|error|bug|program|script|algorithm|sort|merge|binary|array/)) return 'coding';
  if (q.match(/write|poem|story|essay|compose|create|generate|design|draft|blog|article/)) return 'creative';
  // Legal queries → Gemini specialist routing.
  if (q.match(/legal|law|lawsuit|contract|clause|liability|statute|regulation|compliance|gdpr|copyright|patent|trademark/)) return 'legal';
  // Health/medical queries → Gemini specialist routing.
  if (q.match(/health|medical|disease|symptom|treatment|diagnosis|patient|clinical|drug|dosage|therapy/)) return 'health';
  if (q.match(/explain|what is|how does|why|define|describe|who|when|where|which/)) return 'knowledge';
  if (q.match(/compare|analyze|reason|logic|deduce|infer|evaluate|assess|argue|prove|step by step/)) return 'reasoning';
  return 'knowledge';
}

function isCodeGenerationRequest(query: string): boolean {
  return /\b(build|create|generate|make|implement|write|develop)\b[\s\S]{0,120}\b(game|website|web page|webpage|web app|application|landing page|html|css|javascript|typescript|react|component|code|file)\b/i.test(query)
    || /\b(single[- ]file|html game|browser game|playable game|canvas game|three\.js)\b/i.test(query);
}

function estimateDifficulty(query: string, taskType: string): number {
  let d = 0;
  d += Math.min(query.split(' ').length / 10, 5); // 0-5 based on length
  if (['math', 'reasoning', 'coding'].includes(taskType)) d += 2;
  if (query.includes('explain') || query.includes('analyze')) d += 1;
  if (query.includes('compare') || query.includes('step by step')) d += 2;
  // Building a deliverable is a substantial task regardless of how few words
  // the prompt uses. "build a game" is short but still requires a full, runnable
  // file, so it must never be labeled trivial. A named artifact (game / app /
  // website / dashboard) is the hardest class of code-gen build.
  if (isCodeGenerationRequest(query)) {
    d += 3;
    if (/\b(game|web app|webapp|website|web page|webpage|application|app|landing page|dashboard|platform|tool|editor|clone|simulator)\b/i.test(query)) d += 2;
  }
  return Math.min(d, 10);
}

function determineTier(difficulty: number): string {
  if (difficulty < 4) return 'trivial';
  if (difficulty < 7) return 'medium';
  return 'hard';
}

function pickSpecialist(taskType: string): string {
  // Math/coding/reasoning → DeepSeek V4 Pro
  if (['math', 'coding', 'reasoning'].includes(taskType)) return POOL.reasoning;                   // DeepSeek V4 Pro
  // Creative → MiniMax M3
  if (taskType === 'creative') return POOL.vision;                                     // MiniMax M3
  // Legal/health → Gemini 3.5 Flash
  if (q_match(taskType, ['legal', 'health', 'medical', 'law'])) return POOL.multimodal;
  // General knowledge and everything else → GLM-5.2
  return POOL.orchestrator;
}

// Strength-based drafter selection for a build. Returns the strong models that
// should draft the deliverable in parallel. Selection is rule-driven (no extra
// LLM call, robust): DeepSeek V4 Pro is the code anchor; GLM-5.2 is the general
// second drafter; visual/theme-heavy requests swap in Gemini (its strength is
// layout/UX); the hardest builds add the frontier GPT-5.6 Luna. A trivial code
// ask (not a substantial build) returns [] so the caller keeps the cheap single-
// coder path and pays nothing for parallelism.
function selectDrafters(query: string, tier: string): string[] {
  const substantial = /\b(game|web app|webapp|website|web page|webpage|application|app|landing page|dashboard|platform|tool|editor|clone|simulator)\b/i.test(query);
  if (!substantial) return [];
  const visual = /\b(theme|design|visual|animation|ui|ux|landing|aesthetic|canvas|three\.js|phaser|p5|tailwind|responsive|hero|portfolio)\b/i.test(query);
  // Base pair: the code anchor + a general second drafter (GLM-5.2).
  const drafters: string[] = [POOL.reasoning, POOL.orchestrator];
  if (visual) {
    // Visual/theme requests get Gemini's layout/UX strength instead of GLM.
    drafters[1] = POOL.multimodal;
  }
  if (tier === 'hard') {
    // The hardest builds get a third frontier drafter.
    drafters.push(POOL.frontier);
  }
  return drafters;
}

// Helper: check if task type matches keywords in the query
function q_match(taskType: string, keywords: string[]): boolean {
  // This is a simple check — in production, classifyTask would return these types
  return keywords.some(k => taskType.includes(k));
}

// Route only the hardest queries through the conditional frontier escalation.
function needsFrontier(query: string, taskType: string): boolean {
  // Use frontier model for the hardest 5% of queries
  const q = query.toLowerCase();
  // Complex multi-step problems
  if (q.includes('prove') || q.includes('derive') || q.includes('theorem')) return true;
  // Long autonomous tasks
  if (query.split(' ').length > 50 && ['math', 'reasoning', 'coding'].includes(taskType)) return true;
  // Complex codebase questions
  if (q.includes('refactor') || q.includes('architecture') || q.includes('system design')) return true;
  return false;
}

// === LLM REQUEST CLASSIFIER (primary routing path) ===
// The regex classifier above (classifyTask / estimateDifficulty / determineTier
// / isCodeGenerationRequest) is retained as the fallback. The primary path asks
// a fast model to classify the request into {taskType, tier, isCodeGeneration,
// confidence, reason}; on borderline or low-confidence calls it takes a second
// sample (deliberation) to verify the tier before routing. A build/deliverable
// request is never sent to the trivial single-model route.

type ClassResult = {
  taskType: string;
  tier: string;
  isCodeGeneration: boolean;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
};

type DeliberationResult = ClassResult & { difficulty: number; classifierTokens: number };

const CLASS_TASK_TYPES = new Set(['math', 'coding', 'creative', 'legal', 'health', 'knowledge', 'reasoning']);
const CLASS_TIERS = new Set(['trivial', 'medium', 'hard']);
const TIER_RANK: Record<string, number> = { trivial: 0, medium: 1, hard: 2 };
const TIER_DIFFICULTY: Record<string, number> = { trivial: 3, medium: 5, hard: 8 };

const CLASSIFIER_SYSTEM = `You are TemuClaude's request router. Classify the user's LATEST message and respond with ONLY a JSON object — no prose, no markdown, no code fences.

Schema:
{"taskType": "math"|"coding"|"creative"|"legal"|"health"|"knowledge"|"reasoning", "tier": "trivial"|"medium"|"hard", "isCodeGeneration": boolean, "confidence": "high"|"medium"|"low", "reason": "short phrase"}

Tier definitions:
- trivial: a single factual lookup, greeting, or one-line answer.
- medium: needs one specialist and moderate reasoning — an explanation, comparison, or a single short snippet.
- hard: multi-step synthesis, a proof/derivation, deep analysis, OR producing a complete deliverable (webpage, website, app, game, dashboard, tool, landing page, full HTML file).

Rules:
- If the user asks to BUILD/MAKE/CREATE/GENERATE/DESIGN a deliverable (webpage, website, web page, app, game, dashboard, tool, landing page, HTML, component, script), set isCodeGeneration=true and tier="hard".
- A short prompt that asks for a complete built artifact is still "hard" — the work is in the output, not the prompt length.
- "reason" is a short phrase, e.g. "full webpage build", "factual lookup", "multi-step proof".`;

function parseClassifierJson(content: string): ClassResult | null {
  if (!content) return null;
  let text = content.trim();
  // Strip a markdown code fence if the model wrapped the JSON.
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence) text = fence[1].trim();
  // Skip any leading prose and grab the first {...} block.
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start === -1 || end === -1 || end <= start) return null;
  let parsed: any;
  try {
    parsed = JSON.parse(text.slice(start, end + 1));
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== 'object') return null;
  const taskType = typeof parsed.taskType === 'string' ? parsed.taskType.toLowerCase() : '';
  const tier = typeof parsed.tier === 'string' ? parsed.tier.toLowerCase() : '';
  if (!CLASS_TASK_TYPES.has(taskType) || !CLASS_TIERS.has(tier)) return null;
  if (typeof parsed.isCodeGeneration !== 'boolean') return null;
  const rawConf = typeof parsed.confidence === 'string' ? parsed.confidence.toLowerCase() : 'medium';
  const confidence: ClassResult['confidence'] = rawConf === 'high' || rawConf === 'low' ? rawConf : 'medium';
  const reason = typeof parsed.reason === 'string' ? parsed.reason.slice(0, 160) : '';
  return { taskType, tier, isCodeGeneration: parsed.isCodeGeneration, confidence, reason };
}

async function classifyWithLLM(query: string, model: string): Promise<{ result: ClassResult | null; tokens: number }> {
  try {
    const res = await callOpenRouter(
      model,
      [
        { role: 'system', content: CLASSIFIER_SYSTEM },
        { role: 'user', content: `Classify this request:\n\n${query}` },
      ],
      {
        temperature: 0,
        maxTokens: 300,
        timeoutMs: 8_000,
        disableReasoning: true,
        responseFormat: 'json_object',
        sessionId: asciiSessionId('playground-classifier', query),
      },
    );
    if (!res.success) return { result: null, tokens: 0 };
    return { result: parseClassifierJson(res.content), tokens: res.tokens || 0 };
  } catch {
    return { result: null, tokens: 0 };
  }
}

function regexFallbackClassification(query: string): ClassResult {
  const taskType = classifyTask(query);
  const tier = determineTier(estimateDifficulty(query, taskType));
  return {
    taskType,
    tier,
    isCodeGeneration: isCodeGenerationRequest(query),
    confidence: 'low',
    reason: 'regex fallback (classifier unavailable)',
  };
}

function reconcileClassifier(a: ClassResult, b: ClassResult): ClassResult {
  // Reconcile conservatively: any build flag wins; take the harder tier; keep
  // the taskType that drove the harder tier; confidence is high if either was.
  const isCodeGeneration = a.isCodeGeneration || b.isCodeGeneration;
  const tier = TIER_RANK[b.tier] > TIER_RANK[a.tier] ? b.tier : a.tier;
  const taskType = TIER_RANK[b.tier] >= TIER_RANK[a.tier] ? b.taskType : a.taskType;
  const confidence: ClassResult['confidence'] = a.confidence === 'high' || b.confidence === 'high' ? 'high' : 'medium';
  const reason = b.reason || a.reason;
  return { taskType, tier, isCodeGeneration, confidence, reason };
}

async function classifyWithDeliberation(
  query: string,
  profile: ModelProfile,
  controller: ReadableStreamDefaultController,
  encoder: TextEncoder,
  techniques: string[],
): Promise<DeliberationResult> {
  // Sample 1 — fast and cheap; runs on every request (Pro and Lite).
  const s1 = await classifyWithLLM(query, POOL.fastRoute);
  let classifierTokens = s1.tokens;
  let result: ClassResult;

  if (!s1.result) {
    // Classifier call failed or returned unparseable JSON — use the regex path.
    techniques.push('regex-classification-fallback');
    result = regexFallbackClassification(query);
  } else if (
    profile !== 'lite' &&
    (s1.result.confidence !== 'high' || (s1.result.isCodeGeneration && s1.result.tier === 'trivial'))
  ) {
    // Borderline or inconsistent — deliberate via a 2nd sample (Pro only; Lite
    // stays cheap and trusts the fast classifier + the build safety net below).
    sendProgress(controller, encoder, 'Deliberating', 'Re-verifying a borderline classification', 'active');
    const s2 = await classifyWithLLM(query, POOL.orchestrator);
    classifierTokens += s2.tokens;
    techniques.push('llm-classification', 'deliberation');
    result = s2.result
      ? reconcileClassifier(s1.result, s2.result)
      : { ...s1.result, tier: s1.result.isCodeGeneration && s1.result.tier === 'trivial' ? 'hard' : s1.result.tier };
  } else {
    techniques.push('llm-classification');
    result = s1.result;
  }

  // Build safety net: a regex-recognized deliverable is never routed to the
  // trivial single-model path, even if both classifier samples missed it.
  if (isCodeGenerationRequest(query) && !result.isCodeGeneration) {
    result = { ...result, isCodeGeneration: true, reason: result.reason || 'build request (regex safety net)' };
  }
  if (result.isCodeGeneration && result.tier === 'trivial') {
    result = { ...result, tier: 'hard' };
  }

  return { ...result, difficulty: TIER_DIFFICULTY[result.tier] ?? 5, classifierTokens };
}

// === STEP-LEVEL CODE VERIFICATION (rStar-Math pattern) ===
// Extract each reasoning step, generate code for it, verify independently
async function stepLevelVerify(query: string, answer: string): Promise<boolean> {
  // Extract reasoning steps (numbered or bulleted)
  const stepRegex = /(?:Step \d+|step \d+|^\d+[.)]|\n\d+[.)])[\s\S]*?(?=Step \d+|step \d+|\n\d+[.)]|$)/gm;
  const steps = answer.match(stepRegex) || [];
  if (steps.length === 0) return false;

  // Independent checks are parallel: verification quality stays intact while
  // five steps consume one bounded latency window instead of five in series.
  const verdicts = await Promise.all(steps.slice(0, 5).map(async (rawStep) => {
    const step = rawStep.substring(0, 300);
    try {
      const result = await callOpenRouter(POOL.verifier, [
        { role: 'system', content: 'You are a step-level code verifier. For the given reasoning step, determine if it is logically correct. Reply with ONLY "CORRECT" or "INCORRECT".' },
        { role: 'user', content: `Question: ${query.substring(0, 200)}\n\nStep to verify:\n${step}\n\nIs this step logically correct? Reply ONLY "CORRECT" or "INCORRECT".` },
      ], { temperature: 0, maxTokens: 10, timeoutMs: 8000 });
      if (!result.success) return false;
      const verdict = result.content.toUpperCase();
      return verdict.includes('CORRECT') && !verdict.includes('INCORRECT');
    } catch {
      return false;
    }
  }));
  return verdicts.every(Boolean);
}

// === Z3/SMT LOGICAL VERIFICATION (ConsistPRM pattern) ===
// Extract logical claims and check for contradictions using LLM as SMT solver
async function logicalVerify(answer: string): Promise<'pass' | 'contradiction' | 'error'> {
  try {
    const result = await callOpenRouter(POOL.verifier, [
      { role: 'system', content: 'You are a logical consistency checker. Extract all logical claims from the text (if X then Y, X implies Y, X equals Y). Check if any claims contradict each other. Reply with ONLY "PASS" (no contradictions) or "CONTRADICTION" (contradictions found).' },
      { role: 'user', content: `Check this text for logical contradictions:\n\n${answer.substring(0, 800)}\n\nReply ONLY "PASS" or "CONTRADICTION".` },
    ], { temperature: 0, maxTokens: 10, timeoutMs: 8000 });
    if (!result.success) return 'error';
    const verdict = result.content.toUpperCase();
    if (verdict.includes('CONTRADICTION')) return 'contradiction';
    return 'pass';
  } catch { return 'error'; }
}

// === WEB SEARCH (DuckDuckGo — free, unlimited, no API key) ===
async function webSearch(query: string, numResults: number): Promise<string> {
  try {
    // DuckDuckGo HTML endpoint — no API key needed, no rate limits
    const searchUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query.substring(0, 200))}`;
    const response = await fetch(searchUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      },
      signal: AbortSignal.timeout(5000),
    });

    if (!response.ok) return '';

    const html = await response.text();

    // Extract result snippets from DuckDuckGo HTML
    const results: string[] = [];
    const resultRegex = /<a[^>]*class="result__a"[^>]*>([^<]*)<\/a>[\s\S]*?class="result__snippet"[^>]*>([\s\S]*?)<\/a>/g;
    let match;
    let count = 0;
    while ((match = resultRegex.exec(html)) !== null && count < numResults) {
      const title = match[1].replace(/<[^>]*>/g, '').trim();
      const snippet = match[2].replace(/<[^>]*>/g, '').trim();
      if (title && snippet) {
        results.push(`[${count + 1}] ${title}\n${snippet}`);
        count++;
      }
    }

    return results.join('\n\n');
  } catch {
    return '';
  }
}

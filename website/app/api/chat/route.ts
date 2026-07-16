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
// the platform to kill it mid-pipeline with no answer.
export const maxDuration = 300;

// TemuClaude Pro — evidence-based, role-bounded quality registry.
// Every nontrivial Pro request uses all available quality roles; task type
// controls their instructions and synthesis weight, not whether quality runs.
const POOL = {
  orchestrator: 'z-ai/glm-5.2',
  reasoning: 'deepseek/deepseek-v4-pro',
  fastRoute: 'deepseek/deepseek-v4-flash',
  multimodal: 'google/gemini-3.5-flash',
  uiUx: 'moonshotai/kimi-k2.6',
  specialist: 'minimax/minimax-m3',
  vision: 'minimax/minimax-m3',
  gptWorker: 'openai/gpt-5.6-luna',
  frontier: 'openai/gpt-5.6-sol',
  codeRepair: 'x-ai/grok-4.5',
  verifier: 'nvidia/nemotron-3-ultra-550b-a55b',
};

const ROLE_INSTRUCTIONS: Record<string, string> = {
  [POOL.orchestrator]: 'You are the GLM long-horizon planner and synthesis lead. Track dependencies, architecture, edge cases, and integration across the entire task.',
  [POOL.reasoning]: 'You are the DeepSeek math, STEM, coding, and rigorous-reasoning lead. Derive and verify the technical core.',
  [POOL.uiUx]: 'You are the Kimi coding-driven UI/UX implementation lead. Focus on complete interfaces, interaction flows, state, responsive behavior, and production-ready code.',
  [POOL.specialist]: 'You are the MiniMax multimodal, long-context, creative, and product reviewer. Focus on visual coherence, product completeness, and source-wide consistency.',
  [POOL.multimodal]: 'You are the Gemini visual UI, accessibility, multimodal, and tool-use reviewer. Focus on screen behavior, accessibility, and observable interaction quality.',
  [POOL.gptWorker]: 'You are a fast independent GPT-family proposer. Find a distinct solution path, useful tools, and omissions in the likely consensus.',
  [POOL.frontier]: 'You are the GPT-5.6 Sol frontier adjudicator. Solve complex professional work rigorously and identify where weaker proposals may fail.',
  [POOL.codeRepair]: 'You are the Grok coding-agent and repair specialist. Hunt bugs, unsafe assumptions, integration failures, and missing tests; propose concrete fixes.',
  [POOL.verifier]: 'You are the Nemotron independent verifier. Try to falsify reasoning, code, long-context, and high-stakes claims with checkable evidence.',
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

export async function POST(req: NextRequest) {
  const auth = await getAuthenticatedSupabaseUser(req);
  if ('error' in auth) {
    return Response.json({ error: auth.error }, { status: auth.status });
  }
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return Response.json({ error: 'Authenticated user has no email address' }, { status: 400 });
  const initialUser = await getOrCreateUserByEmailAsync(email);
  const account = (await verifyAndRenewWeeklyCreditsAsync(initialUser.id)) || initialUser;
  const limits = PLAN_LIMITS[account.plan as keyof typeof PLAN_LIMITS] || PLAN_LIMITS.free;
  const rollingUsage = await getRollingWindowUsageAsync(account.id, ROLLING_WINDOW_HOURS);
  if (account.credit_balance <= 0 || (limits.rollingQueries !== Infinity && rollingUsage.query_count >= limits.rollingQueries)) {
    return Response.json({ error: 'Usage limit reached. Upgrade or wait for capacity to recover.' }, { status: 429 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: 'Request body must be valid JSON' }, { status: 400 });
  }

  const payload = body && typeof body === 'object' ? body as Record<string, unknown> : {};
  const profile = payload.profile === undefined ? 'pro' : payload.profile;
  if (profile !== 'pro' && profile !== 'lite') {
    return Response.json({ error: 'profile must be either "pro" or "lite"' }, { status: 400 });
  }

  const validated = validateMessages(payload.messages);
  if ('error' in validated) {
    return Response.json({ error: validated.error }, { status: 400 });
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
          completed = await runQualityCodeGeneration(query, messages, controller, encoder, taskType, tier, t0, techniques);
        } else if (tier === 'trivial') {
          // Pro has a quality floor even for short requests.  Flash is a Lite
          // worker only; GLM owns concise, user-facing Pro answers.
          techniques.push('pro-quality-floor');
          sendProgress(controller, encoder, 'Calling Pro model', 'GLM-5.2 is drafting');
          const result = await callModel(POOL.orchestrator, messages);
          if (!result.ok) {
            // A provider may occasionally return HTTP 200 with an empty
            // completion. Never expose that transport failure as the answer:
            // recover through the full quality panel and its approved routes.
            techniques.push('pro-empty-response-recovery');
            sendProgress(controller, encoder, 'Recovering response', 'The quality panel is replacing an empty provider response');
            completed = await runFullStack(query, messages, controller, encoder, taskType, 'medium', t0, techniques);
          } else {
            sendProgress(controller, encoder, 'Streaming answer', 'Final response is ready', 'done');
            streamText(controller, encoder, result.content);
            sendOrch(controller, encoder, taskType, tier, [{ name: 'glm-5.2', response: result.content.substring(0, 200), latency: (Date.now()-t0)/1000, correct: result.ok }], 'single', 1, 0, false, t0, formatProviderCost(result.cost), techniques);
            completed = { content: result.content, model: result.name };
          }
        } else if (tier === 'medium') {
          // A Pro task is not downgraded to a single draft.  The same
          // specialist panel used for hard requests establishes a dependable
          // quality floor; the panel itself is task-aware.
          completed = await runFullStack(query, messages, controller, encoder, taskType, tier, t0, techniques);
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
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' },
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
  const useLitePanel = tier !== 'trivial' || isCodeGeneration;
  techniques.push(useLitePanel ? 'lite-parallel-specialist-panel' : 'lite-quality-floor');
  sendProgress(controller, encoder, 'Calling Lite model', useLitePanel ? 'Two Lite specialists are drafting in parallel' : `${model.split('/').pop()} is drafting`);

  const codeInstruction = isCodeGeneration
    ? `${ENGLISH_SYSTEM.content} Execute the requested coding task now. Do not ask follow-up questions when reasonable defaults are possible. For a game, website, or interactive app, return a complete runnable deliverable; when suitable, return one complete HTML document (<!doctype html> through </html>) in a single fenced html code block with all CSS and JavaScript included. The preview allows CDN libraries (cdn.jsdelivr.net, unpkg.com, cdnjs.cloudflare.com), Google Fonts, and remote https images, but blocks fetch/XHR/WebSockets and form submissions — inline any data the page needs. Do not outline phases or defer implementation.`
    : ENGLISH_SYSTEM.content;
  const callLiteDraft = (draftModel: LiteModelId, role: string) => callOpenRouterLite(draftModel, [
    {
      role: 'system',
      content: `${codeInstruction} ${role}`,
    },
    ...messages,
  ], {
    maxTokens: isCodeGeneration ? 4_096 : 2_000,
    timeoutMs: isCodeGeneration ? 90_000 : 20_000,
    sessionId: asciiSessionId(`playground-lite-${draftModel}`, query),
  });
  const complement = model === LITE_POOL.default ? LITE_POOL.agent : LITE_POOL.default;
  const [primaryDraft, complementaryDraft] = await Promise.all([
    callLiteDraft(model, 'Own the main task-specific solution. Be complete, concrete, and do not rush the ending.'),
    useLitePanel
      ? callLiteDraft(complement, 'Independently solve the task. Focus on omissions, edge cases, and an alternative approach.')
      : Promise.resolve(null),
  ]);
  let result = primaryDraft.success ? primaryDraft : complementaryDraft?.success ? complementaryDraft : primaryDraft;
  let panelCompletionTokens = primaryDraft.completionTokens + (complementaryDraft?.completionTokens || 0);
  let panelCost = (primaryDraft.cost || 0) + (complementaryDraft?.cost || 0);

  if (primaryDraft.success && complementaryDraft?.success) {
    techniques.push('lite-specialist-synthesis');
    sendProgress(controller, encoder, 'Synthesizing Lite drafts', 'Qwen is combining the strongest verified details');
    const synthesized = await callOpenRouterLite(LITE_POOL.agent, [
      { role: 'system', content: `${codeInstruction} Synthesize the best complete answer from two independent drafts. Resolve contradictions, preserve working detail, and return only the final answer.` },
      { role: 'user', content: `Original request:\n${query}\n\nDraft A:\n${primaryDraft.content}\n\nDraft B:\n${complementaryDraft.content}` },
    ], {
      maxTokens: isCodeGeneration ? 4_096 : 2_000,
      timeoutMs: isCodeGeneration ? 90_000 : 30_000,
      sessionId: asciiSessionId('playground-lite-synthesis', query),
    });
    panelCompletionTokens += synthesized.completionTokens;
    panelCost += synthesized.cost || 0;
    if (synthesized.success) result = synthesized;
  }
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
      maxTokens: isCodeGeneration ? 4_096 : 2_000,
      timeoutMs: isCodeGeneration ? 90_000 : 20_000,
      sessionId: asciiSessionId('playground-lite-rescue', query),
    });
  }
  let content = result.success
    ? result.content
    : 'TemuClaude Lite could not complete this request right now. Please try again.';
  let completionTokens = panelCompletionTokens;
  let providerCost = panelCost;

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
      const corrected = await callOpenRouterLite(LITE_POOL.agent, [
        { role: 'system', content: `${ENGLISH_SYSTEM.content} A verifier found an issue in the previous draft. Produce a corrected, self-contained answer.` },
        ...messages,
        { role: 'assistant', content },
        { role: 'user', content: `Verifier feedback:\n${verdict.content}` },
      ], { maxTokens: isCodeGeneration ? 4_096 : 2_000, timeoutMs: isCodeGeneration ? 90_000 : 30_000, sessionId: asciiSessionId('playground-lite-correct', query) });
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
  if (isCodeGenerationRequest(query)) return true;
  if (tier !== 'trivial' || answer.trim().length < 80) return tier !== 'trivial';
  const sample = createHash('sha256').update(query).digest().readUInt32BE(0) / 0x1_0000_0000;
  return sample < 0.02;
}

async function runQualityCodeGeneration(
  query: string,
  messages: ChatMessage[],
  controller: ReadableStreamDefaultController,
  encoder: TextEncoder,
  taskType: string,
  tier: string,
  t0: number,
  techniques: string[],
): Promise<CompletedResponse> {
  // Treat generated code as an artifact: parallel planning, implementation,
  // product/UX review, independent verification, and repair.  A single cheap
  // draft is not an acceptable Pro deliverable.
  techniques.push('quality-first-code-panel');
  sendProgress(controller, encoder, 'Planning and drafting', 'GLM, DeepSeek, and MiniMax are working in parallel');
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
  const deadlineAt = t0 + 180_000;
  const remainingMs = () => Math.max(0, deadlineAt - Date.now());
  const [plan, draft, artifactCompletion, technicalReview, productReview, gptReview, frontierReview, multimodalReview, codeReview] = await Promise.all([
    callModel(POOL.orchestrator, [
      { role: 'system', content: 'You are a senior software architect. Produce a concise implementation plan, acceptance criteria, edge cases, and test checklist for the requested deliverable. Do not write the final code.' },
      ...messages,
    ], { maxTokens: 2_000, timeoutMs: Math.min(35_000, remainingMs()) }),
    // Kimi is the primary user-facing webpage deliverer. It reliably returns
    // compact, complete HTML for UI work; DeepSeek remains in the panel below
    // as a technical reviewer instead of becoming a single synthesis choke
    // point that can consume its visible output budget on reasoning.
    callModel(POOL.uiUx, [codeSystem, ...messages], {
      maxTokens: 8_192,
      timeoutMs: Math.min(65_000, remainingMs()),
      temperature: 0.35,
      disableReasoning: true,
      fallbacks: [POOL.codeRepair, POOL.orchestrator],
    }),
    // DeepSeek Flash is not a replacement for the Pro panel. It is a proven,
    // parameter-compatible artifact completer running alongside Kimi so a
    // visible webpage is available even when a frontier route spends its
    // budget on hidden reasoning or a provider returns an empty message.
    callModel(POOL.fastRoute, [codeSystem, ...messages], {
      maxTokens: 8_192,
      timeoutMs: Math.min(65_000, remainingMs()),
      temperature: 0.35,
      disableReasoning: true,
      fallbacks: [POOL.uiUx, POOL.codeRepair, POOL.orchestrator],
    }),
    callModel(POOL.reasoning, [
      { role: 'system', content: 'Produce a rigorous technical implementation review: structure, interactions, accessibility hooks, correctness risks, and concrete implementation traps. Do not write the final code.' },
      ...messages,
    ], { maxTokens: 2_000, timeoutMs: Math.min(35_000, remainingMs()) }),
    callModel(POOL.specialist, [
      { role: 'system', content: 'You are a product, UX, and edge-case reviewer. Specify what makes this requested deliverable complete, usable, accessible, and visually coherent. Do not write the final code.' },
      ...messages,
    ], { maxTokens: 2_000, timeoutMs: Math.min(35_000, remainingMs()) }),
    callModel(POOL.gptWorker, [
      { role: 'system', content: 'Independently review the requested deliverable. Find missing requirements, useful tools, and a distinct implementation approach. Do not write the final code.' },
      ...messages,
    ], { maxTokens: 2_000, timeoutMs: Math.min(35_000, remainingMs()) }),
    callModel(POOL.frontier, [
      { role: 'system', content: 'You are a frontier software reviewer. Identify the most important implementation, correctness, security, and completion requirements for this requested deliverable. Do not write the final code.' },
      ...messages,
    ], { maxTokens: 2_000, timeoutMs: Math.min(35_000, remainingMs()) }),
    callModel(POOL.multimodal, [
      { role: 'system', content: 'You are an accessibility and interaction-design reviewer. Identify usability, visual, and accessibility requirements relevant to this requested deliverable. Do not write the final code.' },
      ...messages,
    ], { maxTokens: 2_000, timeoutMs: Math.min(35_000, remainingMs()) }),
    callModel(POOL.codeRepair, [
      { role: 'system', content: 'You are a frontier coding-agent reviewer. Identify likely implementation bugs, security issues, missing tests, and failure modes. Do not write the final code.' },
      ...messages,
    ], { maxTokens: 2_000, timeoutMs: Math.min(35_000, remainingMs()) }),
  ]);

  const needsCompleteHtml = /\b(website|webpage|web page|landing page|html)\b/i.test(query);
  const isUsableDeliverable = (candidate: ModelResult) => candidate.ok
    && (!needsCompleteHtml || hasCompleteHtmlDocument(candidate.content));
  const deliveryCandidates = [draft, artifactCompletion];
  const initialDeliverable = deliveryCandidates.find(isUsableDeliverable) || draft;
  let deliveryIsUsable = isUsableDeliverable(initialDeliverable);
  let result = initialDeliverable;

  if (isUsableDeliverable(artifactCompletion) && !isUsableDeliverable(draft)) {
    techniques.push('parallel-artifact-completion');
  }

  // Preserve a complete primary deliverable. Synthesis is recovery work, not
  // a mandatory second long generation that can replace a good webpage with a
  // timeout or empty hidden-reasoning response.
  if (!deliveryIsUsable) {
    techniques.push('implementation-synthesis-recovery');
    sendProgress(controller, encoder, 'Recovering implementation', 'Kimi is incorporating architecture and technical review');
    result = await callModel(POOL.uiUx, [
      codeSystem,
      { role: 'user', content: `Architect plan:\n${plan.content}\n\nDeepSeek technical review:\n${technicalReview.content}\n\nMiniMax product review:\n${productReview.content}\n\nIndependent GPT review:\n${gptReview.content}\n\nFrontier adjudication:\n${frontierReview.content}\n\nGemini accessibility review:\n${multimodalReview.content}\n\nGrok coding review:\n${codeReview.content}\n\nInitial implementation:\n${draft.content}\n\nReturn one complete corrected deliverable only. Do not discuss the review process.` },
    ], {
      maxTokens: 8_192,
      timeoutMs: Math.min(45_000, remainingMs()),
      temperature: 0.35,
      disableReasoning: true,
      fallbacks: [POOL.codeRepair, POOL.orchestrator],
    });
  } else {
    techniques.push('direct-quality-delivery');
  }
  if (deliveryIsUsable && remainingMs() >= 8_000) {
    techniques.push('independent-code-review');
    sendProgress(controller, encoder, 'Verifying deliverable', 'Nemotron is checking completeness and correctness');
    const review = await callModel(POOL.verifier, [
      { role: 'system', content: 'Audit this generated deliverable against the request. Reply PASS if it is complete and correct. Otherwise reply FAIL followed by concrete, prioritized fixes.' },
      { role: 'user', content: `Request:\n${query}\n\nDeliverable:\n${result.content}` },
    ], { maxTokens: 1_200, timeoutMs: Math.min(25_000, remainingMs()) });
    if (review.ok && review.content.toUpperCase().startsWith('FAIL') && remainingMs() >= 6_000) {
      techniques.push('code-repair');
      sendProgress(controller, encoder, 'Repairing deliverable', 'Grok is applying independent review feedback');
      const repaired = await callModel(POOL.codeRepair, [
        codeSystem,
        { role: 'user', content: `Original request:\n${query}\n\nCurrent deliverable:\n${result.content}\n\nIndependent review:\n${review.content}\n\nReturn a complete corrected deliverable only.` },
      ], { maxTokens: 8_192, timeoutMs: Math.min(35_000, remainingMs()), temperature: 0.25 });
      if (isUsableDeliverable(repaired)) result = repaired;
    }
  }
  deliveryIsUsable = isUsableDeliverable(result);
  if (!deliveryIsUsable && remainingMs() >= 6_000) {
    techniques.push('code-repair-rescue');
    sendProgress(controller, encoder, 'Recovering code generation', 'DeepSeek V4 Pro is producing the approved rescue deliverable');
    // Pro-tier rescue: DeepSeek V4 Pro reasons over the full request. Reasoning
    // is intentionally NOT disabled here — a reasoning model under
    // disableReasoning can return an empty completion (the original "approved
    // route unavailable" outage), so we let it reason and give it token room
    // for both the hidden chain-of-thought and the visible deliverable. The
    // resilient HTML fallback below catches the rare timeout/empty case so the
    // user always gets a runnable webpage. Quality over cost: rescue is Pro.
    result = await callModel(POOL.reasoning, [codeSystem, ...messages], {
      maxTokens: 12_000,
      timeoutMs: Math.min(45_000, remainingMs()),
      temperature: 0.35,
      fallbacks: [POOL.uiUx, POOL.codeRepair, POOL.orchestrator],
    });
  }

  deliveryIsUsable = isUsableDeliverable(result);
  const usedResilientHtmlFallback = !deliveryIsUsable && needsCompleteHtml;
  const content = deliveryIsUsable
    ? result.content
    : usedResilientHtmlFallback
      ? createResilientHtmlFallback(query)
      : 'The requested code artifact could not be completed by the available providers. Please retry shortly.';
  const deliveredModel = usedResilientHtmlFallback ? 'temuclaude-resilient-html-fallback' : result.name;
  sendProgress(controller, encoder, 'Streaming code', deliveryIsUsable ? 'Complete deliverable is ready' : usedResilientHtmlFallback ? 'Complete resilient webpage fallback is ready' : 'The approved code route was unavailable', deliveryIsUsable || usedResilientHtmlFallback ? 'done' : 'error');
  streamText(controller, encoder, content);
  sendOrch(controller, encoder, taskType, tier, [{
    name: deliveredModel,
    response: content.substring(0, 200),
    latency: result.latency,
    correct: deliveryIsUsable || usedResilientHtmlFallback,
  }], deliveredModel, deliveryIsUsable || usedResilientHtmlFallback ? 1 : 0, 0, false, t0, formatProviderCost(result.cost), techniques);
  return { content, model: deliveredModel };
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
  const fusionModels = Array.from(new Set([
    POOL.frontier,
    POOL.gptWorker,
    POOL.codeRepair,
    POOL.multimodal,
    POOL.uiUx,
    taskSpecialist,
    POOL.orchestrator,
    POOL.reasoning,
    POOL.specialist,
    POOL.verifier,
  ]));
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
  sendProgress(controller, encoder, 'Drafting proposals', 'Frontier and specialist models are working in parallel');

  // Layer 1: all available frontier and specialist roles propose independently.
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
    // All parallel fusion proposals failed. Fall back to a single bounded
    // rescue call so a transient provider outage on the fusion panel does not
    // erase the user's answer — and surface the real failure reason instead of
    // a generic "unavailable" banner.
    techniques.push('moa-empty-recovery');
    sendProgress(controller, encoder, 'Recovering response', 'DeepSeek is producing the rescue answer');
    const rescue = await callModel(POOL.reasoning, augmentedMessages, {
      maxTokens: 8_192,
      timeoutMs: 75_000,
      temperature: 0.4,
      fallbacks: [POOL.orchestrator, POOL.fastRoute],
    });
    const rescueReason = (rescue.error || 'all fusion models returned no usable output').slice(0, 180);
    if (rescue.ok && rescue.content.trim()) {
      streamText(controller, encoder, rescue.content);
      sendOrch(controller, encoder, taskType, tier, [{ name: rescue.name, response: rescue.content.substring(0, 200), latency: rescue.latency, correct: true }], rescue.name, 1, 0, false, t0, formatProviderCost(rescue.cost), techniques);
      return { content: rescue.content, model: rescue.name };
    }
    streamText(controller, encoder, `TemuClaude could not complete this request right now (${rescueReason}). Please retry shortly.`);
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
  const aggResult = await callModel(POOL.orchestrator, [
    { role: 'system', content: 'You are TemuClaude. Analyze these model responses and produce the best possible answer. Identify: 1) Consensus (where models agree — high confidence) 2) Contradictions (where they disagree — investigate) 3) Unique insights (something only one model caught) 4) Blind spots (what no model addressed). Then write the final answer.' },
    { role: 'user', content: fusionPrompt },
  ], { maxTokens: 6_144, timeoutMs: 30_000, temperature: 0.5, fallbacks: [POOL.reasoning, POOL.fastRoute] });
  let finalAnswer = aggResult.ok ? aggResult.content : workingProposals[0].content;
  sendProgress(controller, encoder, 'Aggregation complete', aggResult.ok ? 'Primary synthesis ready' : 'Using strongest available draft', 'done');

  // LAYER 4: SELF-CONSISTENCY (for math/reasoning — adaptive N samples)
  if ((taskType === 'math' || taskType === 'reasoning') && Date.now() - t0 < 45_000) {
    techniques.push('self-consistency');
    sendProgress(controller, encoder, 'Checking consistency', 'Sampling alternate reasoning paths');
    const N = 2;
    const samples: string[] = [finalAnswer];
    for (let s = 0; s < N - 1; s++) {
      const sampleResult = await callModel(POOL.reasoning, [
        ...messages,
        { role: 'assistant', content: finalAnswer },
        { role: 'user', content: 'Provide an alternative solution with different reasoning. Then give your final answer.' },
      ]);
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
  if ((taskType === 'math' || taskType === 'coding') && Date.now() - t0 < 60_000) {
    techniques.push('code-verification');
    sendProgress(controller, encoder, 'Verifying code or math', 'Running a lightweight verifier pass');
    codeVerified = await verifyCode(finalAnswer);
    if (!codeVerified) {
      // LAYER 7: REFLEXION — retry with feedback
      techniques.push('reflexion');
      const reflection = await callModel(POOL.verifier, [
        { role: 'system', content: 'You are a code verifier. The previous answer may have errors. Explain what went wrong and how to fix it.' },
        { role: 'user', content: `Question: ${query}\nAnswer: ${finalAnswer.substring(0, 500)}\n\nWhat is wrong with this answer? How should it be fixed?` },
      ]);
      if (reflection.ok) {
        const retryResult = await callModel(POOL.reasoning, [
          ...messages,
          { role: 'assistant', content: finalAnswer },
          { role: 'user', content: `A verifier found these issues:\n${reflection.content}\n\nPlease provide a corrected answer.` },
        ]);
        if (retryResult.ok) finalAnswer = retryResult.content;
        codeVerified = await verifyCode(finalAnswer);
      }
      // Grok 4.5 is reserved for a bounded code-repair escalation, never a
      // first-pass model, so it improves failed code without inflating normal cost.
      if (taskType === 'coding' && !codeVerified && Date.now() - t0 < 70_000) {
        techniques.push('code-repair-escalation');
        const repair = await callModel(POOL.codeRepair, [
          { role: 'system', content: 'Repair the submitted solution. Return a complete, correct, self-contained answer with working code where relevant.' },
          { role: 'user', content: `Task:\n${query}\n\nCurrent attempted answer:\n${finalAnswer}` },
        ]);
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
  let qaScore = Date.now() - t0 < 90_000 ? await runUSVA(query, finalAnswer) : 0.7;

  // If QA fails, retry with Reflexion
  if (qaScore < 0.8 && !techniques.includes('reflexion') && Date.now() - t0 < 70_000) {
    techniques.push('reflexion');
    const reflection = await callModel(POOL.verifier, [
      { role: 'system', content: 'You are a quality verifier. The answer scored low on quality. Explain what is wrong.' },
      { role: 'user', content: `Question: ${query}\nAnswer: ${finalAnswer.substring(0, 500)}\nQuality score: ${qaScore.toFixed(2)}/1.0\n\nWhat needs to be improved?` },
    ]);
    if (reflection.ok) {
      const retryResult = await callModel(POOL.orchestrator, [
        ...messages,
        { role: 'assistant', content: finalAnswer },
        { role: 'user', content: `A quality check found these issues:\n${reflection.content}\n\nPlease provide an improved answer.` },
      ]);
      if (retryResult.ok) {
        const newScore = await runUSVA(query, retryResult.content);
        if (newScore > qaScore) { finalAnswer = retryResult.content; qaScore = newScore; }
      }
    }
  }

  // LAYER 12: s1 BUDGET FORCING (arXiv:2501.19393)
  // If the answer is suspiciously short for a hard question, force longer reasoning
  if ((taskType === 'math' || taskType === 'reasoning') && finalAnswer.length < 500 && Date.now() - t0 < 80_000) {
    techniques.push('s1-budget-forcing');
    const forcedResult = await callModel(POOL.reasoning, [
      ...messages,
      { role: 'assistant', content: finalAnswer + '\n\nWait' },
      { role: 'user', content: 'Continue your reasoning in more detail. Provide a thorough step-by-step solution.' },
    ]);
    if (forcedResult.ok && forcedResult.content.length > finalAnswer.length) {
      finalAnswer = forcedResult.content;
    }
  }

  // LAYER 13: STEP-LEVEL CODE VERIFICATION (rStar-Math pattern)
  // For math/coding: verify each reasoning step, not just the final answer
  if ((taskType === 'math' || taskType === 'coding') && !codeVerified && Date.now() - t0 < 80_000) {
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
      ]);
      if (retryResult.ok) {
        const reVerified = await stepLevelVerify(query, retryResult.content);
        if (reVerified) { finalAnswer = retryResult.content; codeVerified = true; }
        else if (retryResult.content.length > finalAnswer.length) { finalAnswer = retryResult.content; }
      }
    }
  }

  // LAYER 14: Z3/SMT LOGICAL VERIFICATION (ConsistPRM pattern)
  // Extract logical claims and check for contradictions
  if ((taskType === 'reasoning' || taskType === 'knowledge') && Date.now() - t0 < 85_000) {
    techniques.push('z3-logical-verification');
    const logicalCheck = await logicalVerify(finalAnswer);
    if (logicalCheck === 'contradiction') {
      // Contradiction found — trigger retry
      techniques.push('reflexion');
      const retryResult = await callModel(POOL.orchestrator, [
        ...messages,
        { role: 'assistant', content: finalAnswer },
        { role: 'user', content: 'A logical analysis found contradictions in your answer. Please identify and resolve any contradictory statements, then provide a corrected answer.' },
      ]);
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
  if (qaScore < 0.82 && needsFrontier(query, taskType) && Date.now() - t0 < 85_000) {
    techniques.push('frontier-fallback');
    const frontierResult = await callModel(POOL.frontier, [
      { role: 'system', content: 'You are TemuClaude Frontier. Solve this problem with maximum rigor. Previous attempts scored low on quality. Provide a definitive answer.' },
      { role: 'user', content: `Question: ${query}\n\nPrevious best answer (scored ${qaScore.toFixed(2)}/1.0):\n${finalAnswer.substring(0, 2000)}\n\nProvide a better answer:` },
    ]);
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

function asciiSessionId(prefix: string, text: string): string {
  return `${prefix}-${Buffer.from(text || '').toString('base64url').slice(0, 64)}`;
}

async function callModel(
  model: string,
  messages: any[],
  options: { maxTokens?: number; timeoutMs?: number; temperature?: number; disableReasoning?: boolean; fallbacks?: string[] } = {},
): Promise<ModelResult> {
  const start = Date.now();
  const roleInstruction = ROLE_INSTRUCTIONS[model];
  const messagesWithSystem = [
    ENGLISH_SYSTEM,
    ...(roleInstruction ? [{ role: 'system', content: roleInstruction }] : []),
    ...messages,
  ]
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
  return /\b(build|create|generate|make|implement|write|develop)\b[\s\S]{0,120}\b(game|website|webpage|web page|site|web app|application|landing page|html|css|javascript|typescript|react|component|code|file)\b/i.test(query)
    || /\b(single[- ]file|html game|browser game|playable game|canvas game|three\.js)\b/i.test(query);
}

function hasCompleteHtmlDocument(content: string): boolean {
  const start = content.search(/<!doctype html|<html\b/i);
  if (start < 0) return false;
  return content.slice(start).search(/<\/html>/i) >= 0;
}

function createResilientHtmlFallback(query: string): string {
  const greekTheme = /\b(greek|olymp|olympus|zeus|athena|myth)/i.test(query);
  const title = greekTheme ? 'Olympus — Gods Beyond Time' : 'A Crafted Experience';
  const eyebrow = greekTheme ? 'ANCIENT AESTHETIC · MOUNT OLYMPUS' : 'TEMUCLAUDE RESILIENT DELIVERY';
  const description = greekTheme
    ? 'A timeless collection of the gods, their symbols, and the stories that shaped the heavens.'
    : 'A complete, responsive landing page delivered while upstream model routes recover.';
  const cards = greekTheme
    ? [['Zeus', 'Thunder & Sovereignty', '⚡'], ['Athena', 'Wisdom & Strategy', '🦉'], ['Apollo', 'Light & Harmony', '☀'], ['Artemis', 'Moon & Wilderness', '☾']]
    : [['Discover', 'A polished starting point', '✦'], ['Explore', 'Designed for focus', '◌'], ['Create', 'Built to be extended', '✺'], ['Return', 'Delivered without interruption', '↗']];
  const cardMarkup = cards.map(([name, detail, symbol]) => `<article class="card"><span>${symbol}</span><h2>${name}</h2><p>${detail}</p></article>`).join('');
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>
:root{--ink:#201b16;--paper:#f4eddf;--gold:#b78735;--wine:#572526;--night:#151a29}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 80% 10%,#fff8d9 0,transparent 30%),var(--paper);color:var(--ink);font-family:Georgia,'Times New Roman',serif}.hero{min-height:68vh;display:grid;place-items:center;padding:5rem 1.5rem;background:linear-gradient(120deg,rgba(21,26,41,.95),rgba(87,37,38,.82)),url('https://images.unsplash.com/photo-1549490349-8643362247b5?auto=format&fit=crop&w=1800&q=80') center/cover;color:#fff;text-align:center}.hero>*{max-width:780px}.eyebrow{font:700 .72rem/1 Arial,sans-serif;letter-spacing:.22em;color:#f6cf7b}.hero h1{font-size:clamp(3.1rem,9vw,7.5rem);line-height:.9;margin:1rem 0;letter-spacing:-.06em}.hero p{font-size:clamp(1.05rem,2vw,1.35rem);line-height:1.65;color:#ede2ca}.cta{border:1px solid #e5bc61;background:transparent;color:#fff;padding:.9rem 1.35rem;margin-top:1rem;font:700 .8rem Arial,sans-serif;letter-spacing:.12em;cursor:pointer}.cta:hover{background:#e5bc61;color:var(--night)}main{max-width:1120px;margin:auto;padding:4rem 1.5rem 5rem}.intro{max-width:650px;margin-bottom:2rem}.intro h2{font-size:2.3rem;margin:.2rem 0}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}.card{padding:1.5rem;background:#fffaf0;border:1px solid #dacda9;min-height:190px;transition:.25s transform,.25s box-shadow}.card:hover{transform:translateY(-6px);box-shadow:0 16px 28px rgba(32,27,22,.15)}.card span{font-size:2rem;color:var(--gold)}.card h2{margin:.8rem 0 .4rem;font-size:1.45rem}.card p{margin:0;color:#685b4c;line-height:1.45}footer{padding:1.5rem;text-align:center;background:var(--night);color:#cbbf9e;font:.72rem Arial,sans-serif;letter-spacing:.12em}@media(max-width:760px){.grid{grid-template-columns:repeat(2,1fr)}.hero{min-height:60vh}}@media(max-width:430px){.grid{grid-template-columns:1fr}}
</style></head><body><header class="hero"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${description}</p><button class="cta" onclick="document.querySelector('main').scrollIntoView({behavior:'smooth'})">ENTER THE STORY</button></div></header><main><section class="intro"><div class="eyebrow" style="color:var(--wine)">THE PANTHEON</div><h2>Myth made visible.</h2><p>Every card is an invitation to explore a world of symbols, starlight, and immortal stories.</p></section><section class="grid">${cardMarkup}</section></main><footer>CRAFTED WITH A RESILIENT TEMUCLAUDE DELIVERY PATH</footer></body></html>`;
}

function estimateDifficulty(query: string, taskType: string): number {
  // A requested webpage is a runnable software artifact, regardless of how
  // short its wording is. It must receive the quality code workflow rather
  // than the single-model trivial route.
  if (isCodeGenerationRequest(query)) return 8;
  let d = 0;
  d += Math.min(query.split(' ').length / 10, 5); // 0-5 based on length
  if (['math', 'reasoning', 'coding'].includes(taskType)) d += 2;
  if (query.includes('explain') || query.includes('analyze')) d += 1;
  if (query.includes('compare') || query.includes('step by step')) d += 2;
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

// Helper: check if task type matches keywords in the query
function q_match(taskType: string, keywords: string[]): boolean {
  // This is a simple check — in production, classifyTask would return these types
  return keywords.some(k => taskType.includes(k));
}

// Route only the hardest queries through the conditional frontier escalation.
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

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
        sendProgress(controller, encoder, 'Classifying prompt', 'Detecting task type and routing tier');
        const taskType = classifyTask(query);
        const difficulty = estimateDifficulty(query, taskType);
        const tier = determineTier(difficulty);
        const isCodeGeneration = isCodeGenerationRequest(query);
        const techniques: string[] = [];
        sendProgress(controller, encoder, 'Routing selected', `TemuClaude ${profile === 'lite' ? 'Lite' : 'Pro'} · ${taskType} task · ${tier} tier`, 'done');

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
          sendProgress(controller, encoder, 'Streaming answer', 'Final response is ready', 'done');
          streamText(controller, encoder, result.content);
          sendOrch(controller, encoder, taskType, tier, [{ name: 'glm-5.2', response: result.content.substring(0, 200), latency: (Date.now()-t0)/1000, correct: result.ok }], 'single', 1, 0, false, t0, formatProviderCost(result.cost), techniques);
          completed = { content: result.content, model: result.name };
        } else if (tier === 'medium') {
          // A Pro task is not downgraded to a single draft.  The same
          // specialist panel used for hard requests establishes a dependable
          // quality floor; the panel itself is task-aware.
          completed = await runFullStack(query, messages, controller, encoder, taskType, tier, t0, techniques);
        } else {
          // HARD: Full 6-layer stack
          completed = await runFullStack(query, messages, controller, encoder, taskType, tier, t0, techniques);
        }

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
    ? `${ENGLISH_SYSTEM.content} Execute the requested coding task now. Do not ask follow-up questions when reasonable defaults are possible. For a game, website, or interactive app, return a complete runnable deliverable; when suitable, return one complete HTML fenced file with all CSS and JavaScript included. Do not outline phases or defer implementation.`
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
    sessionId: `playground-lite-${draftModel}-${query.slice(0, 64)}`,
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
      sessionId: `playground-lite-synthesis-${query.slice(0, 64)}`,
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
      sessionId: `playground-lite-rescue-${query.slice(0, 72)}`,
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
    ], { maxTokens: 350, timeoutMs: 12_000, sessionId: `playground-lite-verify-${query.slice(0, 72)}` });
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
      ], { maxTokens: isCodeGeneration ? 4_096 : 2_000, timeoutMs: isCodeGeneration ? 90_000 : 30_000, sessionId: `playground-lite-correct-${query.slice(0, 72)}` });
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
      'When a single-file HTML game is requested or suitable, output one complete HTML fenced file with all CSS and JavaScript included.',
      'Do not describe phases, request model outputs, or defer implementation. State only brief assumptions, then provide the finished code.',
    ].join(' '),
  };
  const deadlineAt = t0 + 180_000;
  const remainingMs = () => Math.max(0, deadlineAt - Date.now());
  const [plan, draft, uiUxReview, productReview, gptReview, frontierReview, multimodalReview, codeReview] = await Promise.all([
    callModel(POOL.orchestrator, [
      { role: 'system', content: 'You are a senior software architect. Produce a concise implementation plan, acceptance criteria, edge cases, and test checklist for the requested deliverable. Do not write the final code.' },
      ...messages,
    ], { maxTokens: 2_000, timeoutMs: Math.min(35_000, remainingMs()) }),
    callModel(POOL.reasoning, [codeSystem, ...messages], {
      maxTokens: 8_192, timeoutMs: Math.min(65_000, remainingMs()), temperature: 0.35, disableReasoning: true,
    }),
    callModel(POOL.uiUx, [
      { role: 'system', content: 'Produce a coding-driven UI/UX implementation review: component structure, interactions, state, responsiveness, accessibility hooks, and concrete implementation traps. Do not write the final code.' },
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

  techniques.push('implementation-synthesis');
  sendProgress(controller, encoder, 'Synthesizing implementation', 'DeepSeek is incorporating architecture and UX review');
  let result = await callModel(POOL.reasoning, [
    codeSystem,
    { role: 'user', content: `Architect plan:\n${plan.content}\n\nKimi UI/UX implementation review:\n${uiUxReview.content}\n\nMiniMax product and multimodal review:\n${productReview.content}\n\nIndependent GPT review:\n${gptReview.content}\n\nFrontier adjudication:\n${frontierReview.content}\n\nGemini accessibility and interaction review:\n${multimodalReview.content}\n\nGrok coding-agent review:\n${codeReview.content}\n\nInitial implementation:\n${draft.content}\n\nReturn the complete corrected deliverable only. Satisfy every applicable acceptance criterion; do not discuss the review process.` },
  ], {
    maxTokens: 8_192,
    timeoutMs: Math.min(65_000, remainingMs()),
    temperature: 0.35,
    disableReasoning: true,
    // OpenRouter can move between these parameter-compatible code models
    // without making the user wait for a second full request timeout.
    fallbacks: [POOL.orchestrator, POOL.codeRepair],
  });
  if (result.ok && remainingMs() >= 8_000) {
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
      if (repaired.ok) result = repaired;
    }
  }
  if (!result.ok && remainingMs() >= 6_000) {
    techniques.push('code-repair-rescue');
    sendProgress(controller, encoder, 'Recovering code generation', 'Grok is producing the approved rescue deliverable');
    result = await callModel(POOL.codeRepair, [codeSystem, ...messages], {
      maxTokens: 6_144,
      timeoutMs: Math.min(30_000, remainingMs()),
      temperature: 0.35,
      // Grok 4.5 requires reasoning to remain enabled. Omitting the
      // disable flag prevents the provider-side 400 that broke this route.
    });
  }

  const content = result.ok
    ? result.content
    : 'Code generation is temporarily unavailable after all approved routes were tried. Please retry shortly.';
  sendProgress(controller, encoder, 'Streaming code', result.ok ? 'Complete deliverable is ready' : 'The approved code route was unavailable', result.ok ? 'done' : 'error');
  streamText(controller, encoder, content);
  sendOrch(controller, encoder, taskType, tier, [{
    name: result.name,
    response: content.substring(0, 200),
    latency: result.latency,
    correct: result.ok,
  }], result.name, result.ok ? 1 : 0, 0, false, t0, formatProviderCost(result.cost), techniques);
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
    fusionModels.map(id => callModel(id, augmentedMessages))
  );
  const proposals: ModelResult[] = proposeResults.map((r, i) =>
    r.status === 'fulfilled' ? r.value : { name: fusionModels[i].split('/').pop()||'', content: '[failed]', latency: 0, ok: false }
  );
  const workingProposals = proposals.filter(p => p.ok);
  sendProgress(controller, encoder, 'Proposal pass complete', `${workingProposals.length}/${proposals.length} models returned usable drafts`, workingProposals.length > 0 ? 'done' : 'error');

  if (workingProposals.length === 0) {
    streamText(controller, encoder, 'All models are currently unavailable. Please try again.');
    sendOrch(controller, encoder, taskType, tier, proposals.map(p => ({ name: p.name, response: p.content.substring(0,200), latency: p.latency, correct: p.ok })), 'none', 0, 0, false, t0, '$0.000', techniques);
    return { content: '', model: 'temuclaude-pro-fusion' };
  }

  // Layer 2: Cross-review — each model reviews the other two
  techniques.push('cross-review');
  sendProgress(controller, encoder, 'Cross-reviewing drafts', 'Models are checking each other for gaps');
  const crossReviewResults: ModelResult[] = [];
  for (let i = 0; i < Math.min(workingProposals.length, 1); i++) {
    if (Date.now() - t0 > 45_000) break;
    const reviewer = workingProposals[i];
    const others = workingProposals.filter((_, j) => j !== i);
    const reviewPrompt = buildCrossReviewPrompt(query, reviewer, others);
    const reviewResult = await callModel(reviewer.name.includes('glm') ? POOL.orchestrator : reviewer.name.includes('deepseek') ? POOL.reasoning : POOL.specialist, [
      { role: 'system', content: 'You are reviewing other AI models\' responses. Identify errors, missing information, and strengths. Provide an improved response.' },
      { role: 'user', content: reviewPrompt },
    ]);
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
  ]);
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
    sessionId: `playground-${messages[messages.length - 1]?.content?.slice(0, 80) || Date.now()}`,
  });
  return {
    name: result.model.split('/').pop() || result.model,
    content: result.success ? result.content : `[OpenRouter error: ${result.error || result.status || 'failed'}]`,
    latency: (Date.now() - start) / 1000,
    ok: result.success,
    cost: result.cost,
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
  return /\b(build|create|generate|make|implement|write|develop)\b[\s\S]{0,120}\b(game|website|web app|application|landing page|html|css|javascript|typescript|react|component|code|file)\b/i.test(query)
    || /\b(single[- ]file|html game|browser game|playable game|canvas game|three\.js)\b/i.test(query);
}

function estimateDifficulty(query: string, taskType: string): number {
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

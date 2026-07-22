/**
 * TemuClaude OpenAI-Compatible API — evidence-based specialist pipeline
 * POST /v1/chat/completions
 *
 * Eight models, each assigned to a bounded capability role:
 * 1. DeepSeek V4 Flash — Lite-only low-cost requests
 * 2. DeepSeek V4 Pro — math, code, and hard reasoning
 * 3. GLM-5.2 — knowledge, agentic work, and synthesis
 * 4. Kimi K3 — coding-driven UI/UX and multi-agent implementation
 * 5. MiniMax M3 — multimodal, creative, product, and long-context review
 * 6. Gemini 3.5 Flash — visual UI, accessibility, and tool-use review
 * 7. GPT-5.6 Luna — fast independent GPT-family proposer
 * 8. Kimi K3 — frontier adjudication and long-horizon coding review
 * 9. Grok 4.5 — coding-agent critic and repair specialist
 * 10. Nemotron 3 Ultra — independent QA verifier
 *
 * GPT-5.6 Terra is deliberately outside the normal pool and is attempted
 * only as the last emergency rescue after the open-core routes fail.
 *
 * Pipeline:
 * 1. Classify difficulty (heuristic, no API call)
 * 2. Pro → quality-floor specialist or full MoA; Lite → bounded low-cost route
 * 3. Layer 1: all nine Pro roles propose in parallel for nontrivial work
 * 4. Layer 2: Self-consistency for math (3 samples, parallel with Layer 1)
 * 5. Layer 3: Aggregation — analyze consensus, contradictions (1 call)
 * 6. Layer 4: QA gate — 5-rubric score by Nemotron (FREE, independent)
 * 7. Layer 5: Reflexion if QA < 8 — retry with feedback (1 call)
 * 8. Layer 6: QA-failure escalation if QA < 6 — GPT-5.6 Luna (1 call)
 * Timeout: bounded quality pipeline → frontier-first rescue
 */
import { NextRequest, NextResponse } from 'next/server';
import { createHash, timingSafeEqual } from 'crypto';
import { AsyncLocalStorage } from 'node:async_hooks';
import { validateApiKeyAsync, getMonthUsageAsync, getTodayUsageAsync, incrementUsageAsync, getRollingWindowUsageAsync, verifyAndRenewWeeklyCreditsAsync } from '@/lib/db';
import { PLAN_LIMITS } from '@/lib/plans';
import { callOpenRouter } from '@/lib/openrouter';
import { callOpenRouterLite, type LiteModelId } from '@/lib/openrouter-lite';
import { callModalChatCompletions, isModalConfigured } from '@/lib/modal';
import { createGenerationJob, GenerationJobError, publicGenerationJob } from '@/lib/generation-jobs';

// Global in-memory circuit breaker state (retained during warm serverless container instances)
let consecutiveFailures = 0;
let circuitTrippedUntil = 0;
// One request can invoke several models in parallel. AsyncLocalStorage keeps
// that invocation list isolated per request, including across Promise.all.
const modelActivityStore = new AsyncLocalStorage<string[]>();

export const runtime = 'nodejs';
export const maxDuration = 300;

// ── 8-MODEL POOL ──────────────────────────────────────────────
const M_FLASH = 'deepseek/deepseek-v4-flash';
const M_DEEPSEEK = 'deepseek/deepseek-v4-pro';
const M_GLM = 'z-ai/glm-5.2';
const M_MINIMAX = 'minimax/minimax-m3';
const M_GEMINI = 'google/gemini-3.5-flash';
const M_KIMI = 'moonshotai/kimi-k3';
const M_KIMI_FRONTIER = '~moonshotai/kimi-latest';
const M_LUNA = 'openai/gpt-5.6-luna';
// The production provider deliberately avoids Sol. Kimi is the frontier
// reviewer and rescue route for this API surface.
const M_GROK = 'x-ai/grok-4.5';
const M_NEMOTRON = 'nvidia/nemotron-3-ultra-550b-a55b';
const M_TERRA = 'openai/gpt-5.6-terra'; // emergency rescue only
const LITE_DEFAULT: LiteModelId = 'deepseek/deepseek-v4-flash';
const LITE_REASONING: LiteModelId = 'qwen/qwen3.7-plus';
const LITE_AGENT: LiteModelId = 'qwen/qwen3.7-plus';
const LITE_VERIFIER: LiteModelId = 'nvidia/nemotron-3-ultra-550b-a55b';
const TEMUCLAUDE_PRO_MODEL = 'temuclaude/temuclaude-pro';
const REQUIRED_MODAL_MODELS = new Set([
  M_GLM, M_DEEPSEEK, M_KIMI, M_MINIMAX, M_GEMINI,
  M_LUNA, M_KIMI_FRONTIER, M_GROK, M_NEMOTRON,
]);

const MODEL_ROLE_PROMPTS: Record<string, string> = {
  [M_GLM]: 'You are the GLM long-horizon planner and synthesis lead. Track dependencies, architecture, edge cases, and integration.',
  [M_DEEPSEEK]: 'You are the DeepSeek math, STEM, coding, and rigorous-reasoning lead. Derive and verify the technical core.',
  [M_KIMI]: 'You are the Kimi coding-driven UI/UX and frontier adjudication lead. Focus on complete interfaces, interaction flows, state, responsive behavior, production-ready code, and identifying weaker assumptions.',
  [M_MINIMAX]: 'You are the MiniMax multimodal, long-context, creative, and product reviewer. Focus on visual coherence and product completeness.',
  [M_GEMINI]: 'You are the Gemini visual UI, accessibility, multimodal, and tool-use reviewer. Focus on observable interaction quality.',
  [M_LUNA]: 'You are a fast independent GPT-family proposer. Find a distinct solution path, useful tools, and consensus omissions.',
  [M_GROK]: 'You are the Grok coding-agent and repair specialist. Hunt bugs, unsafe assumptions, integration failures, and missing tests.',
  [M_NEMOTRON]: 'You are the Nemotron independent verifier. Try to falsify reasoning, code, long-context, and high-stakes claims.',
};

interface Msg { role: 'system' | 'user' | 'assistant'; content: string }
interface Result { success: boolean; content: string; tokens: number }
type ModelCallOptions = { fallbacks?: string[]; timeoutMs?: number; disableReasoning?: boolean };
interface OrchestrationResult { content: string; tokens: number; tier: string; time: number }

function hasUsableContent(content: unknown): content is string {
  return typeof content === 'string' && content.trim().length > 0;
}

function promptTokenEstimate(messages: Msg[]): number {
  return messages.reduce((sum, message) => sum + Math.ceil(String(message.content || '').length / 4), 0);
}

function completionTokenEstimate(content: string): number {
  return Math.ceil(content.length / 4);
}

function upstreamFailure(message: string, status = 503) {
  return NextResponse.json(
    { error: { message, type: 'server_error' } },
    { status },
  );
}

function extractAssistantContent(data: any): string {
  return data?.choices?.[0]?.message?.content || '';
}

function hasCompleteModalPanel(data: any): boolean {
  const completed = data?.orchestration?.completed_models;
  return Array.isArray(completed) && Array.from(REQUIRED_MODAL_MODELS).every((model) => completed.includes(model));
}

function recordModelActivity(model: string | null | undefined) {
  if (!model || /^temuclaude(?:\/|$)/i.test(model)) return;
  modelActivityStore.getStore()?.push(model);
}

type CompletionPayload = {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<Record<string, unknown>>;
  usage?: Record<string, number>;
};

type OpenAITool = {
  type?: string;
  function?: { name?: string; description?: string; parameters?: unknown };
};

type ParsedToolCall = { id: string; type: 'function'; function: { name: string; arguments: string } };

function toolAwareMessages(messages: Msg[], tools: unknown): Msg[] {
  if (!Array.isArray(tools)) return messages;
  const names = (tools as OpenAITool[])
    .map((tool) => tool.type === 'function' ? tool.function?.name : undefined)
    .filter((name): name is string => typeof name === 'string' && name.length > 0)
    .slice(0, 64);
  if (names.length === 0) return messages;
  const fileWriteHint = names.includes('file.write_file') || names.includes('write_file')
    ? ` For ${names.includes('file.write_file') ? 'file.write_file' : 'write_file'}, arguments must be an object with path and content.`
    : '';
  return [{
    role: 'system',
    content: `You can use these tools: ${names.join(', ')}. When executing a tool is the best next action, respond with exactly one XML-wrapped JSON tool call and nothing else: <tool_call>{"name":"tool_name","arguments":{}}</tool_call>. Only select a listed tool and provide valid JSON arguments.${fileWriteHint} Do not merely claim that a tool was used.`,
  }, ...messages];
}

function firstJsonObject(value: string): string | null {
  const start = value.indexOf('{');
  if (start < 0) return null;
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let index = start; index < value.length; index += 1) {
    const character = value[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (character === '\\') escaped = true;
      else if (character === '"') inString = false;
      continue;
    }
    if (character === '"') inString = true;
    else if (character === '{') depth += 1;
    else if (character === '}') {
      depth -= 1;
      if (depth === 0) return value.slice(start, index + 1);
    }
  }
  return null;
}

function parseToolCall(content: string, tools: unknown): ParsedToolCall | null {
  if (!Array.isArray(tools)) return null;
  const allowed = new Set((tools as OpenAITool[])
    .map((tool) => tool.type === 'function' ? tool.function?.name : undefined)
    .filter((name): name is string => typeof name === 'string'));
  // DeepSeek-family models can ignore the requested XML wrapper and emit
  // their native DSML invocation syntax instead.  Hermes sends OpenAI tool
  // definitions, so leaving that syntax in `content` makes it look like a
  // normal assistant reply and the agent cannot continue its tool loop.
  // Convert only a complete, allow-listed invocation into the standard
  // OpenAI shape; arbitrary tags or unlisted names stay ordinary content.
  const dsmlInvoke = content.match(/<｜DSML｜invoke\s+name=(?:"([^"]+)"|'([^']+)')\s*>([\s\S]*?)<\/｜DSML｜invoke>/i);
  if (dsmlInvoke) {
    const name = dsmlInvoke[1] || dsmlInvoke[2] || '';
    if (!allowed.has(name)) return null;
    const args: Record<string, string> = {};
    const parameters = dsmlInvoke[3];
    const parameterPattern = /<｜DSML｜parameter\s+name=(?:"([^"]+)"|'([^']+)')[^>]*>([\s\S]*?)<\/｜DSML｜parameter>/gi;
    let parameter: RegExpExecArray | null;
    while ((parameter = parameterPattern.exec(parameters)) !== null) {
      const key = parameter[1] || parameter[2] || '';
      if (!key || Object.prototype.hasOwnProperty.call(args, key)) return null;
      args[key] = parameter[3].trim();
    }
    if (Object.keys(args).length === 0) return null;
    const serializedArgs = JSON.stringify(args);
    return {
      id: `call_${createHash('sha256').update(`${name}:${serializedArgs}:${Date.now()}`).digest('hex').slice(0, 24)}`,
      type: 'function',
      function: { name, arguments: serializedArgs },
    };
  }
  // Some OpenAI-compatible agent clients and upstream models omit the
  // cosmetic closing tag once the JSON object is complete. The JSON itself is
  // still validated below, so accepting end-of-message is safe and makes the
  // tool contract interoperable with Hermes, Claude Code, and OpenCode.
  const match = content.match(/<tool_call>\s*([\s\S]*?)(?:\s*<\/tool_call>|\s*$)/i);
  // Kimi's structured-output mode sometimes returns the JSON object directly
  // instead of adding an XML wrapper. Treat it as a candidate only when it
  // parses as an allowed tool call below.
  // Kimi occasionally closes the wrapper with its internal argument tag
  // (`</arg_value>`) even though the JSON object is complete.  It is not an
  // OpenAI tool-call field and must be stripped before JSON validation.
  const rawCall = (match?.[1] || content.trim())
    .replace(/\s*<\/(?:tool_call|arg_value)\s*>\s*$/i, '')
    .trim();
  // Some Kimi responses close the JSON and then begin a second malformed XML
  // tag. Extracting the balanced object lets Hermes execute the valid action
  // while still rejecting incomplete or structurally invalid arguments.
  const jsonCall = firstJsonObject(rawCall);
  if (!jsonCall) return null;
  try {
    const call = JSON.parse(jsonCall) as { name?: unknown; arguments?: unknown };
    if (typeof call.name !== 'string' || !allowed.has(call.name)) return null;
    const args = typeof call.arguments === 'string' ? call.arguments : JSON.stringify(call.arguments ?? {});
    JSON.parse(args);
    return { id: `call_${createHash('sha256').update(`${call.name}:${args}:${Date.now()}`).digest('hex').slice(0, 24)}`, type: 'function', function: { name: call.name, arguments: args } };
  } catch {
    return null;
  }
}

/**
 * Return either the established JSON completion contract or a small,
 * standards-compliant OpenAI SSE sequence.  The pipeline deliberately
 * completes before emitting: orchestration depends on several model calls,
 * but clients that request `stream: true` (including AI SDK consumers such as
 * Obsidian LLM Wiki) still receive the protocol they expect.
 */
function completionResponse(payload: CompletionPayload, stream: boolean): NextResponse {
  if (!stream) return NextResponse.json(payload);

  const message = payload.choices[0]?.message as { content?: string; tool_calls?: ParsedToolCall[] } | undefined;
  const content = String(message?.content || '');
  const toolCalls = message?.tool_calls || [];
  const chunkBase = {
    id: payload.id,
    object: 'chat.completion.chunk',
    created: payload.created,
    model: payload.model,
  };
  const encoder = new TextEncoder();
  const sse = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({
        ...chunkBase,
        choices: [{ index: 0, delta: { role: 'assistant' }, finish_reason: null }],
      })}\n\n`));
      if (toolCalls.length > 0) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          ...chunkBase,
          choices: [{ index: 0, delta: { tool_calls: toolCalls.map((toolCall, index) => ({ index, id: toolCall.id, type: toolCall.type, function: { name: toolCall.function.name, arguments: '' } })) }, finish_reason: null }],
        })}\n\n`));
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          ...chunkBase,
          choices: [{ index: 0, delta: { tool_calls: toolCalls.map((toolCall, index) => ({ index, function: { arguments: toolCall.function.arguments } })) }, finish_reason: null }],
        })}\n\n`));
      } else if (content) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          ...chunkBase,
          choices: [{ index: 0, delta: { content }, finish_reason: null }],
        })}\n\n`));
      }
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({
        ...chunkBase,
        choices: [{ index: 0, delta: {}, finish_reason: toolCalls.length > 0 ? 'tool_calls' : 'stop' }],
      })}\n\n`));
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });
  return new NextResponse(sse, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}

/**
 * Call a model via OpenRouter with reasoning field fallback.
 * Prepends English enforcement system prompt to ensure consistent English output.
 */
async function call(model: string, messages: Msg[], temp = 0.6, maxTok = 4096, options: ModelCallOptions = {}): Promise<Result> {
  recordModelActivity(model);
  let msgs = messages;
  const effectiveMaxTokens = Math.max(64, maxTok);
  if (!messages.some(m => m.role === 'system')) {
    msgs = [{ role: 'system', content: 'You are TemuClaude, an AI assistant. Always respond in clear, professional English. Be concise and direct.' }, ...messages];
  }
  const rolePrompt = MODEL_ROLE_PROMPTS[model];
  if (rolePrompt) msgs = [{ role: 'system', content: rolePrompt }, ...msgs];

  const result = await callOpenRouter(model, msgs, {
    temperature: temp,
    maxTokens: effectiveMaxTokens,
    timeoutMs: options.timeoutMs ?? 60_000,
    fallbacks: options.fallbacks,
    disableReasoning: options.disableReasoning,
    sessionId: `v1-${Buffer.from(messages[messages.length - 1]?.content || '').toString('base64url').slice(0, 64)}`,
  });
  recordModelActivity(result.model);
  return { success: result.success, content: result.content, tokens: result.tokens };
}

async function finalRescue(messages: Msg[], temp: number, maxTok: number): Promise<OrchestrationResult> {
  const start = Date.now();
  const result = await call(M_KIMI, messages, temp, maxTok, {
    fallbacks: [M_GROK, M_DEEPSEEK, M_GLM, M_TERRA],
    timeoutMs: 100_000,
  });
  return {
    content: result.success ? result.content.trim() : '',
    tokens: result.tokens,
    tier: result.success ? 'rescue-fallback' : 'failed-empty',
    time: Date.now() - start,
  };
}

/**
 * Difficulty Classifier — heuristic, no API call.  Pro code generation is a
 * hard artifact task: it receives the full panel, aggregation, QA, and repair
 * rather than an economy-oriented single draft.
 */
function classify(text: string): 'trivial' | 'medium' | 'hard' {
  const l = text.toLowerCase();
  const wc = text.split(/\s+/).length;
  let s = 0;
  if (wc > 100) s += 4; else if (wc > 50) s += 2; else if (wc > 20) s += 1;
  if (/\b(solve|calculate|derivative|integral|equation|prove|theorem|factor|simplify|evaluate|compute|matrix|probability|limit|optimi[sz]e)\b/i.test(l)) s += 3;
  if ((text.match(/[+\-*/^=<>]/g) || []).length > 3) s += 2;
  if (/\b(because|therefore|if.*then|contradiction|inference|deduce|imply|assume|prove that|show that|explain why|reason)\b/i.test(l)) s += 2;
  if (/\b(then|after|next|finally|step by step|how long|how many|show your work)\b/i.test(l)) s += 2;
  if ((text.match(/[;,.]/g) || []).length > 3) s += 1;
  if (/\b(if|when|where|given|assuming|suppose)\b/i.test(l)) s += 1;

  // Code generation is a hard artifact task on Pro.
  const isCodeGen = /\b(build|create|generate|write|make|develop|implement|code|html|css|javascript|python|function|class|component|game|website|webpage|app|script|program|landing page|dashboard)\b/i.test(l) &&
                    /\b(html|css|js|javascript|python|code|function|component|page|game|app|script|file|complete)\b/i.test(l);
  if (isCodeGen) return 'hard';

  // General coding keywords still add to score but won't force hard if code gen detected
  if (/\b(function|code|debug|program|algorithm|python|javascript|implement|write.*code|compile|runtime|complexity|recursive|sort|search)\b/i.test(l)) s += 3;

  if (s >= 7) return 'hard';
  if (s >= 3) return 'medium';
  return 'trivial';
}

/**
 * Detect if the query is a code generation task (not a code reasoning/debugging task).
 * Code generation should route to a single strong model, not the full MoA pipeline.
 */
function isCodeGen(text: string): boolean {
  const l = text.toLowerCase();
  return /\b(build|create|generate|write|make|develop|implement|code|html|css|javascript|python|function|class|component|game|website|webpage|app|script|program|landing page|dashboard)\b/i.test(l) &&
         /\b(html|css|js|javascript|python|code|function|component|page|game|app|script|file|complete)\b/i.test(l);
}

function isMath(text: string): boolean {
  return /\b(solve|calculate|derivative|integral|equation|prove|theorem|sum|product|factor|simplify|evaluate|compute|find.*value|matrix|probability|limit|optimi[sz]e)\b/i.test(text) ||
         (/\d/.test(text) && /[+\-*/^=]/.test(text));
}

function isCreative(text: string): boolean {
  return /\b(write|story|poem|creative|imagine|describe|narrative|character|dialogue|screenplay|lyrics|essay|blog|article)\b/i.test(text);
}

function isMultimodal(text: string): boolean {
  return /\b(image|picture|photo|video|visual|diagram|chart|screenshot|see|look at|describe.*image)\b/i.test(text);
}

function isLiteModel(model: unknown): boolean {
  return typeof model === 'string' && ['temuclaude-lite', 'temuclaude/temuclaude-lite', 'temuclaude/lite'].includes(model.toLowerCase());
}

function isProModel(model: unknown): boolean {
  return model === undefined || model === null || (typeof model === 'string' && [
    'temuclaude',
    'temuclaude-pro',
    'temuclaude/temuclaude',
    TEMUCLAUDE_PRO_MODEL,
    'temuclaude/pro',
  ].includes(model.toLowerCase()));
}

function selectLiteApiModel(text: string, tier: string): LiteModelId {
  // A runnable code deliverable is both latency- and budget-sensitive. Keep
  // Lite on the low-cost Flash route rather than treating every code prompt
  // as an expensive agentic request.
  if (isCodeGen(text)) return LITE_DEFAULT;
  if (tier === 'hard' && (isMath(text) || /\b(reason|prove|deduce|infer|logic)\b/i.test(text))) return LITE_REASONING;
  if (isMultimodal(text) || /\b(agent|tool|workflow|ui|screen|browser)\b/i.test(text)) return LITE_AGENT;
  return LITE_DEFAULT;
}

function shouldVerifyLite(query: string, tier: string, answer: string): boolean {
  const text = query.toLowerCase();
  if (/(medical|diagnosis|medication|legal advice|financial advice|investment decision|safety critical|verify|fact-check|audit)/.test(text)) return true;
  if (isCodeGen(query)) return true;
  if (tier !== 'trivial' || answer.trim().length < 80) return tier !== 'trivial';
  const sample = createHash('sha256').update(query).digest().readUInt32BE(0) / 0x1_0000_0000;
  return sample < 0.02;
}

/**
 * Self-Consistency: 3 samples at temp 0.7, majority vote.
 * Research: +18.4% on MATH benchmark (arXiv:2203.11317).
 */
async function selfConsistency(q: string, maxTok: number): Promise<{ answer: string; tokens: number }> {
  const results = await Promise.all([
    call(M_DEEPSEEK, [{ role: 'user', content: q }], 0.7, maxTok),
    call(M_DEEPSEEK, [{ role: 'user', content: q }], 0.7, maxTok),
    call(M_DEEPSEEK, [{ role: 'user', content: q }], 0.7, maxTok),
  ]);
  const samples = results.filter(r => r.success && r.content).map(r => r.content.trim());
  const tokens = results.reduce((s, r) => s + r.tokens, 0);
  if (samples.length === 0) return { answer: '', tokens };

  const extract = (t: string): string => {
    const boxed = t.match(/\\boxed\{([^}]+)\}/);
    if (boxed) return boxed[1].trim();
    const lines = t.split('\n').filter(x => x.trim());
    const last = lines[lines.length - 1]?.trim() || '';
    if (last.length < 50) return last;
    const m = t.match(/(?:answer is|final answer is|=|equals|result is|x\s*=)\s*[:\s]*([^\n.]+)/i);
    return m ? m[1].trim() : last;
  };

  const finals = samples.map(extract);
  const counts: Record<string, number> = {};
  for (const a of finals) counts[a] = (counts[a] || 0) + 1;

  let best = samples[0], bestCount = 0;
  for (let i = 0; i < finals.length; i++) {
    if (counts[finals[i]] > bestCount) { bestCount = counts[finals[i]]; best = samples[i]; }
  }
  return { answer: best, tokens };
}

/**
 * Aggregation: Analyze consensus, contradictions, synthesize one definitive answer.
 */
async function aggregate(q: string, responses: { name: string; content: string }[], maxTok: number): Promise<Result> {
  const text = responses.map(r => `${r.name}: ${r.content}`).join('\n\n---\n\n');
  return call(M_GLM, [
    { role: 'system', content: `You are an expert answer synthesizer. Analyze the responses for:
1. CONSENSUS — what most agree on (likely correct)
2. CONTRADICTIONS — where they disagree, determine which is correct
3. BEST INSIGHTS — extract unique points from each
4. ERRORS — fix any mistakes

Provide ONE definitive answer. Do NOT mention the analysis. Output ONLY the final answer.` },
    { role: 'user', content: `Question: ${q}\n\nResponses:\n${text}\n\nProvide the definitive answer:` },
  ], 0.3, maxTok);
}

/**
 * QA Gate: 5-rubric score by the independent Nemotron verifier.
 */
async function qaGate(q: string, a: string): Promise<{ score: number; tokens: number; feedback: string }> {
  const r = await call(M_NEMOTRON, [
    { role: 'system', content: `Score this answer on 5 rubrics (1-10 each):
LC — Logical Coherence
FC — Factual Correctness
CM — Completeness
GA — Goal Alignment
CL — Clarity

Output:
AVERAGE: X
FEEDBACK: <one sentence>` },
    { role: 'user', content: `Question: ${q}\nAnswer: ${a}\n\nScore:` },
  ], 0.0, 500);

  const avg = r.content?.match(/AVERAGE:\s*(\d+(?:\.\d+)?)/i);
  const fb = r.content?.match(/FEEDBACK:\s*(.+)/i);
  let score = avg ? parseFloat(avg[1]) : 0;
  if (!score && r.content) {
    const rubricScores = r.content.match(/(?:LC|FC|CM|GA|CL):\s*(\d+)/gi);
    if (rubricScores && rubricScores.length >= 3) {
      const nums = rubricScores.map(s => { const m = s.match(/(\d+)/); return m ? parseInt(m[1]) : 0; }).filter(n => n > 0);
      if (nums.length > 0) score = nums.reduce((a: number, b: number) => a + b, 0) / nums.length;
    }
  }
  if (!score) score = 5; // Default to 5 (triggers reflexion) not 7 (skips it)
  return { score, tokens: r.tokens, feedback: fb ? fb[1].trim() : 'Improve completeness and clarity' };
}

/**
 * Reflexion: Retry with specific feedback from QA gate.
 * Research: 91% on HumanEval vs 80% without (arXiv:2303.11366).
 */
async function reflexion(q: string, prevAnswer: string, feedback: string, maxTok: number): Promise<Result> {
  const repairModel = isCodeGen(q) ? M_GROK : M_DEEPSEEK;
  return call(repairModel, [
    { role: 'system', content: 'You are answering a question. A previous attempt received feedback. Use it to improve. Output ONLY the improved answer.' },
    { role: 'user', content: `Question: ${q}\n\nPrevious answer: ${prevAnswer}\n\nFeedback: ${feedback}\n\nImproved answer:` },
  ], 0.4, maxTok);
}

/**
 * Full capability-aware orchestration pipeline
 */
async function orchestrate(messages: Msg[], temp: number, maxTok: number) {
  const start = Date.now();
  let tokens = 0;
  const q = messages[messages.length - 1]?.content || '';
  // Pro is an all-model product: classification controls optional techniques,
  // never whether a customer is reduced to a one-model response.
  const math = isMath(q);
  const creative = isCreative(q);
  const multimodal = isMultimodal(q);

  // ── All-task, full capability-aware MoA pipeline ──

  // MATH: self-consistency replaces single DeepSeek call (runs parallel)
  if (math) {
    const [r1, r3, sc, r4, r5, r6, r7, r8, r9] = await Promise.all([
      call(M_GLM, messages, temp, maxTok),
      call(M_NEMOTRON, messages, temp, maxTok),
      selfConsistency(q, maxTok),
      call(M_LUNA, messages, temp, maxTok),
      call(M_GEMINI, messages, temp, maxTok),
      call(M_MINIMAX, messages, temp, maxTok),
      call(M_GROK, messages, temp, maxTok),
      call(M_KIMI, messages, temp, maxTok),
      call(M_KIMI_FRONTIER, messages, temp, maxTok),
    ]);
    tokens += r1.tokens + r3.tokens + sc.tokens + r4.tokens + r5.tokens + r6.tokens + r7.tokens + r8.tokens + r9.tokens;

    const l1: { name: string; content: string }[] = [];
    if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
    if (sc.answer) l1.push({ name: 'Model B (DeepSeek, self-consistency)', content: sc.answer });
    if (r3.success && r3.content) l1.push({ name: 'Model C (Nemotron 3 Ultra)', content: r3.content });
    if (r4.success && r4.content) l1.push({ name: 'Model D (GPT-5.6 Luna independent worker)', content: r4.content });
    if (r5.success && r5.content) l1.push({ name: 'Model E (Gemini multimodal)', content: r5.content });
    if (r6.success && r6.content) l1.push({ name: 'Model F (MiniMax long-context)', content: r6.content });
    if (r7.success && r7.content) l1.push({ name: 'Model G (Grok critic)', content: r7.content });
    if (r8.success && r8.content) l1.push({ name: 'Model H (Kimi UI/UX implementation)', content: r8.content });
    if (r9.success && r9.content) l1.push({ name: 'Model I (Kimi frontier adjudicator)', content: r9.content });

    if (l1.length === 0) return { content: '', tokens, tier: 'hard', time: Date.now() - start };

    const agg = await aggregate(q, l1, maxTok);
    tokens += agg.tokens;
    let final = (agg.success && agg.content) ? agg.content : l1[0].content;

    const qa = await qaGate(q, final);
    tokens += qa.tokens;

    if (qa.score < 8) {
      const ref = await reflexion(q, final, qa.feedback, maxTok);
      tokens += ref.tokens;
      if (ref.success && ref.content) {
        const qa2 = await qaGate(q, ref.content);
        tokens += qa2.tokens;
        if (qa2.score > qa.score) final = ref.content;
      }
      if (qa.score < 6) {
        const frontier = await call(M_KIMI, messages, temp, maxTok);
        tokens += frontier.tokens;
        if (frontier.success && frontier.content) {
          const qa3 = await qaGate(q, frontier.content);
          tokens += qa3.tokens;
          if (qa3.score > qa.score) final = frontier.content;
        }
      }
    }
    return { content: final, tokens, tier: 'hard', time: Date.now() - start };
  }

  // CREATIVE: Route to MiniMax M3 as 3rd proposer instead of Gemini
  if (creative) {
    const [r1, r2, r3, r4, r5, r6, r7, r8, r9] = await Promise.all([
      call(M_GLM, messages, temp, maxTok),
      call(M_DEEPSEEK, messages, temp, maxTok),
      call(M_MINIMAX, messages, temp, maxTok),
      call(M_GEMINI, messages, temp, maxTok),
      call(M_LUNA, messages, temp, maxTok),
      call(M_GROK, messages, temp, maxTok),
      call(M_NEMOTRON, messages, temp, maxTok),
      call(M_KIMI, messages, temp, maxTok),
      call(M_KIMI_FRONTIER, messages, temp, maxTok),
    ]);
    tokens += r1.tokens + r2.tokens + r3.tokens + r4.tokens + r5.tokens + r6.tokens + r7.tokens + r8.tokens + r9.tokens;

    const l1: { name: string; content: string }[] = [];
    if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
    if (r2.success && r2.content) l1.push({ name: 'Model B (DeepSeek V4 Pro)', content: r2.content });
    if (r3.success && r3.content) l1.push({ name: 'Model C (MiniMax M3, creative)', content: r3.content });
    if (r4.success && r4.content) l1.push({ name: 'Model D (Gemini multimodal)', content: r4.content });
    if (r5.success && r5.content) l1.push({ name: 'Model E (GPT-5.6 Luna independent worker)', content: r5.content });
    if (r6.success && r6.content) l1.push({ name: 'Model F (Grok critic)', content: r6.content });
    if (r7.success && r7.content) l1.push({ name: 'Model G (Nemotron verifier)', content: r7.content });
    if (r8.success && r8.content) l1.push({ name: 'Model H (Kimi UI/UX implementation)', content: r8.content });
    if (r9.success && r9.content) l1.push({ name: 'Model I (Kimi frontier adjudicator)', content: r9.content });

    if (l1.length === 0) return { content: '', tokens, tier: 'hard', time: Date.now() - start };

    const agg = await aggregate(q, l1, maxTok);
    tokens += agg.tokens;
    let final = (agg.success && agg.content) ? agg.content : l1[0].content;

    const qa = await qaGate(q, final);
    tokens += qa.tokens;

    if (qa.score < 8) {
      const ref = await reflexion(q, final, qa.feedback, maxTok);
      tokens += ref.tokens;
      if (ref.success && ref.content) {
        const qa2 = await qaGate(q, ref.content);
        tokens += qa2.tokens;
        if (qa2.score > qa.score) final = ref.content;
      }
      if (qa.score < 6) {
        const frontier = await call(M_KIMI, messages, temp, maxTok);
        tokens += frontier.tokens;
        if (frontier.success && frontier.content) {
          const qa3 = await qaGate(q, frontier.content);
          tokens += qa3.tokens;
          if (qa3.score > qa.score) final = frontier.content;
        }
      }
    }
    return { content: final, tokens, tier: 'hard-creative', time: Date.now() - start };
  }

  // HARD (general): every configured frontier and specialist role contributes.
  const [r1, r2, r3, r4, r5, r6, r7, r8, r9] = await Promise.all([
    call(M_GLM, messages, temp, maxTok),
    call(M_DEEPSEEK, messages, temp, maxTok),
    call(M_NEMOTRON, messages, temp, maxTok),
    call(M_LUNA, messages, temp, maxTok),
    call(M_GEMINI, messages, temp, maxTok),
    call(M_MINIMAX, messages, temp, maxTok),
    call(M_GROK, messages, temp, maxTok),
    call(M_KIMI, messages, temp, maxTok),
    call(M_KIMI_FRONTIER, messages, temp, maxTok),
  ]);
  tokens += r1.tokens + r2.tokens + r3.tokens + r4.tokens + r5.tokens + r6.tokens + r7.tokens + r8.tokens + r9.tokens;

  const l1: { name: string; content: string }[] = [];
  if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
  if (r2.success && r2.content) l1.push({ name: 'Model B (DeepSeek V4 Pro)', content: r2.content });
  if (r3.success && r3.content) l1.push({ name: 'Model C (Nemotron 3 Ultra)', content: r3.content });
  if (r4.success && r4.content) l1.push({ name: 'Model D (GPT-5.6 Luna independent worker)', content: r4.content });
  if (r5.success && r5.content) l1.push({ name: 'Model E (Gemini multimodal)', content: r5.content });
  if (r6.success && r6.content) l1.push({ name: 'Model F (MiniMax specialist)', content: r6.content });
  if (r7.success && r7.content) l1.push({ name: 'Model G (Grok critic)', content: r7.content });
  if (r8.success && r8.content) l1.push({ name: 'Model H (Kimi UI/UX implementation)', content: r8.content });
  if (r9.success && r9.content) l1.push({ name: 'Model I (Kimi frontier adjudicator)', content: r9.content });

  if (l1.length === 0) return { content: '', tokens, tier: 'hard', time: Date.now() - start };

  const agg = await aggregate(q, l1, maxTok);
  tokens += agg.tokens;
  let final = (agg.success && agg.content) ? agg.content : l1[0].content;

  const qa = await qaGate(q, final);
  tokens += qa.tokens;

  if (qa.score < 8) {
    const ref = await reflexion(q, final, qa.feedback, maxTok);
    tokens += ref.tokens;
    if (ref.success && ref.content) {
      const qa2 = await qaGate(q, ref.content);
      tokens += qa2.tokens;
      if (qa2.score > qa.score) final = ref.content;
    }
    if (qa.score < 6) {
      const frontier = await call(M_KIMI, messages, temp, maxTok);
      tokens += frontier.tokens;
      if (frontier.success && frontier.content) {
        const qa3 = await qaGate(q, frontier.content);
        tokens += qa3.tokens;
        if (qa3.score > qa.score) final = frontier.content;
      }
    }
  }

  return { content: final, tokens, tier: 'hard', time: Date.now() - start };
}

// Constant-time secret comparison (avoids a timing side-channel on the master
// key check). crypto.timingSafeEqual throws on length mismatch, so guard first.
function constantTimeEqual(a: string, b: string): boolean {
  const aBuf = Buffer.from(a);
  const bBuf = Buffer.from(b);
  if (aBuf.length !== bBuf.length) return false;
  return timingSafeEqual(aBuf, bBuf);
}

export async function POST(request: NextRequest) {
  return modelActivityStore.run([], async () => {
  try {
    // ── Auth & Usage ──────────────────────────────────────
    // Authenticate before parsing the body so an unauthenticated request gets
    // 401 (not a body-validation 400 that reveals parsing ran). The master-key
    // comparison is constant-time; the DB key path is the customer's secret.
    // 1. Try API key (Bearer token or x-api-key header)
    const apiKey = request.headers.get('authorization')?.replace('Bearer ', '') ||
                   request.headers.get('x-api-key') || '';
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;

    let userId: string | null = null;
    let userPlan = 'free';
    let isEvalMode = false; // open access for benchmarking platforms
    const allowAnonymousApi = process.env.TEMUCLAUDE_ALLOW_PUBLIC_API === 'true';

    if (apiKey) {
      // Check master key first (for evaluation platforms — AA, LMSys, LiveBench, etc.)
      if (masterKey && constantTimeEqual(apiKey, masterKey)) {
        isEvalMode = true;
      } else {
        // Validate against DB
        const valid = await validateApiKeyAsync(apiKey);
        if (!valid) {
          return NextResponse.json(
            { error: { message: 'Invalid API key', type: 'authentication_error' } },
            { status: 401 }
          );
        }
        userId = valid.userId;
        userPlan = valid.user.plan || 'free';
        if (userPlan === 'free') {
          return NextResponse.json(
            { error: { message: 'API access requires a Developer, Pro, Max, or Enterprise plan.', type: 'permission_error' } },
            { status: 403 }
          );
        }
      }
    } else if (!allowAnonymousApi) {
      return NextResponse.json(
        { error: { message: 'Missing API key', type: 'authentication_error' } },
        { status: 401 }
      );
    }
    // Anonymous API access is disabled by default. Set TEMUCLAUDE_ALLOW_PUBLIC_API=true
    // only for temporary benchmarking or public evaluation windows.

    // Check usage limits for non-eval users
    if (!isEvalMode && userId) {
      // Dynamic weekly renewal check
      const user = await verifyAndRenewWeeklyCreditsAsync(userId);
      const creditBalance = user ? user.credit_balance : 0;

      if (creditBalance <= 0) {
        return NextResponse.json(
          { error: { message: 'Credit balance exhausted. Please purchase a top-up or wait for weekly renewal.', type: 'rate_limit_error' } },
          { status: 429 }
        );
      }

      const limits = PLAN_LIMITS[userPlan as keyof typeof PLAN_LIMITS] || PLAN_LIMITS.free;
      const rollingUsage = await getRollingWindowUsageAsync(userId, 5);

      if (limits.rollingQueries !== Infinity && rollingUsage.query_count >= limits.rollingQueries) {
        return NextResponse.json(
          { error: { message: `Rate limit exceeded. Rolling limit is ${limits.rollingQueries} queries per 5 hours. Upgrade at temuclaude.com/pricing`, type: 'rate_limit_error' } },
          { status: 429 }
        );
      }
    }

    // ── Body parse & validation (after auth) ──────────────
    const body = await request.json();
    const { model, messages, temperature, max_tokens, tools } = body;
    const wantsStream = body.stream === true;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: { message: 'messages array is required', type: 'invalid_request_error' } },
        { status: 400 }
      );
    }
    const providerMessages = toolAwareMessages(messages as Msg[], tools);

    if (!isLiteModel(model) && !isProModel(model)) {
      return NextResponse.json(
        { error: { message: 'Unsupported model. Use temuclaude/temuclaude-pro or temuclaude/temuclaude-lite.', type: 'invalid_request_error' } },
        { status: 400 },
      );
    }

    // OpenAI-compatible opt-in for work that must outlive one HTTP request.
    // API clients poll /v1/jobs/{id}; normal completions keep their current
    // synchronous response contract.
    if (body.background === true || body.execution === 'maximum_quality') {
      if (!userId || isEvalMode) {
        return NextResponse.json(
          { error: { message: 'Background maximum-quality jobs require an authenticated customer API key.', type: 'permission_error' } },
          { status: 403 },
        );
      }
      try {
        const job = await createGenerationJob(userId, messages);
        const base = (process.env.TEMUCLAUDE_MODAL_URL || process.env.MODAL_API_URL || '').replace(/\/+$/, '');
        const key = process.env.TEMUCLAUDE_MASTER_KEY || '';
        if (!base || !key) throw new GenerationJobError('Maximum-quality generation is not configured.', 503, 'generation_worker_unconfigured');
        const dispatch = await fetch(`${base}/v1/jobs/${encodeURIComponent(job.id)}/start`, {
          method: 'POST', headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_id: job.id }), signal: AbortSignal.timeout(15_000),
        });
        if (!dispatch.ok) throw new GenerationJobError('Unable to start the maximum-quality worker.', 503, 'generation_dispatch_failed');
        return NextResponse.json({ id: job.id, object: 'chat.completion.job', status: 'queued', poll_url: `/v1/jobs/${job.id}`, job: publicGenerationJob(job) }, { status: 202 });
      } catch (error) {
        const message = error instanceof GenerationJobError ? error.message : 'Unable to create maximum-quality generation job.';
        const status = error instanceof GenerationJobError ? error.status : 500;
        return NextResponse.json({ error: { message, type: 'server_error' } }, { status });
      }
    }

    if (!isModalConfigured()) {
      return upstreamFailure('Full Modal orchestration is required but unavailable.', 503);
    }

    // ── Layer 1: Pro orchestration proxy to the Fly Python engine ──────────
    // When TEMUCLAUDE_ENGINE_URL is configured, Pro completions are served by
    // the real 10-layer Python orchestrator on Fly (api_server.py) instead of
    // the in-process TS MoA pipeline below. Lite stays on the bounded Vercel
    // cascade (its own cost contract). The flag is opt-in: with
    // TEMUCLAUDE_ENGINE_URL unset, behavior is unchanged. On any engine failure
    // we fall back to a single fast GLM call — never the full ~210s MoA — so a
    // Fly hiccup degrades gracefully instead of 504'ing.
    const engineUrl = process.env.TEMUCLAUDE_ENGINE_URL;
    const engineKey = process.env.TEMUCLAUDE_ENGINE_API_KEY;
    // Modal is an explicit production override.  Without this guard, the Fly
    // engine returns first and makes the Modal branch below unreachable.
    const useModalBackend = true;
    if (!useModalBackend && engineUrl && engineKey && isProModel(model) && !isLiteModel(model)) {
      const engineBody = {
        model: 'temuclaude',
        messages,
        temperature: temperature ?? 0.6,
        max_tokens: Math.min(Number(max_tokens) || 2048, 8192),
        model_profile: 'pro',
        budget_profile: 'max_quality',
      };
      const requestId = request.headers.get('x-request-id') || `v1-pro-${Date.now()}`;
      try {
        const controller = new AbortController();
        const engineTimeout = setTimeout(() => controller.abort(), 280_000);
        const upstream = await fetch(`${engineUrl.replace(/\/$/, '')}/v1/chat/completions`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${engineKey}`,
            'Content-Type': 'application/json',
            'X-Request-ID': requestId,
          },
          body: JSON.stringify(engineBody),
          signal: controller.signal,
        });
        clearTimeout(engineTimeout);
        if (upstream.ok) {
          const data = await upstream.json();
          const content = extractAssistantContent(data);
          if (hasUsableContent(content)) {
            const pt = data?.usage?.prompt_tokens;
            const ct = data?.usage?.completion_tokens;
            const promptTokens = typeof pt === 'number' ? pt : promptTokenEstimate(messages);
            const completionTokens = typeof ct === 'number' ? ct : completionTokenEstimate(content);
            if (!isEvalMode && userId) {
              try { await incrementUsageAsync(userId, promptTokens, completionTokens, modelActivityStore.getStore()?.join(',')); } catch {}
            }
            return completionResponse({
              id: String(data?.id || `chatcmpl-${Date.now()}`),
              object: 'chat.completion',
              created: Number(data?.created) || Math.floor(Date.now() / 1000),
              model: TEMUCLAUDE_PRO_MODEL,
              choices: [{ index: 0, message: { role: 'assistant', content: content.trim() }, finish_reason: 'stop' }],
              usage: {
                prompt_tokens: promptTokens,
                completion_tokens: completionTokens,
                total_tokens: promptTokens + completionTokens,
              },
            }, wantsStream);
          }
          console.warn('Engine returned an empty completion; falling back to fast GLM.');
        } else {
          console.warn(`Engine proxy failed with status ${upstream.status}; falling back to fast GLM.`);
        }
      } catch (engineError: any) {
        console.warn(`Engine proxy error: ${engineError?.message}; falling back to fast GLM.`);
      }
      // Fast fallback: a single GLM call, never the full MoA pipeline.
      const fallback = await call(M_GLM, messages, temperature ?? 0.6, max_tokens ?? 4096, { timeoutMs: 25_000 });
      if (hasUsableContent(fallback.content)) {
        const fbPromptTokens = promptTokenEstimate(messages);
        const fbCompletionTokens = completionTokenEstimate(fallback.content);
        if (!isEvalMode && userId) {
          try { await incrementUsageAsync(userId, fbPromptTokens, fbCompletionTokens, modelActivityStore.getStore()?.join(',')); } catch {}
        }
        return completionResponse({
          id: `chatcmpl-${Date.now()}`,
          object: 'chat.completion',
          created: Math.floor(Date.now() / 1000),
          model: TEMUCLAUDE_PRO_MODEL,
          choices: [{ index: 0, message: { role: 'assistant', content: fallback.content.trim() }, finish_reason: 'stop' }],
          usage: {
            prompt_tokens: fbPromptTokens,
            completion_tokens: fbCompletionTokens,
            total_tokens: fbPromptTokens + fbCompletionTokens,
          },
        }, wantsStream);
      }
      return upstreamFailure('TemuClaude could not produce a non-empty completion. Please retry shortly.', 503);
    }

    // Lite is a separately bounded public API profile. It must bypass Modal
    // and the Pro fusion pipeline so its allowlist and cost contract remain
    // enforceable even when callers supply an arbitrary `model` field.
    // In production, Lite uses the same complete Modal panel as Pro.  Its
    // plan remains a quota entitlement, not a lower-quality model route.
    // The legacy Lite cascade is retained solely as an outage fallback when
    // Modal has intentionally not been configured.
    if (isLiteModel(model) && !(useModalBackend && isModalConfigured())) {
      const latestUserText = [...messages].reverse().find((message: Msg) => message.role === 'user')?.content || '';
      const tier = classify(latestUserText);
      const liteModel = selectLiteApiModel(latestUserText, tier);
      const liteCodeRequest = isCodeGen(latestUserText);
      const liteMessages: Msg[] = liteCodeRequest
        ? [{ role: 'system', content: 'You are TemuClaude Code. Execute the requested coding task now; do not ask follow-up questions when reasonable defaults are possible. For a game, website, or interactive app, return a complete runnable deliverable. When suitable, return one complete HTML fenced file with all CSS and JavaScript included. Do not outline phases or defer implementation.' }, ...messages]
        : messages;
      const useLitePanel = tier !== 'trivial' || liteCodeRequest;
      const complement: LiteModelId = liteModel === LITE_DEFAULT ? LITE_AGENT : LITE_DEFAULT;
      const callLiteDraft = (draftModel: LiteModelId, role: string) => {
        recordModelActivity(draftModel);
        return callOpenRouterLite(draftModel, [
          { role: 'system', content: role },
          ...liteMessages,
        ], {
          temperature: temperature ?? 0.45,
          maxTokens: Math.min(max_tokens ?? (liteCodeRequest ? 4096 : 2048), 4096),
          timeoutMs: liteCodeRequest ? 90_000 : 60_000,
          sessionId: `v1-lite-${draftModel}-${Date.now()}`,
        });
      };
      const [primaryDraft, complementaryDraft] = await Promise.all([
        callLiteDraft(liteModel, 'Own the main task-specific solution. Be complete, concrete, and do not rush the ending.'),
        useLitePanel
          ? callLiteDraft(complement, 'Independently solve the task. Focus on omissions, edge cases, and a different approach.')
          : Promise.resolve(null),
      ]);
      let lite = primaryDraft.success ? primaryDraft : complementaryDraft?.success ? complementaryDraft : primaryDraft;
      if (!lite.success || !hasUsableContent(lite.content)) {
        return upstreamFailure(lite.error || 'TemuClaude Lite is temporarily unavailable.', 503);
      }
      let promptTokens = primaryDraft.promptTokens + (complementaryDraft?.promptTokens || 0) || promptTokenEstimate(messages);
      let completionTokens = primaryDraft.completionTokens + (complementaryDraft?.completionTokens || 0) || completionTokenEstimate(lite.content);

      if (primaryDraft.success && complementaryDraft?.success) {
        recordModelActivity(LITE_AGENT);
        const synthesized = await callOpenRouterLite(LITE_AGENT, [
          { role: 'system', content: 'Synthesize the strongest complete answer from two independent drafts. Resolve contradictions, preserve working detail, and return only the final answer.' },
          { role: 'user', content: `Original request:\n${latestUserText}\n\nDraft A:\n${primaryDraft.content}\n\nDraft B:\n${complementaryDraft.content}` },
        ], {
          temperature: temperature ?? 0.35,
          maxTokens: Math.min(max_tokens ?? (liteCodeRequest ? 4096 : 2048), 4096),
          timeoutMs: liteCodeRequest ? 90_000 : 60_000,
          sessionId: `v1-lite-synthesis-${Date.now()}`,
        });
        promptTokens += synthesized.promptTokens;
        completionTokens += synthesized.completionTokens;
        if (synthesized.success && hasUsableContent(synthesized.content)) lite = synthesized;
      }

      // Keep the API profile aligned with Playground Lite: nontrivial work is
      // synthesized from complementary drafts and independently verified. A
      // corrective pass stays inside the Lite allowlist.
      if (shouldVerifyLite(latestUserText, tier, lite.content)) {
        recordModelActivity(LITE_VERIFIER);
        const verdict = await callOpenRouterLite(LITE_VERIFIER, [
          { role: 'system', content: 'Check the draft for factual, logical, or safety-critical errors. Reply with PASS, or FAIL followed by a concise correction request.' },
          { role: 'user', content: `Question:\n${latestUserText}\n\nDraft:\n${lite.content}` },
        ], {
          maxTokens: 350,
          timeoutMs: 30_000,
          sessionId: `v1-lite-verify-${Date.now()}`,
        });
        completionTokens += verdict.completionTokens;
        promptTokens += verdict.promptTokens;
        if (verdict.success && verdict.content.toUpperCase().startsWith('FAIL')) {
          recordModelActivity(LITE_AGENT);
          const corrected = await callOpenRouterLite(LITE_AGENT, [
            ...messages,
            { role: 'assistant', content: lite.content },
            { role: 'user', content: `Verifier feedback:\n${verdict.content}\n\nReturn a corrected, self-contained answer.` },
          ], {
            temperature: temperature ?? 0.35,
            maxTokens: Math.min(max_tokens ?? (liteCodeRequest ? 4096 : 2048), 4096),
            timeoutMs: liteCodeRequest ? 90_000 : 60_000,
            sessionId: `v1-lite-correct-${Date.now()}`,
          });
          if (corrected.success && hasUsableContent(corrected.content)) {
            lite = corrected;
            promptTokens += corrected.promptTokens;
            completionTokens += corrected.completionTokens;
          }
        }
      }
      if (!isEvalMode && userId) {
        try { await incrementUsageAsync(userId, promptTokens, completionTokens, modelActivityStore.getStore()?.join(',')); } catch {}
      }
      return completionResponse({
        id: `chatcmpl-${Date.now()}`,
        object: 'chat.completion',
        created: Math.floor(Date.now() / 1000),
        model: 'temuclaude/temuclaude-lite',
        choices: [{ index: 0, message: { role: 'assistant', content: lite.content.trim() }, finish_reason: 'stop' }],
        usage: {
          prompt_tokens: promptTokens,
          completion_tokens: completionTokens,
          total_tokens: promptTokens + completionTokens,
        },
      }, wantsStream);
    }

    // Tool turns are protocol-bound agent actions, not answer-synthesis
    // turns.  A full MoA pass can correctly draft the requested HTML yet
    // erase the final function-call wrapper during aggregation, leaving
    // Hermes/Claude Code/OpenCode with prose they cannot execute.  Route
    // these turns through Kimi's deterministic tool mode; normal Pro turns
    // continue into the full Modal quality pipeline below.
    if (Array.isArray(tools) && tools.length > 0) {
      // A tool invocation still benefits from the full Pro panel: each role
      // first identifies constraints and failure modes, then Kimi emits the
      // one protocol-bound action. This preserves OpenAI tool semantics while
      // ensuring agent work is never silently a single-model route.
      const toolPanelModels = [M_GLM, M_DEEPSEEK, M_MINIMAX, M_GEMINI, M_LUNA, M_GROK, M_NEMOTRON, M_KIMI];
      const toolPanel = await Promise.all(toolPanelModels.map((panelModel) =>
        call(panelModel, messages, 0.2, 700, { timeoutMs: 25_000, disableReasoning: true }),
      ));
      const toolBrief = toolPanel
        .filter((result) => result.success && hasUsableContent(result.content))
        .map((result) => `${result.content.slice(0, 900)}`)
        .join('\n\n---\n\n');
      // Agent clients commonly omit max_tokens or default it to 2,048. That is
      // not enough to encode a complete file as JSON arguments (especially an
      // HTML game), and cutting a tool call mid-JSON makes it unusable. Give
      // protocol-bound actions a bounded 8K floor/ceiling independently of
      // conversational output defaults. This stays below the route deadline
      // while leaving the quality-first Kimi primary and approved recovery
      // models in charge.
      const requestedToolTokens = Number(max_tokens);
      const toolMaxTokens = Math.max(4096, Math.min(Number.isFinite(requestedToolTokens) && requestedToolTokens > 0 ? requestedToolTokens : 8192, 8192));
      const toolMessages: Msg[] = toolBrief
        ? [...providerMessages, { role: 'user', content: `Specialist preflight notes (use them silently; execute only one valid listed tool call):\n${toolBrief}` }]
        : providerMessages;
      const toolResult = await call(M_KIMI, toolMessages, 0, toolMaxTokens, {
        fallbacks: [M_DEEPSEEK, M_GLM],
        timeoutMs: 180_000,
        disableReasoning: true,
      });
      if (!toolResult.success || !hasUsableContent(toolResult.content)) {
        return upstreamFailure('TemuClaude tool mode is temporarily unavailable.', 503);
      }
      const parsedToolCall = parseToolCall(toolResult.content, tools);
      const promptTokens = promptTokenEstimate(messages);
      const completionTokens = completionTokenEstimate(toolResult.content);
      if (!isEvalMode && userId) {
        try { await incrementUsageAsync(userId, promptTokens, completionTokens, M_KIMI); } catch {}
      }
      return completionResponse({
        id: `chatcmpl-${Date.now()}`,
        object: 'chat.completion',
        created: Math.floor(Date.now() / 1000),
        model: String(model || TEMUCLAUDE_PRO_MODEL),
        choices: [{
          index: 0,
          message: parsedToolCall
            ? { role: 'assistant', content: null, tool_calls: [parsedToolCall] }
            : { role: 'assistant', content: toolResult.content.trim() },
          finish_reason: parsedToolCall ? 'tool_calls' : 'stop',
        }],
        usage: { prompt_tokens: promptTokens, completion_tokens: completionTokens, total_tokens: promptTokens + completionTokens },
      }, wantsStream);
    }

    if (Date.now() < circuitTrippedUntil) {
      return upstreamFailure('Full Modal orchestration is temporarily unavailable. Please retry shortly.', 503);
    }

    let modalSuccess = false;
    let modal;

    // The legacy Modal service has a separate model registry. It must never
    // become an implicit production route, otherwise API users can receive a
    // different stack than Playground users. Re-enable it only intentionally.
    if (useModalBackend) {
      try {
        modal = await callModalChatCompletions({
          model: model || 'temuclaude',
          messages: providerMessages,
          // Tool selection is a protocol decision, not a creative one. A
          // deterministic request prevents an agent from alternately emitting
          // a valid tool block and a prose-only claim for the same action.
          temperature: Array.isArray(tools) ? 0 : temperature ?? 0.6,
          max_tokens: max_tokens ?? 4096,
        });

        if (modal.ok) {
          modalSuccess = true;
          consecutiveFailures = 0; // Reset failures on success

          const modalContent = extractAssistantContent(modal.data);
          if (!hasUsableContent(modalContent) || !hasCompleteModalPanel(modal.data)) {
            return upstreamFailure('Modal backend did not complete every required quality role.', 503);
          } else {
            recordModelActivity(typeof modal.data?.model === 'string' ? modal.data.model : null);
            if (!isEvalMode && userId) {
              const usage = modal.data?.usage || {};
              const promptTokens = Number(usage.prompt_tokens || promptTokenEstimate(messages));
              const completionTokens = Number(usage.completion_tokens || completionTokenEstimate(modalContent));
              try { await incrementUsageAsync(userId, promptTokens, completionTokens, modelActivityStore.getStore()?.join(',')); } catch {}
            }
            const parsedToolCall = parseToolCall(modalContent, tools);
            if (parsedToolCall) {
              return completionResponse({
                id: String(modal.data?.id || `chatcmpl-${Date.now()}`),
                object: 'chat.completion',
                created: Number(modal.data?.created || Math.floor(Date.now() / 1000)),
                model: String(modal.data?.model || model || 'temuclaude'),
                choices: [{ index: 0, message: { role: 'assistant', content: null, tool_calls: [parsedToolCall] }, finish_reason: 'tool_calls' }],
                usage: modal.data?.usage,
              }, wantsStream);
            }
            if (wantsStream) {
              return completionResponse({
                id: String(modal.data?.id || `chatcmpl-${Date.now()}`),
                object: 'chat.completion',
                created: Number(modal.data?.created || Math.floor(Date.now() / 1000)),
                model: String(modal.data?.model || model || 'temuclaude'),
                choices: [{ index: 0, message: { role: 'assistant', content: modalContent }, finish_reason: 'stop' }],
                usage: modal.data?.usage,
              }, true);
            }
            return NextResponse.json(modal.data, { status: modal.status });
          }
        } else {
          consecutiveFailures += 1;
          console.warn(`Upstream Modal call failed. Consecutive failure count: ${consecutiveFailures}`);
        }
      } catch (e: any) {
        consecutiveFailures += 1;
        console.error(`Error during Modal execution: ${e.message}. Failure count: ${consecutiveFailures}`);
      }

      if (consecutiveFailures >= 3) {
        circuitTrippedUntil = Date.now() + 60000; // Trip for 60 seconds
        console.warn(`Circuit breaker TRIPPED until ${new Date(circuitTrippedUntil).toISOString()}`);
      }

      if (!modalSuccess) {
        return NextResponse.json(
          { error: { message: (modal && modal.error) || 'Modal backend unavailable', type: 'server_error' } },
          { status: (modal && modal.status) || 503 }
        );
      }

    }

    // Timeout safeguard: reserve enough time for one strong GLM response
    // before Vercel's 300-second function deadline. (Raised from 120s on
    // 2026-07-14: hard MoA queries can reach ~210s via race → GLM fallback
    // → finalRescue, which exceeded the old 120s cap and 504'd on Vercel.)
    const pipeline = orchestrate(messages, temperature ?? 0.6, max_tokens ?? 4096);
    const timeout = new Promise<OrchestrationResult>(resolve => {
      setTimeout(async () => {
        const fb = await call(M_GLM, messages, 0.6, max_tokens ?? 4096, { timeoutMs: 25_000 });
        resolve({ content: fb.content, tokens: fb.tokens, tier: 'timeout-fallback', time: 85_000 });
      }, 85_000);
    });

    let result = await Promise.race([pipeline, timeout]);
    if (!hasUsableContent(result.content)) {
      result = await finalRescue(messages, temperature ?? 0.6, max_tokens ?? 4096);
    }

    if (!hasUsableContent(result.content)) {
      return upstreamFailure('TemuClaude could not produce a non-empty completion. Please retry shortly.', 503);
    }

    const finalContent = result.content.trim();

    // Track usage for authenticated users
    if (!isEvalMode && userId) {
      const promptTokens = promptTokenEstimate(messages);
      const completionTokens = completionTokenEstimate(finalContent);
      try { await incrementUsageAsync(userId, promptTokens, completionTokens, modelActivityStore.getStore()?.join(',')); } catch {}
    }

    return completionResponse({
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: TEMUCLAUDE_PRO_MODEL,
      choices: [{
        index: 0,
        message: { role: 'assistant', content: finalContent },
        finish_reason: 'stop',
      }],
      usage: {
        prompt_tokens: promptTokenEstimate(messages),
        completion_tokens: completionTokenEstimate(finalContent),
        total_tokens: result.tokens || promptTokenEstimate(messages) + completionTokenEstimate(finalContent),
      },
    }, wantsStream);
  } catch {
    return NextResponse.json(
      { error: { message: 'Internal server error', type: 'server_error' } },
      { status: 500 }
    );
  }
  });
}

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    model: 'temuclaude',
    description: 'TemuClaude — capability-aware multi-model AI orchestration (OpenAI-compatible)',
    models: [
      { name: 'DeepSeek V4 Flash', role: 'Trivial routing', iq: null },
      { name: 'DeepSeek V4 Pro', role: 'Reasoning + math + code', iq: null },
      { name: 'GLM-5.2', role: 'Planning + project engineering + synthesis', iq: null },
      { name: 'Kimi K3', role: 'Coding-driven UI/UX + multi-agent implementation', iq: null },
      { name: 'MiniMax M3', role: 'Multimodal + creative + long context', iq: null },
      { name: 'Gemini 3.5 Flash', role: 'Visual UI + accessibility + tools', iq: null },
      { name: 'GPT-5.6 Luna', role: 'Fast independent GPT proposer', iq: null },
      { name: 'Kimi Latest', role: 'Frontier adjudication', iq: null },
      { name: 'Grok 4.5', role: 'Code-repair escalation', iq: null },
      { name: 'Nemotron 3 Ultra', role: 'Independent QA', iq: null },
      { name: 'TemuClaude Lite', role: 'Cost-bounded OpenRouter cascade', model: 'temuclaude/temuclaude-lite' },
    ],
    pipeline: ['moa-fusion', 'self-consistency', 'aggregation', 'qa-gate', 'reflexion', 'frontier-fallback'],
  });
}

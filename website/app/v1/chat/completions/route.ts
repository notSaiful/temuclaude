/** OpenAI-compatible chat completions with automatic model selection. */
import { NextRequest, NextResponse } from 'next/server';
import { createHash, timingSafeEqual } from 'crypto';
import { AsyncLocalStorage } from 'node:async_hooks';
import { validateApiKeyAsync, getMonthUsageAsync, getTodayUsageAsync, incrementUsageAsync, getRollingWindowUsageAsync, verifyAndRenewWeeklyCreditsAsync } from '@/lib/db';
import { PLAN_LIMITS } from '@/lib/plans';
import { callOpenRouter } from '@/lib/openrouter';
import { callOpenRouterLite, type LiteModelId } from '@/lib/openrouter-lite';
import { callModalChatCompletions, isModalConfigured, isModalRequired } from '@/lib/modal';
import { LITE_MODEL_POOL, MODEL_IDS, PUBLIC_API_MODELS, PUBLIC_MODEL_ROLES } from '@/lib/model-catalog';
import { validateChatMessages, validateMaxTokens, validateTemperature } from '@/lib/chat-contract';

// Global in-memory circuit breaker state (retained during warm serverless container instances)
let consecutiveFailures = 0;
let circuitTrippedUntil = 0;
// One request can invoke several models in parallel. AsyncLocalStorage keeps
// that invocation list isolated per request, including across Promise.all.
const modelActivityStore = new AsyncLocalStorage<string[]>();

export const runtime = 'nodejs';
// Raised from 120s to 300s on 2026-07-14: hard requests can reach ~210s via
// the 85s race -> empty GLM fallback -> finalRescue chain, which exceeded the
// old 120s Vercel cap and 504'd. 300s is the Vercel plan ceiling.
export const maxDuration = 300;

// ── 8-MODEL POOL ──────────────────────────────────────────────
const M_FLASH = MODEL_IDS.flash;
const M_DEEPSEEK = MODEL_IDS.reasoning;
const M_GLM = MODEL_IDS.planner;
const M_MINIMAX = MODEL_IDS.creative;
const M_GEMINI = MODEL_IDS.multimodal;
const M_LUNA = MODEL_IDS.qualityEscalation;
const M_GROK = MODEL_IDS.codeRepair;
const M_NEMOTRON = MODEL_IDS.verifier;
const M_TERRA = MODEL_IDS.emergencyEscalation;
const LITE_DEFAULT: LiteModelId = LITE_MODEL_POOL.default;
const LITE_REASONING: LiteModelId = LITE_MODEL_POOL.reasoning;
const LITE_AGENT: LiteModelId = LITE_MODEL_POOL.agent;
const LITE_VERIFIER: LiteModelId = LITE_MODEL_POOL.verifier;
const TEMUCLAUDE_PRO_MODEL = PUBLIC_API_MODELS.pro;

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

function bearerToken(request: NextRequest): string {
  const authorization = request.headers.get('authorization') || '';
  const match = authorization.match(/^Bearer\s+(.+)$/i);
  return match?.[1]?.trim() || request.headers.get('x-api-key')?.trim() || '';
}

function secretsEqual(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left, 'utf8');
  const rightBuffer = Buffer.from(right, 'utf8');
  return leftBuffer.length === rightBuffer.length && timingSafeEqual(leftBuffer, rightBuffer);
}

function extractAssistantContent(data: unknown): string {
  if (!data || typeof data !== 'object') return '';
  const choices = (data as Record<string, unknown>).choices;
  if (!Array.isArray(choices) || !choices[0] || typeof choices[0] !== 'object') return '';
  const message = (choices[0] as Record<string, unknown>).message;
  if (!message || typeof message !== 'object') return '';
  const content = (message as Record<string, unknown>).content;
  return typeof content === 'string' ? content : '';
}

async function recordApiUsage(userId: string, promptTokens: number, completionTokens: number): Promise<void> {
  try {
    await incrementUsageAsync(userId, promptTokens, completionTokens, modelActivityStore.getStore());
  } catch (error) {
    console.error('API usage recording failed:', error instanceof Error ? error.message : 'unknown error');
  }
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

/**
 * Return either the established JSON completion contract or a small,
 * standards-compliant OpenAI SSE sequence.  The pipeline deliberately
 * completes before emitting: orchestration depends on several model calls,
 * but clients that request `stream: true` (including AI SDK consumers such as
 * Obsidian LLM Wiki) still receive the protocol they expect.
 */
function completionResponse(payload: CompletionPayload, stream: boolean): NextResponse {
  if (!stream) return NextResponse.json(payload);

  const content = String((payload.choices[0]?.message as { content?: string } | undefined)?.content || '');
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
      if (content) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          ...chunkBase,
          choices: [{ index: 0, delta: { content }, finish_reason: null }],
        })}\n\n`));
      }
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({
        ...chunkBase,
        choices: [{ index: 0, delta: {}, finish_reason: 'stop' }],
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
  const result = await call(M_FLASH, messages, temp, maxTok, {
    fallbacks: [M_GLM, M_DEEPSEEK, M_TERRA],
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
 * Difficulty Classifier — heuristic, no API call.
 * Code generation tasks route to one strong model instead of the multi-draft route.
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

  // Code generation uses one strong model rather than merging several drafts.
  // Code needs one strong model with high max_tokens, not 3 models debating.
  const isCodeGen = /\b(build|create|generate|write|make|develop|implement|code|html|css|javascript|python|function|class|component|game|website|webpage|app|script|program|landing page|dashboard)\b/i.test(l) &&
                    /\b(html|css|js|javascript|python|code|function|component|page|game|app|script|file|complete)\b/i.test(l);
  if (isCodeGen) return 'medium';

  // General coding keywords still add to score but won't force hard if code gen detected
  if (/\b(function|code|debug|program|algorithm|python|javascript|implement|write.*code|compile|runtime|complexity|recursive|sort|search)\b/i.test(l)) s += 3;

  if (s >= 7) return 'hard';
  if (s >= 3) return 'medium';
  return 'trivial';
}

/**
 * Detect if the query is a code generation task (not a code reasoning/debugging task).
 * Code generation should route to a single strong model.
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
  if (isCodeGen(query)) return false;
  if (tier !== 'hard' || answer.trim().length < 80) return tier === 'hard';
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
 * Full 8-Model Orchestration Pipeline
 */
async function orchestrate(messages: Msg[], temp: number, maxTok: number) {
  const start = Date.now();
  let tokens = 0;
  const q = messages[messages.length - 1]?.content || '';
  const diff = classify(q);
  const math = isMath(q);
  const creative = isCreative(q);
  const multimodal = isMultimodal(q);

  // A code or game request needs a complete file, not a fusion discussion.
  // This is deliberately the same direct delivery contract used by Playground.
  if (isCodeGen(q)) {
    const r = await call(M_DEEPSEEK, [
      { role: 'system', content: 'You are TemuClaude Code. Execute the request now; do not ask follow-up questions when reasonable defaults are possible. Return a complete, runnable deliverable. For a single-file web game, output one complete HTML fenced file with all CSS and JavaScript included. Do not describe phases or defer implementation.' },
      ...messages,
    ], 0.35, Math.min(Math.max(maxTok, 4096), 8192), {
      fallbacks: [M_GLM, M_GROK],
      timeoutMs: 100_000,
    });
    return { content: r.content, tokens: r.tokens, tier: 'direct-code-generation', time: Date.now() - start };
  }

  // ── TRIVIAL: DeepSeek V4 Flash ──
  if (diff === 'trivial') {
    const r = await call(M_FLASH, messages, temp, maxTok);
    if (r.success && r.content) {
      return { content: r.content, tokens: r.tokens, tier: 'trivial', time: Date.now() - start };
    }
    // Fallback to GLM if Flash fails
    const r2 = await call(M_GLM, messages, temp, maxTok);
    return { content: r2.content, tokens: r2.tokens, tier: 'trivial-fallback', time: Date.now() - start };
  }

  // ── MEDIUM: Route to best specialist ──
  if (diff === 'medium') {
    let model: string = M_GLM;
    if (math) model = M_DEEPSEEK;
    else if (creative) model = M_MINIMAX;
    else if (multimodal) model = M_GEMINI;
    // Code generation uses GLM (best at following complex instructions)
    // isCodeGen already detected by classifier, routing here is automatic via medium
    const r = await call(model, messages, temp, maxTok);
    return { content: r.content, tokens: r.tokens, tier: 'medium', time: Date.now() - start };
  }

  // Hard requests use parallel drafts followed by review and synthesis.

  // MATH: self-consistency replaces single DeepSeek call (runs parallel)
  if (math) {
    const [r1, r3, sc] = await Promise.all([
      call(M_GLM, messages, temp, maxTok),
      call(M_NEMOTRON, messages, temp, maxTok),
      selfConsistency(q, maxTok),
    ]);
    tokens += r1.tokens + r3.tokens + sc.tokens;

    const l1: { name: string; content: string }[] = [];
    if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
    if (sc.answer) l1.push({ name: 'Model B (DeepSeek, self-consistency)', content: sc.answer });
    if (r3.success && r3.content) l1.push({ name: 'Model C (Nemotron 3 Ultra)', content: r3.content });

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
        const frontier = await call(M_LUNA, messages, temp, maxTok);
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
    const [r1, r2, r3] = await Promise.all([
      call(M_GLM, messages, temp, maxTok),
      call(M_DEEPSEEK, messages, temp, maxTok),
      call(M_MINIMAX, messages, temp, maxTok),
    ]);
    tokens += r1.tokens + r2.tokens + r3.tokens;

    const l1: { name: string; content: string }[] = [];
    if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
    if (r2.success && r2.content) l1.push({ name: 'Model B (DeepSeek V4 Pro)', content: r2.content });
    if (r3.success && r3.content) l1.push({ name: 'Model C (MiniMax M3, creative)', content: r3.content });

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
        const frontier = await call(M_LUNA, messages, temp, maxTok);
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

  // HARD (general): core three-model panel only; premium models do not join by default.
  const [r1, r2, r3] = await Promise.all([
    call(M_GLM, messages, temp, maxTok),
    call(M_DEEPSEEK, messages, temp, maxTok),
    call(M_NEMOTRON, messages, temp, maxTok),
  ]);
  tokens += r1.tokens + r2.tokens + r3.tokens;

  const l1: { name: string; content: string }[] = [];
  if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
  if (r2.success && r2.content) l1.push({ name: 'Model B (DeepSeek V4 Pro)', content: r2.content });
  if (r3.success && r3.content) l1.push({ name: 'Model C (Nemotron 3 Ultra)', content: r3.content });

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
      const frontier = await call(M_LUNA, messages, temp, maxTok);
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

export async function POST(request: NextRequest) {
  return modelActivityStore.run([], async () => {
  try {
    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return NextResponse.json(
        { error: { message: 'Request body must be valid JSON', type: 'invalid_request_error' } },
        { status: 400 }
      );
    }
    const payload = body && typeof body === 'object' ? body as Record<string, unknown> : {};
    const model = payload.model;
    const validatedMessages = validateChatMessages(payload.messages, ['system', 'user', 'assistant'] as const);
    if ('error' in validatedMessages) {
      return NextResponse.json({ error: { message: validatedMessages.error, type: 'invalid_request_error' } }, { status: 400 });
    }
    const messages: Msg[] = validatedMessages.messages;
    const temperature = validateTemperature(payload.temperature);
    if (temperature && typeof temperature === 'object') {
      return NextResponse.json({ error: { message: temperature.error, type: 'invalid_request_error' } }, { status: 400 });
    }
    const max_tokens = validateMaxTokens(payload.max_tokens);
    if (max_tokens && typeof max_tokens === 'object') {
      return NextResponse.json({ error: { message: max_tokens.error, type: 'invalid_request_error' } }, { status: 400 });
    }
    if (payload.stream !== undefined && typeof payload.stream !== 'boolean') {
      return NextResponse.json({ error: { message: 'stream must be a boolean', type: 'invalid_request_error' } }, { status: 400 });
    }
    const wantsStream = payload.stream === true;

    // ── Auth & Usage ──────────────────────────────────────
    // 1. Try API key (Bearer token or x-api-key header)
    const apiKey = bearerToken(request);
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;

    let userId: string | null = null;
    let userPlan = 'free';
    let isEvalMode = false; // open access for benchmarking platforms
    const allowAnonymousApi = process.env.TEMUCLAUDE_ALLOW_PUBLIC_API === 'true';

    if (apiKey) {
      // Check master key first (for evaluation platforms — AA, LMSys, LiveBench, etc.)
      if (masterKey && secretsEqual(apiKey, masterKey)) {
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

    if (!isLiteModel(model) && !isProModel(model)) {
      return NextResponse.json(
        { error: { message: 'Unsupported model. Use temuclaude/temuclaude-pro or temuclaude/temuclaude-lite.', type: 'invalid_request_error' } },
        { status: 400 },
      );
    }

    // Lite is a separately bounded public API profile. It must bypass Modal
    // and the Pro fusion pipeline so its allowlist and cost contract remain
    // enforceable even when callers supply an arbitrary `model` field.
    if (isLiteModel(model)) {
      const latestUserText = [...messages].reverse().find((message: Msg) => message.role === 'user')?.content || '';
      const tier = classify(latestUserText);
      const liteModel = selectLiteApiModel(latestUserText, tier);
      const liteCodeRequest = isCodeGen(latestUserText);
      const liteMessages: Msg[] = liteCodeRequest
        ? [{ role: 'system', content: 'You are TemuClaude Code. Execute the requested coding task now; do not ask follow-up questions when reasonable defaults are possible. For a game, website, or interactive app, return a complete runnable deliverable. When suitable, return one complete HTML fenced file with all CSS and JavaScript included. Do not outline phases or defer implementation.' }, ...messages]
        : messages;
      recordModelActivity(liteModel);
      let lite = await callOpenRouterLite(liteModel, liteMessages, {
        temperature: temperature ?? 0.45,
        maxTokens: Math.min(max_tokens ?? (liteCodeRequest ? 3072 : 2048), 4096),
        timeoutMs: 60_000,
        sessionId: `v1-lite-${Date.now()}`,
      });
      if (!lite.success || !hasUsableContent(lite.content)) {
        return upstreamFailure(lite.error || 'TemuClaude Lite is temporarily unavailable.', 503);
      }
      let promptTokens = lite.promptTokens || promptTokenEstimate(messages);
      let completionTokens = lite.completionTokens || completionTokenEstimate(lite.content);

      // Keep the API profile aligned with Playground Lite: an independent
      // critic runs only for high-risk, explicit-check, or audit-sampled work.
      // A correction makes at most three Lite model calls in total.
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
          recordModelActivity(liteModel);
          const corrected = await callOpenRouterLite(liteModel, [
            ...messages,
            { role: 'assistant', content: lite.content },
            { role: 'user', content: `Verifier feedback:\n${verdict.content}\n\nReturn a corrected, self-contained answer.` },
          ], {
            temperature: temperature ?? 0.35,
            maxTokens: Math.min(max_tokens ?? 2048, 4096),
            timeoutMs: 60_000,
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
        await recordApiUsage(userId, promptTokens, completionTokens);
      }
      return completionResponse({
        id: `chatcmpl-${Date.now()}`,
        object: 'chat.completion',
        created: Math.floor(Date.now() / 1000),
        model: PUBLIC_API_MODELS.lite,
        choices: [{ index: 0, message: { role: 'assistant', content: lite.content.trim() }, finish_reason: 'stop' }],
        usage: {
          prompt_tokens: promptTokens,
          completion_tokens: completionTokens,
          total_tokens: promptTokens + completionTokens,
        },
      }, wantsStream);
    }

    let useFallbackRoute = false;
    if (Date.now() < circuitTrippedUntil) {
      console.warn('Circuit breaker is TRIPPED. Routing to fallback pool directly.');
      useFallbackRoute = true;
    }

    let modalSuccess = false;
    let modal;

    // The legacy Modal service has a separate model registry. It must never
    // become an implicit production route, otherwise API users can receive a
    // different stack than Playground users. Re-enable it only intentionally.
    const useModalBackend = process.env.TEMUCLAUDE_USE_MODAL_BACKEND === 'true';
    if (!useFallbackRoute && useModalBackend && isModalConfigured()) {
      try {
        modal = await callModalChatCompletions({
          model: model || 'temuclaude',
          messages,
          temperature: temperature ?? 0.6,
          max_tokens: max_tokens ?? 4096,
        });

        if (modal.ok) {
          modalSuccess = true;
          consecutiveFailures = 0; // Reset failures on success

          const modalContent = extractAssistantContent(modal.data);
          if (!hasUsableContent(modalContent)) {
            if (isModalRequired()) {
              return upstreamFailure('Modal backend returned an empty completion.', 503);
            }
            console.warn('Modal backend returned an empty completion, falling back to in-process pipeline.');
          } else {
            recordModelActivity(typeof modal.data?.model === 'string' ? modal.data.model : null);
            if (!isEvalMode && userId) {
              const usage = modal.data?.usage || {};
              const promptTokens = Number(usage.prompt_tokens || promptTokenEstimate(messages));
              const completionTokens = Number(usage.completion_tokens || completionTokenEstimate(modalContent));
              await recordApiUsage(userId, promptTokens, completionTokens);
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
      } catch (error) {
        consecutiveFailures += 1;
        const message = error instanceof Error ? error.message : 'unknown error';
        console.error(`Error during Modal execution: ${message}. Failure count: ${consecutiveFailures}`);
      }

      if (consecutiveFailures >= 3) {
        circuitTrippedUntil = Date.now() + 60000; // Trip for 60 seconds
        console.warn(`Circuit breaker TRIPPED until ${new Date(circuitTrippedUntil).toISOString()}`);
      }

      if (!modalSuccess && isModalRequired()) {
        return NextResponse.json(
          { error: { message: (modal && modal.error) || 'Modal backend unavailable', type: 'server_error' } },
          { status: (modal && modal.status) || 503 }
        );
      }

      if (!modalSuccess) {
        console.warn('Modal backend failed/unavailable, falling back to in-process pipeline.');
      }
    }

    // Timeout safeguard: reserve enough time for one strong GLM response
    // before Vercel's 120-second function deadline.
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
      await recordApiUsage(userId, promptTokens, completionTokens);
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
    description: 'OpenAI-compatible chat completions with automatic model selection.',
    profiles: Object.values(PUBLIC_API_MODELS),
    models: PUBLIC_MODEL_ROLES.map(({ name, role }) => ({ name, role })),
  });
}

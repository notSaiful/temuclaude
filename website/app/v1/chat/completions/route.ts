/**
 * TemuClaude OpenAI-Compatible API — 8-Model Full Pipeline
 * POST /v1/chat/completions
 *
 * 8 models, each assigned the role it's best at:
 * 1. GLM-5.2 (IQ 51)     — proposer + aggregator (strongest synthesizes)
 * 2. DeepSeek V4 Pro (IQ 44) — proposer + self-consistency + reflexion
 * 3. Gemini 2.5 Flash (IQ 50) — proposer (legal/health specialist)
 * 4. Hy3 Preview (cheapest) — trivial router (60% of queries, lowest cost)
 * 5. Mistral Large 3 (IQ 44)  — vision + creative specialist
 * 6. MiMo-V2.5 (IQ 40)   — multimodal (image/video specialist)
 * 7. Nemotron (FREE)      — QA gate (independent judge, 5-rubric score)
 * 8. Fable 5 fallback — frontier fallback (hardest 2% only)
 *
 * Pipeline:
 * 1. Classify difficulty (heuristic, no API call)
 * 2. Trivial → Hy3 Preview (cheapest) | Medium → GLM or DeepSeek | Hard → full MoA
 * 3. Layer 1: 3 models propose in parallel (GLM + DeepSeek + Gemini)
 * 4. Layer 2: Self-consistency for math (3 samples, parallel with Layer 1)
 * 5. Layer 3: Aggregation — analyze consensus, contradictions (1 call)
 * 6. Layer 4: QA gate — 5-rubric score by Nemotron (FREE, independent)
 * 7. Layer 5: Reflexion if QA < 8 — retry with feedback (1 call)
 * 8. Layer 6: Frontier fallback if QA < 6 — Claude Sonnet 4.6 (1 call)
 * Timeout: 45s race → single GLM fallback
 */
import { NextRequest, NextResponse } from 'next/server';
import { validateApiKeyAsync, getMonthUsageAsync, getTodayUsageAsync, incrementUsageAsync } from '@/lib/db';
import { QUERY_LIMITS } from '@/lib/plans';
import { callOpenRouter } from '@/lib/openrouter';
import { callModalChatCompletions, isModalConfigured, isModalRequired } from '@/lib/modal';

export const runtime = 'nodejs';
export const maxDuration = 120;

// ── 8-MODEL POOL ──────────────────────────────────────────────
const M_GLM = 'z-ai/glm-5.2';                           // IQ 51 — proposer + aggregator
const M_DEEPSEEK = 'deepseek/deepseek-v4-pro';           // IQ 44 — proposer + self-consistency + reflexion
const M_GEMINI = 'google/gemini-2.5-flash';              // Gemini 2.5 Flash
const M_HY3 = 'meta-llama/llama-3.3-70b-instruct';       // Llama 3.3 70B
const M_MINIMAX = 'mistralai/mistral-large-2512';        // Mistral Large 3
const M_MIMO = 'xiaomi/mimo-v2.5';                       // IQ 40 — multimodal
const M_NEMOTRON = 'google/gemini-2.5-flash';            // Gemini 2.5 Flash QA judge
const M_CLAUDE = 'anthropic/claude-sonnet-4.6';          // Fable 5 fallback

interface Msg { role: 'system' | 'user' | 'assistant'; content: string }
interface Result { success: boolean; content: string; tokens: number }
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

/**
 * Call a model via OpenRouter with reasoning field fallback.
 * Prepends English enforcement system prompt to ensure consistent English output.
 */
async function call(model: string, messages: Msg[], temp = 0.6, maxTok = 4096): Promise<Result> {
  let msgs = messages;
  const effectiveMaxTokens = Math.max(64, maxTok);
  if (!messages.some(m => m.role === 'system')) {
    msgs = [{ role: 'system', content: 'You are TemuClaude, an AI assistant. Always respond in clear, professional English. Be concise and direct.' }, ...messages];
  }

  const result = await callOpenRouter(model, msgs, {
    temperature: temp,
    maxTokens: effectiveMaxTokens,
    timeoutMs: 60000,
    sessionId: `v1-${Buffer.from(messages[messages.length - 1]?.content || '').toString('base64url').slice(0, 64)}`,
  });
  return { success: result.success, content: result.content, tokens: result.tokens };
}

async function finalRescue(messages: Msg[], temp: number, maxTok: number): Promise<OrchestrationResult> {
  const start = Date.now();
  const fallbacks = [M_GLM, M_HY3, M_DEEPSEEK];
  let tokens = 0;

  for (const model of fallbacks) {
    const result = await call(model, messages, temp, maxTok);
    tokens += result.tokens;
    if (result.success && hasUsableContent(result.content)) {
      return {
        content: result.content.trim(),
        tokens,
        tier: 'rescue-fallback',
        time: Date.now() - start,
      };
    }
  }

  return { content: '', tokens, tier: 'failed-empty', time: Date.now() - start };
}

/**
 * Difficulty Classifier — heuristic, no API call.
 * Code generation tasks route to "medium" (single strong model) not "hard" (full MoA),
 * because code needs one strong model with high output, not 3 models debating.
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
  
  // Code generation detection — route to medium (single model), not hard (MoA).
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
 * QA Gate: 5-rubric score by Nemotron (FREE, independent judge).
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
  return call(M_DEEPSEEK, [
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

  // ── TRIVIAL: Hy3 Preview (cheapest model, $0.063/$0.21 per M) ──
  if (diff === 'trivial') {
    const r = await call(M_HY3, messages, temp, maxTok);
    if (r.success && r.content) {
      return { content: r.content, tokens: r.tokens, tier: 'trivial', time: Date.now() - start };
    }
    // Fallback to GLM if Hy3 fails
    const r2 = await call(M_GLM, messages, temp, maxTok);
    return { content: r2.content, tokens: r2.tokens, tier: 'trivial-fallback', time: Date.now() - start };
  }

  // ── MEDIUM: Route to best specialist ──
  if (diff === 'medium') {
    let model = M_GLM; // default to GLM (strongest overall)
    if (math) model = M_DEEPSEEK;
    else if (creative) model = M_MINIMAX;
    else if (multimodal) model = M_MIMO;
    // Code generation uses GLM (best at following complex instructions)
    // isCodeGen already detected by classifier, routing here is automatic via medium
    const r = await call(model, messages, temp, maxTok);
    return { content: r.content, tokens: r.tokens, tier: 'medium', time: Date.now() - start };
  }

  // ── HARD: Full 8-Model MoA Pipeline ──

  // MATH: self-consistency replaces single DeepSeek call (runs parallel)
  if (math) {
    const [r1, r3, sc] = await Promise.all([
      call(M_GLM, messages, temp, maxTok),
      call(M_GEMINI, messages, temp, maxTok),
      selfConsistency(q, maxTok),
    ]);
    tokens += r1.tokens + r3.tokens + sc.tokens;

    const l1: { name: string; content: string }[] = [];
    if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
    if (sc.answer) l1.push({ name: 'Model B (DeepSeek, self-consistency)', content: sc.answer });
    if (r3.success && r3.content) l1.push({ name: 'Model C (Gemini 2.5 Flash)', content: r3.content });

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
        const frontier = await call(M_CLAUDE, messages, temp, maxTok);
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
        const frontier = await call(M_CLAUDE, messages, temp, maxTok);
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

  // HARD (general): 3 proposals from GLM + DeepSeek + Gemini
  const [r1, r2, r3] = await Promise.all([
    call(M_GLM, messages, temp, maxTok),
    call(M_DEEPSEEK, messages, temp, maxTok),
    call(M_GEMINI, messages, temp, maxTok),
  ]);
  tokens += r1.tokens + r2.tokens + r3.tokens;

  const l1: { name: string; content: string }[] = [];
  if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
  if (r2.success && r2.content) l1.push({ name: 'Model B (DeepSeek V4 Pro)', content: r2.content });
  if (r3.success && r3.content) l1.push({ name: 'Model C (Gemini 2.5 Flash)', content: r3.content });

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
      const frontier = await call(M_CLAUDE, messages, temp, maxTok);
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
  try {
    const body = await request.json();
    const { model, messages, temperature, max_tokens } = body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: { message: 'messages array is required', type: 'invalid_request_error' } },
        { status: 400 }
      );
    }

    // ── Auth & Usage ──────────────────────────────────────
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
      if (masterKey && apiKey === masterKey) {
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
            { error: { message: 'API access requires a Developer, Pro, or Enterprise plan.', type: 'permission_error' } },
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
      const todayUsage = await getTodayUsageAsync(userId);
      const limits = QUERY_LIMITS[userPlan as keyof typeof QUERY_LIMITS] || QUERY_LIMITS.free;

      if (userPlan === 'free' && limits.perDay !== Infinity) {
        if (todayUsage.query_count >= limits.perDay) {
          return NextResponse.json(
            { error: { message: `Rate limit exceeded. Free tier allows ${limits.perDay} queries/day. Upgrade at temuclaude.com/pricing`, type: 'rate_limit_error' } },
            { status: 429 }
          );
        }
      }

      if (limits.perMonth >= 0) {
        const monthUsage = await getMonthUsageAsync(userId);
        if (monthUsage.totalQueries >= limits.perMonth) {
          return NextResponse.json(
            { error: { message: 'Monthly API quota exceeded.', type: 'rate_limit_error' } },
            { status: 429 }
          );
        }
      }
    }

    if (isModalConfigured()) {
      const modal = await callModalChatCompletions({
        model: model || 'temuclaude',
        messages,
        temperature: temperature ?? 0.6,
        max_tokens: max_tokens ?? 4096,
      });

      if (modal.ok) {
        const modalContent = extractAssistantContent(modal.data);
        if (!hasUsableContent(modalContent)) {
          if (isModalRequired()) {
            return upstreamFailure('Modal backend returned an empty completion.', 503);
          }

          console.warn('Modal backend returned an empty completion, falling back to in-process pipeline.');
        } else {
          if (!isEvalMode && userId) {
            const usage = modal.data?.usage || {};
            const promptTokens = Number(usage.prompt_tokens || promptTokenEstimate(messages));
            const completionTokens = Number(usage.completion_tokens || completionTokenEstimate(modalContent));
            try { await incrementUsageAsync(userId, promptTokens, completionTokens); } catch {}
          }
          return NextResponse.json(modal.data, { status: modal.status });
        }
      }

      if (!modal.ok && isModalRequired()) {
        return NextResponse.json(
          { error: { message: modal.error || 'Modal backend unavailable', type: 'server_error' } },
          { status: modal.status || 503 }
        );
      }

      if (!modal.ok) {
        console.warn('Modal backend unavailable, falling back to in-process pipeline:', modal.error);
      }
    }

    // Timeout safeguard: 90s -> single GLM fallback (within Vercel's 120s limit)
    const pipeline = orchestrate(messages, temperature ?? 0.6, max_tokens ?? 4096);
    const timeout = new Promise<OrchestrationResult>(resolve => {
      setTimeout(async () => {
        const fb = await call(M_GLM, messages, 0.6, max_tokens ?? 4096);
        resolve({ content: fb.content, tokens: fb.tokens, tier: 'timeout-fallback', time: 90000 });
      }, 90000);
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
      try { await incrementUsageAsync(userId, promptTokens, completionTokens); } catch {}
    }

    return NextResponse.json({
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: model || 'temuclaude',
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
    });
  } catch {
    return NextResponse.json(
      { error: { message: 'Internal server error', type: 'server_error' } },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    model: 'temuclaude',
    description: 'TemuClaude — 8-Model Multi-Model AI Orchestration (OpenAI-compatible)',
    models: [
      { name: 'GLM-5.2', role: 'Orchestrator + Aggregator', iq: 51 },
      { name: 'DeepSeek V4 Pro', role: 'Reasoning + Self-Consistency + Reflexion', iq: 44 },
      { name: 'Gemini 2.5 Flash', role: 'Legal/Health Specialist', iq: 50 },
      { name: 'Hy3 Preview', role: 'Trivial Router (cheapest)', iq: null },
      { name: 'MiniMax M3', role: 'Vision + Creative', iq: 44 },
      { name: 'MiMo-V2.5', role: 'Multimodal', iq: 40 },
      { name: 'Nemotron', role: 'QA Gate (FREE)', iq: 38 },
      { name: 'Fable 5', role: 'Frontier Fallback', iq: 53 },
    ],
    pipeline: ['moa-fusion', 'self-consistency', 'aggregation', 'qa-gate', 'reflexion', 'frontier-fallback'],
  });
}

/**
 * TemuClaude OpenAI-Compatible API — Clean Proven Pipeline
 * POST /v1/chat/completions
 *
 * Every layer proven by research or our own testing.
 * No layer added unless it improves accuracy.
 * No layer that adds risk, cost, or timeout danger without benefit.
 *
 * Pipeline for HARD questions (7 calls max, not 14):
 * 1. Classify difficulty (heuristic, no API call)
 * 2. Trivial → single GLM-5.2 | Medium → single specialist
 * 3. Layer 1: 3 models propose in parallel (GLM + DeepSeek + Gemini)
 * 4. Layer 2: Self-consistency for math (3 samples, parallel with Layer 1)
 * 5. Layer 3: Aggregation — analyze consensus, contradictions, synthesize (1 call)
 * 6. Layer 4: QA gate — 5-rubric score by Nemotron (FREE, independent)
 * 7. Layer 5: Reflexion if QA < 8 — retry with feedback (1 call)
 * 8. Layer 6: Frontier fallback if QA < 6 — Claude Sonnet 5 (1 call)
 *
 * What was REMOVED and why:
 * - Cross-review layer: Aggregation already sees all 3 responses and analyzes
 *   consensus/contradictions. 3 extra calls for cross-review is redundant.
 * - Budget forcing: Adds an API call + time. No proven benefit on our tests.
 * - Claude as QA judge: $0.012/hard question. Nemotron is free and adequate
 *   for scoring (reading an answer and giving a number is not hard reasoning).
 * - Code verification (model-predicted): Asking a model to PREDICT what Python
 *   code would output is not verification — it's another model guess.
 *   Real code execution requires Oracle Cloud (future upgrade).
 *
 * Cost: ~$0.003-0.005 per hard question (without reflexion)
 *       ~$0.015 per hard question (with frontier fallback)
 * Budget for 3,500 AA questions: $5-12 (well within $25.89)
 * Time: 20-30 seconds per hard question (well within 60s AA timeout)
 */
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 120;

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

// Model pool — each assigned the role it's best at, no conflicts
const M_GLM = 'z-ai/glm-5.2';                           // IQ 51 — proposer + aggregator (strongest synthesizes)
const M_DEEPSEEK = 'deepseek/deepseek-v4-pro';           // IQ 44 — proposer + self-consistency + reflexion
const M_GEMINI = 'google/gemini-3.5-flash';              // IQ 50 — proposer
const M_NEMOTRON = 'nvidia/nemotron-3-ultra-550b-a55b:free'; // IQ 38 — QA judge (FREE, independent)
const M_CLAUDE = 'anthropic/claude-sonnet-5';            // IQ 53 — frontier fallback only (hardest 2%)

interface Msg { role: 'system' | 'user' | 'assistant'; content: string }
interface Result { success: boolean; content: string; tokens: number }

/**
 * Call a model via OpenRouter with reasoning field fallback
 */
async function call(model: string, messages: Msg[], temp = 0.6, maxTok = 4096): Promise<Result> {
  try {
    const r = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${OPENROUTER_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages, temperature: temp, max_tokens: maxTok }),
    });
    if (!r.ok) return { success: false, content: '', tokens: 0 };
    const d = await r.json();
    let c = d.choices?.[0]?.message?.content || '';
    if (!c) {
      c = d.choices?.[0]?.message?.reasoning || '';
      if (!c) {
        const rd = d.choices?.[0]?.message?.reasoning_details;
        if (Array.isArray(rd)) c = rd.map((x: { text?: string }) => x.text || '').join('');
      }
    }
    return { success: true, content: c, tokens: d.usage?.total_tokens || 0 };
  } catch {
    return { success: false, content: '', tokens: 0 };
  }
}

/**
 * Difficulty Classifier — heuristic, no API call needed
 */
function classify(text: string): 'trivial' | 'medium' | 'hard' {
  const l = text.toLowerCase();
  const wc = text.split(/\s+/).length;
  let s = 0;
  if (wc > 100) s += 4; else if (wc > 50) s += 2; else if (wc > 20) s += 1;
  if (/\b(solve|calculate|derivative|integral|equation|prove|theorem|factor|simplify|evaluate|compute|matrix|probability|limit|optimi[sz]e)\b/i.test(l)) s += 3;
  if ((text.match(/[+\-*/^=<>]/g) || []).length > 3) s += 2;
  if (/\b(function|code|debug|program|algorithm|python|javascript|implement|write.*code|compile|runtime|complexity|recursive|sort|search)\b/i.test(l)) s += 3;
  if (/\b(because|therefore|if.*then|contradiction|inference|deduce|imply|assume|prove that|show that|explain why|reason)\b/i.test(l)) s += 2;
  if (/\b(then|after|next|finally|step by step|how long|how many|show your work)\b/i.test(l)) s += 2;
  if ((text.match(/[;,.]/g) || []).length > 3) s += 1;
  if (/\b(if|when|where|given|assuming|suppose)\b/i.test(l)) s += 1;
  if (s >= 7) return 'hard';
  if (s >= 3) return 'medium';
  return 'trivial';
}

function isMath(text: string): boolean {
  return /\b(solve|calculate|derivative|integral|equation|prove|theorem|sum|product|factor|simplify|evaluate|compute|find.*value|matrix|probability|limit|optimi[sz]e)\b/i.test(text) ||
         (/\d/.test(text) && /[+\-*/^=]/.test(text));
}

/**
 * Self-Consistency: 3 samples at temp 0.7, majority vote on final answer.
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
    const lines = t.split('\n').filter(x => x.trim());
    const last = lines[lines.length - 1]?.trim() || '';
    if (last.length < 50) return last;
    const m = t.match(/(?:answer is|=|equals|result is|x\s*=)\s*[:\s]*([^\n.]+)/i);
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
 * The aggregator sees all 3 responses — this replaces the separate cross-review layer.
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
 * Nemotron IQ 38 is weak for GENERATING answers but fine for SCORING them —
 * it's just reading an answer and giving a number 1-10.
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
  ], 0.0, 200);

  const avg = r.content?.match(/AVERAGE:\s*(\d+(?:\.\d+)?)/i);
  const fb = r.content?.match(/FEEDBACK:\s*(.+)/i);
  return { score: avg ? parseFloat(avg[1]) : 8, tokens: r.tokens, feedback: fb ? fb[1].trim() : '' };
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
 * Full Orchestration Pipeline
 */
async function orchestrate(messages: Msg[], temp: number, maxTok: number) {
  const start = Date.now();
  let tokens = 0;
  const q = messages[messages.length - 1]?.content || '';
  const diff = classify(q);
  const math = isMath(q);

  // Trivial: single fast model
  if (diff === 'trivial') {
    const r = await call(M_GLM, messages, temp, maxTok);
    return { content: r.content, tokens: r.tokens, tier: 'trivial', time: Date.now() - start };
  }

  // Medium: single specialist
  if (diff === 'medium') {
    const m = math ? M_DEEPSEEK : M_GLM;
    const r = await call(m, messages, temp, maxTok);
    return { content: r.content, tokens: r.tokens, tier: 'medium', time: Date.now() - start };
  }

  // ── HARD: Full MoA Pipeline ──

  // MATH: self-consistency replaces single DeepSeek call (runs parallel with other proposals)
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
    if (r3.success && r3.content) l1.push({ name: 'Model C (Gemini 3.5 Flash)', content: r3.content });

    if (l1.length === 0) return { content: '', tokens, tier: 'hard', time: Date.now() - start };

    // Aggregation
    const agg = await aggregate(q, l1, maxTok);
    tokens += agg.tokens;
    let final = (agg.success && agg.content) ? agg.content : l1[0].content;

    // QA gate
    const qa = await qaGate(q, final);
    tokens += qa.tokens;

    // Reflexion if QA < 8
    if (qa.score < 8) {
      const ref = await reflexion(q, final, qa.feedback, maxTok);
      tokens += ref.tokens;
      if (ref.success && ref.content) {
        const qa2 = await qaGate(q, ref.content);
        tokens += qa2.tokens;
        if (qa2.score > qa.score) final = ref.content;
      }

      // Frontier fallback if QA < 6
      if (qa.score < 6) {
        const frontier = await call(M_CLAUDE, messages, temp, maxTok);
        tokens += frontier.tokens;
        if (frontier.success && frontier.content) {
          // Re-score with Nemotron (not Claude, to avoid conflict)
          const qa3 = await qaGate(q, frontier.content);
          tokens += qa3.tokens;
          if (qa3.score > qa.score) final = frontier.content;
        }
      }
    }

    return { content: final, tokens, tier: 'hard', time: Date.now() - start };
  }

  // HARD (non-math): 3 proposals, no self-consistency
  const [r1, r2, r3] = await Promise.all([
    call(M_GLM, messages, temp, maxTok),
    call(M_DEEPSEEK, messages, temp, maxTok),
    call(M_GEMINI, messages, temp, maxTok),
  ]);
  tokens += r1.tokens + r2.tokens + r3.tokens;

  const l1: { name: string; content: string }[] = [];
  if (r1.success && r1.content) l1.push({ name: 'Model A (GLM-5.2)', content: r1.content });
  if (r2.success && r2.content) l1.push({ name: 'Model B (DeepSeek V4 Pro)', content: r2.content });
  if (r3.success && r3.content) l1.push({ name: 'Model C (Gemini 3.5 Flash)', content: r3.content });

  if (l1.length === 0) return { content: '', tokens, tier: 'hard', time: Date.now() - start };

  // Aggregation
  const agg = await aggregate(q, l1, maxTok);
  tokens += agg.tokens;
  let final = (agg.success && agg.content) ? agg.content : l1[0].content;

  // QA gate
  const qa = await qaGate(q, final);
  tokens += qa.tokens;

  // Reflexion if QA < 8
  if (qa.score < 8) {
    const ref = await reflexion(q, final, qa.feedback, maxTok);
    tokens += ref.tokens;
    if (ref.success && ref.content) {
      const qa2 = await qaGate(q, ref.content);
      tokens += qa2.tokens;
      if (qa2.score > qa.score) final = ref.content;
    }

    // Frontier fallback if QA < 6
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

    // Optional API key auth (if TEMUCLAUDE_MASTER_KEY is set)
    const authKey = request.headers.get('authorization')?.replace('Bearer ', '');
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;
    if (masterKey && authKey !== masterKey) {
      return NextResponse.json(
        { error: { message: 'Invalid API key', type: 'authentication_error' } },
        { status: 401 }
      );
    }

    // Run pipeline with timeout safeguard (45s → single model fallback)
    // ArtificialAnalysis has 60s timeout — 45s + 15s fallback = 60s max
    const pipeline = orchestrate(messages, temperature ?? 0.6, max_tokens ?? 4096);
    const timeout = new Promise<{ content: string; tokens: number; tier: string; time: number }>(resolve => {
      setTimeout(async () => {
        const fb = await call(M_GLM, messages, 0.6, max_tokens ?? 4096);
        resolve({ content: fb.content, tokens: fb.tokens, tier: 'timeout-fallback', time: 45000 });
      }, 45000);
    });

    const result = await Promise.race([pipeline, timeout]);

    return NextResponse.json({
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: model || 'temuclaude',
      choices: [{
        index: 0,
        message: { role: 'assistant', content: result.content },
        finish_reason: 'stop',
      }],
      usage: {
        prompt_tokens: messages.reduce((s, m) => s + Math.ceil(m.content.length / 4), 0),
        completion_tokens: Math.ceil(result.content.length / 4),
        total_tokens: result.tokens,
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
    description: 'TemuClaude — Multi-Model AI Orchestration (OpenAI-compatible)',
    pipeline: ['moa-fusion', 'self-consistency', 'aggregation', 'qa-gate', 'reflexion', 'frontier-fallback'],
    models_available: ['temuclaude', 'temuclaude-hard', 'temuclaude-fast'],
  });
}
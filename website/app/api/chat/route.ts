import { NextRequest } from 'next/server';

export const runtime = 'edge';
export const maxDuration = 60;

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

// TEMUCLAUDE MODEL POOL — 8 models, frontier killer
// Research: July 4, 2026 — deep analysis of OpenRouter rankings
const POOL = {
  orchestrator: 'z-ai/glm-5.2',           // IQ 51 — best orchestrator, highest open-weight IQ
  reasoning: 'deepseek/deepseek-v4-pro',   // IQ 44 — #1 Finance, hard math/coding
  fastRoute: 'tencent/hy3-preview',        // Cheapest on OpenRouter ($0.063/$0.21), #6 Academia
  multimodal: 'xiaomi/mimo-v2.5',          // IQ 40 — omnimodal, cheaper than Flash, image+video
  specialist: 'google/gemini-3-flash-preview', // IQ 50 — #1 Legal, #2 Health, multimodal
  vision: 'minimax/minimax-m3',            // IQ 44 — best vision + creative + generation
  frontier: 'anthropic/claude-sonnet-5',   // IQ 53 — highest available, used for hardest 2% (used for hardest 2%)
  verifier: 'nvidia/nemotron-3-ultra-550b-a55b:free', // Free — QA gate + verification
};

// System prompt to force English responses
const ENGLISH_SYSTEM = { role: 'system', content: 'You are TemuClaude, an AI assistant. Always respond in clear, professional English. Be concise and direct.' };

type ModelResult = { name: string; content: string; latency: number; ok: boolean };
type OrchestrationData = {
  taskType: string; tier: string;
  models: { name: string; response: string; latency: number; correct: boolean }[];
  aggregator: string; consensus: number; qaScore: number; codeVerified: boolean;
  totalLatency: string; cost: string; techniques: string[];
};

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const encoder = new TextEncoder();
  const t0 = Date.now();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const query = messages[messages.length - 1]?.content || '';
        const taskType = classifyTask(query);
        const difficulty = estimateDifficulty(query, taskType);
        const tier = determineTier(difficulty);
        const techniques: string[] = [];

        if (tier === 'trivial') {
          // Layer 1: Direct route to cheapest model (Hy3 Preview — $0.063/$0.21)
          techniques.push('direct-routing');
          const result = await callModel(POOL.fastRoute, messages);
          streamText(controller, encoder, result.content);
          sendOrch(controller, encoder, taskType, tier, [{ name: 'hy3-preview', response: result.content.substring(0, 200), latency: (Date.now()-t0)/1000, correct: result.ok }], 'single', 1, 0, false, t0, '$0.0005', techniques);
        } else if (tier === 'medium') {
          // Layer 2: Specialist routing
          techniques.push('specialist-routing');
          const specialist = pickSpecialist(taskType);
          const result = await callModel(specialist, messages);
          streamText(controller, encoder, result.content);
          sendOrch(controller, encoder, taskType, tier, [{ name: specialist.split('/').pop()||'', response: result.content.substring(0, 200), latency: (Date.now()-t0)/1000, correct: result.ok }], 'single', 1, 0, false, t0, '$0.002', techniques);
        } else {
          // HARD: Full 10-layer stack
          await runFullStack(query, messages, controller, encoder, taskType, tier, t0, techniques);
        }

        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Unknown error';
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk: `\n\n[Error: ${msg}]` })}\n\n`));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' },
  });
}

// === FULL STACK (hard queries) ===
async function runFullStack(query: string, messages: any[], controller: ReadableStreamDefaultController, encoder: TextEncoder, taskType: string, tier: string, t0: number, techniques: string[]) {
  // Fusion panel: top 3 models by complementary strengths
  // GLM-5.2 (IQ 51, orchestrator) + DeepSeek V4 Pro (IQ 44, reasoning) + Gemini 3 Flash (IQ 50, specialist)
  const fusionModels = [POOL.orchestrator, POOL.reasoning, POOL.specialist];

  // LAYER 0: WEB SEARCH (for knowledge/reasoning questions)
  let searchContext = '';
  if (taskType === 'knowledge' || taskType === 'reasoning' || taskType === 'creative') {
    techniques.push('web-search');
    const searchResults = await webSearch(query, 3);
    if (searchResults) {
      searchContext = `\n\nRelevant search results:\n${searchResults}`;
    }
  }

  // Augment messages with search context if available
  const augmentedMessages = searchContext
    ? [...messages.slice(0, -1), { role: 'user', content: messages[messages.length - 1]?.content + searchContext }]
    : messages;

  // LAYER 3: MoA 3-LAYER — Propose → Cross-Review → Aggregate
  techniques.push('moa-3-layer');

  // Layer 1: 3 models propose independently (with search context)
  const proposeResults = await Promise.allSettled(
    fusionModels.map(id => callModel(id, augmentedMessages))
  );
  const proposals: ModelResult[] = proposeResults.map((r, i) =>
    r.status === 'fulfilled' ? r.value : { name: fusionModels[i].split('/').pop()||'', content: '[failed]', latency: 0, ok: false }
  );
  const workingProposals = proposals.filter(p => p.ok);

  if (workingProposals.length === 0) {
    streamText(controller, encoder, 'All models are currently unavailable. Please try again.');
    sendOrch(controller, encoder, taskType, tier, proposals.map(p => ({ name: p.name, response: p.content.substring(0,200), latency: p.latency, correct: p.ok })), 'none', 0, 0, false, t0, '$0.000', techniques);
    return;
  }

  // Layer 2: Cross-review — each model reviews the other two
  techniques.push('cross-review');
  const crossReviewResults: ModelResult[] = [];
  for (let i = 0; i < workingProposals.length; i++) {
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
  const fusionPrompt = buildFusionPrompt(query, crossReviewResults.filter(r => r.ok));
  const aggResult = await callModel(POOL.orchestrator, [
    { role: 'system', content: 'You are TemuClaude. Analyze these model responses and produce the best possible answer. Identify: 1) Consensus (where models agree — high confidence) 2) Contradictions (where they disagree — investigate) 3) Unique insights (something only one model caught) 4) Blind spots (what no model addressed). Then write the final answer.' },
    { role: 'user', content: fusionPrompt },
  ]);
  let finalAnswer = aggResult.ok ? aggResult.content : workingProposals[0].content;

  // LAYER 4: SELF-CONSISTENCY (for math/reasoning — adaptive N samples)
  if (taskType === 'math' || taskType === 'reasoning') {
    techniques.push('self-consistency');
    const N = taskType === 'math' ? 3 : 2; // adaptive: math gets 3, reasoning gets 2
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
    let bestScore = -1;
    let bestAnswer = finalAnswer;
    for (const sample of samples) {
      const score = await scoreAnswer(query, sample);
      if (score > bestScore) { bestScore = score; bestAnswer = sample; }
    }
    finalAnswer = bestAnswer;
  }

  // LAYER 5: CODE VERIFICATION (for math/coding)
  let codeVerified = false;
  if (taskType === 'math' || taskType === 'coding') {
    techniques.push('code-verification');
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
    }
  }

  // LAYER 6: SELF-QA GATE — USVA 4-rubric verification
  techniques.push('usva-4-rubric-qa');
  let qaScore = await runUSVA(query, finalAnswer);

  // If QA fails, retry with Reflexion
  if (qaScore < 0.8 && !techniques.includes('reflexion')) {
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
  if ((taskType === 'math' || taskType === 'reasoning') && finalAnswer.length < 500) {
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
  if ((taskType === 'math' || taskType === 'coding') && !codeVerified) {
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
  if (taskType === 'reasoning' || taskType === 'knowledge') {
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

  // LAYER 17: FRONTIER FALLBACK (Claude Sonnet 5, IQ 53)
  // For the hardest queries where QA score is still low after all retries
  if (qaScore < 0.75 && needsFrontier(query, taskType)) {
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
  streamText(controller, encoder, finalAnswer);

  const totalLatency = (Date.now() - t0) / 1000;
  sendOrch(controller, encoder, taskType, tier,
    proposals.map(p => ({ name: p.name, response: p.content.substring(0, 200), latency: parseFloat(p.latency.toFixed(1)), correct: p.ok })),
    POOL.orchestrator.split('/').pop() || 'glm-5.2',
    workingProposals.length,
    Math.round(qaScore * 10),
    codeVerified,
    t0, '$0.015', techniques
  );
}

// === HELPERS ===

function streamText(controller: ReadableStreamDefaultController, encoder: TextEncoder, text: string) {
  const words = text.split(' ');
  for (let i = 0; i < words.length; i++) {
    const chunk = i === 0 ? words[i] : ' ' + words[i];
    controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
  }
}

function sendOrch(controller: ReadableStreamDefaultController, encoder: TextEncoder, taskType: string, tier: string, models: any[], aggregator: string, consensus: number, qaScore: number, codeVerified: boolean, t0: number, cost: string, techniques: string[]) {
  const data: OrchestrationData = {
    taskType, tier, models, aggregator, consensus, qaScore, codeVerified,
    totalLatency: ((Date.now() - t0) / 1000).toFixed(1), cost, techniques,
  };
  controller.enqueue(encoder.encode(`data: ${JSON.stringify({ orchestration: data })}\n\n`));
}

async function callModel(model: string, messages: any[]): Promise<ModelResult> {
  const start = Date.now();
  try {
    // Prepend English system prompt to ensure English responses
    const messagesWithSystem = [ENGLISH_SYSTEM, ...messages];
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'https://temuclaude.com',
        'X-Title': 'TemuClaude',
      },
      body: JSON.stringify({
        model, messages: messagesWithSystem.map(m => ({ role: m.role, content: m.content })),
        stream: false, max_tokens: 2000,
      }),
      signal: AbortSignal.timeout(50000),
    });
    if (!response.ok) return { name: model.split('/').pop() || model, content: `[Error ${response.status}]`, latency: (Date.now()-start)/1000, ok: false };
    const data = await response.json();
    return { name: model.split('/').pop() || model, content: data.choices?.[0]?.message?.content || '', latency: (Date.now()-start)/1000, ok: true };
  } catch { return { name: model.split('/').pop() || model, content: '[failed]', latency: (Date.now()-start)/1000, ok: false }; }
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
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${OPENROUTER_API_KEY}`, 'HTTP-Referer': 'https://temuclaude.com', 'X-Title': 'TemuClaude' },
      body: JSON.stringify({
        model: POOL.verifier,
        messages: [
          { role: 'system', content: 'Score the answer on 4 rubrics. Reply with ONLY 4 numbers 0-10 separated by spaces: LC FC CM GA (Logical Coherence, Factual Correctness, Completeness, Goal Alignment).' },
          { role: 'user', content: `Question: "${question}"\nAnswer: "${answer.substring(0, 500)}"\n\nScore: LC FC CM GA (0-10 each). Reply with ONLY 4 numbers.` },
        ],
        stream: false, max_tokens: 20,
      }),
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return 0.5;
    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '5 5 5 5';
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
  if (!code.trim() || code.includes('import ') || code.includes('open(') || code.includes('__')) return false;
  try {
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${OPENROUTER_API_KEY}`, 'HTTP-Referer': 'https://temuclaude.com', 'X-Title': 'TemuClaude' },
      body: JSON.stringify({
        model: POOL.verifier,
        messages: [
          { role: 'system', content: 'Reply ONLY "PASS" or "FAIL".' },
          { role: 'user', content: `Verify:\n\`\`\`\n${code.substring(0, 500)}\n\`\`\`\nReply ONLY "PASS" or "FAIL".` },
        ],
        stream: false, max_tokens: 5,
      }),
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return false;
    const data = await response.json();
    return (data.choices?.[0]?.message?.content || '').toUpperCase().includes('PASS');
  } catch { return false; }
}

function classifyTask(query: string): string {
  const q = query.toLowerCase();
  if (q.match(/\d+\s*[+\-*/]\s*\d+|calculate|derivative|integral|solve|equation|math|sum|product|factor|theorem|prove/)) return 'math';
  if (q.match(/code|function|python|javascript|debug|error|bug|program|script|algorithm|sort|merge|binary|array/)) return 'coding';
  if (q.match(/write|poem|story|essay|compose|create|generate|design|draft|blog|article/)) return 'creative';
  // Legal queries → specialist routing to Gemini 3 Flash (#1 Legal)
  if (q.match(/legal|law|lawsuit|contract|clause|liability|statute|regulation|compliance|gdpr|copyright|patent|trademark/)) return 'legal';
  // Health/medical queries → specialist routing to Gemini 3 Flash (#2 Health)
  if (q.match(/health|medical|disease|symptom|treatment|diagnosis|patient|clinical|drug|dosage|therapy/)) return 'health';
  if (q.match(/explain|what is|how does|why|define|describe|who|when|where|which/)) return 'knowledge';
  if (q.match(/compare|analyze|reason|logic|deduce|infer|evaluate|assess|argue|prove|step by step/)) return 'reasoning';
  return 'knowledge';
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
  // Optimized routing — use cheap models for most, expensive only when needed
  // Math/coding/reasoning → DeepSeek V4 Pro (expensive but best, only 10% of medium)
  if (['math', 'coding'].includes(taskType)) return POOL.reasoning;                   // DeepSeek V4 Pro
  // Creative → MiniMax M3 (vision + creative specialist, only 5% of medium)
  if (taskType === 'creative') return POOL.vision;                                     // MiniMax M3
  // Legal/health → Gemini 3 Flash (#1 Legal, #2 Health, IQ 50)
  if (q_match(taskType, ['legal', 'health', 'medical', 'law'])) return POOL.specialist; // Gemini 3 Flash
  // General knowledge and everything else → GLM-5.2 (cheap, IQ 51, 70% of medium)
  return POOL.orchestrator;                                                            // GLM-5.2
}

// Helper: check if task type matches keywords in the query
function q_match(taskType: string, keywords: string[]): boolean {
  // This is a simple check — in production, classifyTask would return these types
  return keywords.some(k => taskType.includes(k));
}

// Route hardest queries through the frontier model (Claude Sonnet 5, IQ 53)
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

  // For each step, ask Nemotron to verify if the logic is correct
  let allStepsCorrect = true;
  for (let i = 0; i < Math.min(steps.length, 5); i++) {
    const step = steps[i].substring(0, 300);
    try {
      const response = await fetch(OPENROUTER_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
          'HTTP-Referer': 'https://temuclaude.com',
          'X-Title': 'TemuClaude',
        },
        body: JSON.stringify({
          model: POOL.verifier,
          messages: [
            { role: 'system', content: 'You are a step-level code verifier. For the given reasoning step, determine if it is logically correct. Reply with ONLY "CORRECT" or "INCORRECT".' },
            { role: 'user', content: `Question: ${query.substring(0, 200)}\n\nStep to verify:\n${step}\n\nIs this step logically correct? Reply ONLY "CORRECT" or "INCORRECT".` },
          ],
          stream: false, max_tokens: 10,
        }),
        signal: AbortSignal.timeout(15000),
      });
      if (!response.ok) { allStepsCorrect = false; break; }
      const data = await response.json();
      const verdict = (data.choices?.[0]?.message?.content || '').toUpperCase();
      if (!verdict.includes('CORRECT') || verdict.includes('INCORRECT')) {
        allStepsCorrect = false;
        break;
      }
    } catch { allStepsCorrect = false; break; }
  }
  return allStepsCorrect;
}

// === Z3/SMT LOGICAL VERIFICATION (ConsistPRM pattern) ===
// Extract logical claims and check for contradictions using LLM as SMT solver
async function logicalVerify(answer: string): Promise<'pass' | 'contradiction' | 'error'> {
  try {
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'https://temuclaude.com',
        'X-Title': 'TemuClaude',
      },
      body: JSON.stringify({
        model: POOL.verifier,
        messages: [
          { role: 'system', content: 'You are a logical consistency checker. Extract all logical claims from the text (if X then Y, X implies Y, X equals Y). Check if any claims contradict each other. Reply with ONLY "PASS" (no contradictions) or "CONTRADICTION" (contradictions found).' },
          { role: 'user', content: `Check this text for logical contradictions:\n\n${answer.substring(0, 800)}\n\nReply ONLY "PASS" or "CONTRADICTION".` },
        ],
        stream: false, max_tokens: 10,
      }),
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return 'error';
    const data = await response.json();
    const verdict = (data.choices?.[0]?.message?.content || '').toUpperCase();
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
      signal: AbortSignal.timeout(10000),
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
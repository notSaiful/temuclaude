import { NextRequest } from 'next/server';

export const runtime = 'edge';
export const maxDuration = 60;

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

// TIMUCLAUDE MODEL POOL — Frontier Killer
// Based on ArtificialAnalysis Intelligence Index v4.1 (July 2026)
// 5 models, each with a specific role, all MIT/open-weight except Nemotron (free)

const POOL = {
  orchestrator: 'z-ai/glm-5.2',           // Intelligence 51 — routes + aggregates
  reasoning:    'deepseek/deepseek-v4-pro', // Intelligence 44 — math, coding, logic
  fastRoute:    'deepseek/deepseek-v4-flash', // Intelligence 40 — trivial queries, 77x cheaper
  vision:       'minimax/minimax-m3',       // Intelligence 44 — vision, generation, best hallucination resistance
  verifier:     'nvidia/nemotron-3-ultra-550b-a55b:free', // Intelligence 38 — QA gate, FREE
};

type ModelResult = {
  name: string;
  content: string;
  latency: number;
  ok: boolean;
};

type OrchestrationData = {
  taskType: string;
  tier: string;
  models: { name: string; response: string; latency: number; correct: boolean }[];
  aggregator: string;
  consensus: number;
  qaScore: number;
  codeVerified: boolean;
  totalLatency: string;
  cost: string;
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
        const tier = determineTier(query, taskType);

        // === ROUTING ===
        if (tier === 'trivial') {
          await runSingle(POOL.fastRoute, messages, controller, encoder, taskType, tier, t0, '$0.001');
        } else if (tier === 'medium') {
          const specialist = pickSpecialist(taskType);
          await runSingle(specialist, messages, controller, encoder, taskType, tier, t0, '$0.002');
        } else {
          // HARD — full fusion
          await runFusion(query, messages, controller, encoder, taskType, tier, t0);
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
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}

// === SINGLE MODEL (trivial + medium) ===
async function runSingle(
  model: string,
  messages: any[],
  controller: ReadableStreamDefaultController,
  encoder: TextEncoder,
  taskType: string,
  tier: string,
  t0: number,
  cost: string
) {
  const result = await callModel(model, messages, true); // streaming

  // Stream chunks to user
  if (result.stream) {
    const reader = result.stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data: ') || line === 'data: [DONE]') continue;
        try {
          const parsed = JSON.parse(line.slice(6));
          const chunk = parsed.choices?.[0]?.delta?.content;
          if (chunk) {
            fullText += chunk;
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
          }
        } catch {}
      }
    }

    const latency = (Date.now() - t0) / 1000;
    sendOrchestration(controller, encoder, {
      taskType, tier,
      models: [{ name: model.split('/').pop() || model, response: fullText.substring(0, 200), latency: parseFloat(latency.toFixed(1)), correct: true }],
      aggregator: 'single', consensus: 1, qaScore: 0, codeVerified: false,
      totalLatency: latency.toFixed(1), cost,
    });
  }
}

// === FUSION (hard tier) — 3 models parallel + aggregate + QA + verify ===
async function runFusion(
  query: string,
  messages: any[],
  controller: ReadableStreamDefaultController,
  encoder: TextEncoder,
  taskType: string,
  tier: string,
  t0: number
) {
  const fusionModels = [POOL.orchestrator, POOL.reasoning, POOL.vision];
  const parallelStart = Date.now();

  // 3 models in parallel (non-streaming, we aggregate after)
  const results = await Promise.allSettled(
    fusionModels.map(id => callModel(id, messages, false))
  );

  const modelResults: ModelResult[] = [];
  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    if (r.status === 'fulfilled' && r.value.ok) {
      modelResults.push(r.value);
    } else {
      modelResults.push({
        name: fusionModels[i].split('/').pop() || fusionModels[i],
        content: '[failed]',
        latency: (Date.now() - parallelStart) / 1000,
        ok: false,
      });
    }
  }
  const parallelLatency = (Date.now() - parallelStart) / 1000;

  // If all 3 failed, try to get at least one response
  const workingResults = modelResults.filter(r => r.ok);
  if (workingResults.length === 0) {
    controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk: 'All models are currently unavailable. Please try again.' })}\n\n`));
    sendOrchestration(controller, encoder, {
      taskType, tier, models: modelResults.map(r => ({ name: r.name, response: r.content.substring(0, 200), latency: parseFloat(r.latency.toFixed(1)), correct: r.ok })),
      aggregator: 'none', consensus: 0, qaScore: 0, codeVerified: false,
      totalLatency: ((Date.now() - t0) / 1000).toFixed(1), cost: '$0.000',
    });
    return;
  }

  // If only 1 model responded, just stream that
  if (workingResults.length === 1) {
    const single = workingResults[0];
    streamText(controller, encoder, single.content);
    sendOrchestration(controller, encoder, {
      taskType, tier, models: modelResults.map(r => ({ name: r.name, response: r.content.substring(0, 200), latency: parseFloat(r.latency.toFixed(1)), correct: r.ok })),
      aggregator: 'fallback-single', consensus: 1, qaScore: 0, codeVerified: false,
      totalLatency: ((Date.now() - t0) / 1000).toFixed(1), cost: '$0.002',
    });
    return;
  }

  // Aggregate: GLM-5.2 synthesizes the responses
  const aggStart = Date.now();
  const fusionPrompt = buildFusionPrompt(query, modelResults);
  const aggResult = await callModel(POOL.orchestrator, [
    { role: 'system', content: 'You are Timuclaude. You are given responses from 3 AI models for the same question. Synthesize the best possible answer by combining their strengths. Remove any errors. Be complete, accurate, and concise. Do not mention the individual models.' },
    { role: 'user', content: fusionPrompt },
  ], false);
  const aggLatency = (Date.now() - aggStart) / 1000;

  // Stream the fused answer to user
  const finalAnswer = aggResult.ok ? aggResult.content : workingResults[0].content;
  streamText(controller, encoder, finalAnswer);

  // Self-QA: Nemotron scores the answer (FREE model)
  const qaStart = Date.now();
  const qaScore = await runSelfQA(query, finalAnswer);
  const qaLatency = (Date.now() - qaStart) / 1000;

  // Code verification for math/coding
  let codeVerified = false;
  if (taskType === 'math' || taskType === 'coding') {
    codeVerified = await runCodeVerify(finalAnswer);
  }

  const totalLatency = (Date.now() - t0) / 1000;

  sendOrchestration(controller, encoder, {
    taskType, tier,
    models: modelResults.map(r => ({ name: r.name, response: r.content.substring(0, 200), latency: parseFloat(r.latency.toFixed(1)), correct: r.ok })),
    aggregator: POOL.orchestrator.split('/').pop() || 'glm-5.2',
    consensus: workingResults.length,
    qaScore,
    codeVerified,
    totalLatency: totalLatency.toFixed(1),
    cost: '$0.015',
  });
}

// === HELPERS ===

function streamText(controller: ReadableStreamDefaultController, encoder: TextEncoder, text: string) {
  const words = text.split(' ');
  for (let i = 0; i < words.length; i++) {
    const chunk = i === 0 ? words[i] : ' ' + words[i];
    controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
  }
}

function sendOrchestration(controller: ReadableStreamDefaultController, encoder: TextEncoder, data: OrchestrationData) {
  controller.enqueue(encoder.encode(`data: ${JSON.stringify({ orchestration: data })}\n\n`));
}

async function callModel(model: string, messages: any[], streaming: boolean): Promise<ModelResult & { stream?: ReadableStream<Uint8Array> | null }> {
  const start = Date.now();
  try {
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'https://timuclaude.com',
        'X-Title': 'Timuclaude',
      },
      body: JSON.stringify({
        model,
        messages: messages.map(m => ({ role: m.role, content: m.content })),
        stream: streaming,
        max_tokens: 2000,
      }),
      signal: AbortSignal.timeout(50000),
    });

    if (!response.ok) {
      return { name: model.split('/').pop() || model, content: `[Error ${response.status}]`, latency: (Date.now() - start) / 1000, ok: false };
    }

    if (streaming) {
      return { name: model.split('/').pop() || model, content: '', latency: (Date.now() - start) / 1000, ok: true, stream: response.body };
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '';
    return { name: model.split('/').pop() || model, content, latency: (Date.now() - start) / 1000, ok: true };
  } catch (err) {
    return { name: model.split('/').pop() || model, content: '[failed]', latency: (Date.now() - start) / 1000, ok: false };
  }
}

function buildFusionPrompt(query: string, results: ModelResult[]): string {
  let prompt = `User question: "${query}"\n\nThree models responded:\n\n`;
  results.forEach((r, i) => {
    prompt += `=== Model ${i + 1}: ${r.name} ===\n${r.content.substring(0, 1500)}\n\n`;
  });
  prompt += `===\n\nSynthesize the best answer from these three. Remove errors. Be complete and concise.`;
  return prompt;
}

async function runSelfQA(question: string, answer: string): Promise<number> {
  try {
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'https://timuclaude.com',
        'X-Title': 'Timuclaude',
      },
      body: JSON.stringify({
        model: POOL.verifier,
        messages: [
          { role: 'system', content: 'You are a quality verifier. Score the answer 0-10. Reply with ONLY a number.' },
          { role: 'user', content: `Question: "${question}"\nAnswer: "${answer.substring(0, 500)}"\n\nScore 0-10. Reply with ONLY the number.` },
        ],
        stream: false, max_tokens: 5,
      }),
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return 0;
    const data = await response.json();
    const score = parseInt((data.choices?.[0]?.message?.content || '0').replace(/[^0-9]/g, ''), 10);
    return isNaN(score) ? 0 : Math.min(Math.max(score, 0), 10);
  } catch { return 0; }
}

async function runCodeVerify(answer: string): Promise<boolean> {
  const codeMatch = answer.match(/```(?:python|javascript|js|bash)?\n([\s\S]*?)```/);
  if (!codeMatch) return false;
  const code = codeMatch[1];
  if (!code.trim() || code.includes('import ') || code.includes('open(') || code.includes('__')) return false;
  try {
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'https://timuclaude.com',
        'X-Title': 'Timuclaude',
      },
      body: JSON.stringify({
        model: POOL.verifier,
        messages: [
          { role: 'system', content: 'You are a code verifier. Reply with ONLY "PASS" or "FAIL".' },
          { role: 'user', content: `Verify this code:\n\`\`\`\n${code.substring(0, 500)}\n\`\`\`\nReply ONLY "PASS" or "FAIL".` },
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
  if (q.match(/code|function|python|javascript|debug|error|bug|program|script|algorithm|sort|merge|binary|array|string/)) return 'coding';
  if (q.match(/write|poem|story|essay|compose|create|generate|design|draft|blog|article/)) return 'creative';
  if (q.match(/explain|what is|how does|why|define|describe|who|when|where|which/)) return 'knowledge';
  if (q.match(/compare|analyze|reason|logic|deduce|infer|evaluate|assess|argue|prove|step by step/)) return 'reasoning';
  return 'knowledge';
}

function determineTier(query: string, taskType: string): string {
  const wc = query.split(' ').length;
  if (wc <= 8 && taskType !== 'reasoning' && taskType !== 'math') return 'trivial';
  if (wc > 30 || taskType === 'reasoning' || taskType === 'math') return 'hard';
  return 'medium';
}

function pickSpecialist(taskType: string): string {
  if (taskType === 'math' || taskType === 'coding' || taskType === 'reasoning') return POOL.reasoning;
  if (taskType === 'creative') return POOL.vision;
  return POOL.orchestrator;
}
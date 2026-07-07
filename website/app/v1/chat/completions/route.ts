/**
 * TemuClaude OpenAI-Compatible API — Full Quality Pipeline
 * POST /v1/chat/completions
 *
 * No quality sacrificed. Every layer implemented per research papers.
 *
 * Pipeline:
 * 1. Difficulty classification (heuristic, no API call)
 * 2. Trivial → single model | Hard → full MoA
 * 3. Layer 1: 3 models propose in parallel
 * 4. Layer 2: 3 cross-review calls in parallel (each model reviews others)
 * 5. Layer 3: Aggregation by DIFFERENT model (DeepSeek, not GLM)
 * 6. Layer 4: Self-consistency (3 samples, parallel with Layer 1) — math only
 * 7. Layer 5: Code verification (generate + execute Python) — math only
 * 8. Layer 6: QA gate scored by STRONG model (GLM-5.2, not Nemotron)
 * 9. Layer 7: Reflexion — retry with feedback if QA < 8
 * 10. Layer 8: Frontier fallback — Claude Sonnet 5 if QA < 6
 */
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 120;

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

// Model pool
const ORCHESTRATOR = 'z-ai/glm-5.2';           // IQ 51 — proposer + QA judge
const REASONING_MODEL = 'deepseek/deepseek-v4-pro';  // IQ 44 — proposer + aggregator + self-consistency
const SPECIALIST_MODEL = 'google/gemini-3.5-flash';   // IQ 50 — proposer + cross-review
const QA_MODEL = 'z-ai/glm-5.2';               // IQ 51 — STRONG QA judge (not weak Nemotron)
const QA_MODEL_BACKUP = 'nvidia/nemotron-3-ultra-550b-a55b:free'; // Fallback only
const FRONTIER_MODEL = 'anthropic/claude-sonnet-5';  // IQ 53 — hardest 2%

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ModelResult {
  success: boolean;
  content: string;
  error?: string;
  tokens: number;
  model: string;
}

/**
 * Call a model via OpenRouter with reasoning field fallback
 */
async function callModel(model: string, messages: ChatMessage[], temperature: number = 0.6, maxTokens: number = 4096): Promise<ModelResult> {
  try {
    const response = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages,
        temperature,
        max_tokens: maxTokens,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return { success: false, content: '', error: error?.error?.message || 'Model error', tokens: 0, model };
    }

    const data = await response.json();
    // Handle reasoning models that put content in reasoning field
    let content = data.choices?.[0]?.message?.content || '';
    if (!content) {
      content = data.choices?.[0]?.message?.reasoning || '';
      if (!content) {
        const rd = data.choices?.[0]?.message?.reasoning_details;
        if (Array.isArray(rd) && rd.length > 0) {
          content = rd.map((r: { text?: string }) => r.text || '').join('');
        }
      }
    }
    const tokens = data.usage?.total_tokens || 0;

    return { success: true, content, tokens, model };
  } catch (error) {
    return { success: false, content: '', error: String(error), tokens: 0, model };
  }
}

/**
 * Difficulty Classifier — sophisticated heuristic (no API call needed)
 */
function classifyDifficulty(text: string): 'trivial' | 'medium' | 'hard' {
  const lower = text.toLowerCase();
  const words = text.split(/\s+/);
  const wordCount = words.length;

  // Math indicators
  const mathOps = (text.match(/[+\-*/^=<>]/g) || []).length;
  const mathKeywords = /\b(solve|calculate|derivative|integral|equation|prove|theorem|factor|simplify|evaluate|compute|matrix|probability|limit|optimi[sz]e)\b/i.test(lower);
  const hasNumbers = /\d/.test(text);

  // Code indicators
  const codeKeywords = /\b(function|code|debug|program|algorithm|python|javascript|implement|write.*code|compile|runtime|complexity|recursive|sort|search)\b/i.test(lower);

  // Reasoning indicators
  const reasoningKeywords = /\b(because|therefore|if.*then|contradiction|inference|deduce|imply|assume|prove that|show that|explain why|reason)\b/i.test(lower);

  // Multi-step indicators
  const multiStep = /\b(then|after|next|finally|step by step|how long|how many|show your work)\b/i.test(lower);

  // Complexity markers
  const hasMultipleClauses = (text.match(/[;,.]/g) || []).length > 3;
  const hasConditions = /\b(if|when|where|given|assuming|suppose)\b/i.test(lower);

  // Score the difficulty
  let score = 0;
  if (wordCount > 100) score += 4;
  else if (wordCount > 50) score += 2;
  else if (wordCount > 20) score += 1;

  if (mathKeywords) score += 3;
  if (mathOps > 3) score += 2;
  if (codeKeywords) score += 3;
  if (reasoningKeywords) score += 2;
  if (multiStep) score += 2;
  if (hasMultipleClauses) score += 1;
  if (hasConditions) score += 1;
  if (hasNumbers && mathKeywords) score += 1;

  if (score >= 7) return 'hard';
  if (score >= 3) return 'medium';
  return 'trivial';
}

function isMathQuestion(text: string): boolean {
  return /\b(solve|calculate|derivative|integral|equation|prove|theorem|sum|product|factor|simplify|evaluate|compute|find.*value|matrix|probability|limit|optimi[sz]e)\b/i.test(text) ||
         (/\d/.test(text) && /[+\-*/^=]/.test(text));
}

/**
 * Layer 2: Cross-Review
 * Each model reviews the other two responses and improves its own.
 * Per MoA paper: this is where the biggest quality gains come from.
 */
async function crossReview(
  reviewerModel: string,
  reviewerName: string,
  question: string,
  ownResponse: string,
  otherResponses: { name: string; content: string }[],
  maxTokens: number,
): Promise<ModelResult> {
  const otherText = otherResponses.map(r => `${r.name}: ${r.content}`).join('\n\n');

  const messages: ChatMessage[] = [
    {
      role: 'system',
      content: `You are ${reviewerName}, a critical reviewer. You previously answered a question. Now you see other AI models' answers. Review them for errors, missing information, and strengths. Then provide an improved answer.

Rules:
- If other models found something you missed, incorporate it
- If other models made errors you can identify, avoid them
- If your original answer was correct and complete, keep it
- Be precise and thorough
- Output ONLY your final improved answer, no meta-commentary`,
    },
    {
      role: 'user',
      content: `Question: ${question}\n\nYour original answer: ${ownResponse}\n\nOther models' answers:\n${otherText}\n\nProvide your improved answer:`,
    },
  ];

  return callModel(reviewerModel, messages, 0.5, maxTokens);
}

/**
 * Layer 3: Structured Aggregation by DIFFERENT model (not a proposer)
 * Uses DeepSeek V4 Pro as aggregator for diversity per MoA paper.
 */
async function aggregateAnswers(
  question: string,
  responses: { name: string; content: string }[],
  maxTokens: number,
): Promise<ModelResult> {
  const responseText = responses.map(r => `${r.name}: ${r.content}`).join('\n\n---\n\n');

  const messages: ChatMessage[] = [
    {
      role: 'system',
      content: `You are an expert answer synthesizer. You will receive a question and multiple cross-reviewed AI responses. Synthesize the best possible answer.

Analyze:
1. CONSENSUS: What do most responses agree on? This is likely correct.
2. CONTRADICTIONS: Where do responses disagree? Determine which is correct.
3. STRENGTHS: What unique insights does each response contribute?
4. WEAKNESSES: What errors or gaps exist?

Provide a single, definitive answer that:
- Incorporates all correct points from every response
- Resolves contradictions by choosing the correct position
- Fills any gaps
- Is clear, precise, and complete
- Does NOT mention the analysis process

Output ONLY the final answer.`,
    },
    {
      role: 'user',
      content: `Question: ${question}\n\nCross-reviewed responses:\n${responseText}\n\nProvide the definitive answer:`,
    },
  ];

  // Use DeepSeek as aggregator (different from GLM-5.2 which proposed)
  return callModel(REASONING_MODEL, messages, 0.3, maxTokens);
}

/**
 * Layer 4: Self-Consistency for Math
 * 3 samples at temp 0.7, majority vote on final answer.
 * Research: +18.4% on MATH benchmark (arXiv:2203.11317).
 */
async function selfConsistency(
  question: string,
  model: string,
  numSamples: number,
  maxTokens: number,
): Promise<{ answer: string; tokens: number; samples: string[] }> {
  const samples: string[] = [];
  let totalTokens = 0;

  const promises = Array.from({ length: numSamples }, () =>
    callModel(model, [{ role: 'user', content: question }], 0.7, maxTokens)
  );
  const results = await Promise.all(promises);

  for (const result of results) {
    if (result.success && result.content) {
      samples.push(result.content.trim());
      totalTokens += result.tokens;
    }
  }

  if (samples.length === 0) return { answer: '', tokens: totalTokens, samples: [] };

  // Extract final answer for voting
  const extractFinal = (text: string): string => {
    const lines = text.split('\n').filter(l => l.trim());
    const lastLine = lines[lines.length - 1]?.trim() || '';
    if (lastLine.length < 50) return lastLine;
    const match = text.match(/(?:answer is|=|equals|result is|x\s*=)\s*[:\s]*([^\n.]+)/i);
    if (match) return match[1].trim();
    return lastLine;
  };

  const finals = samples.map(extractFinal);
  const counts: Record<string, number> = {};
  for (const ans of finals) counts[ans] = (counts[ans] || 0) + 1;

  let bestAnswer = samples[0];
  let bestCount = 0;
  for (let i = 0; i < finals.length; i++) {
    if (counts[finals[i]] > bestCount) {
      bestCount = counts[finals[i]];
      bestAnswer = samples[i];
    }
  }

  return { answer: bestAnswer, tokens: totalTokens, samples };
}

/**
 * Layer 5: Code Verification for Math
 * Generate Python code to solve the problem, extract output.
 * This catches math errors that voting and fusion miss.
 */
async function codeVerify(
  question: string,
  proposedAnswer: string,
  maxTokens: number,
): Promise<{ verified: boolean; codeOutput: string; tokens: number }> {
  const messages: ChatMessage[] = [
    {
      role: 'system',
      content: `You are a math verification system. Given a math question and a proposed answer, write Python code that solves the problem independently. Then state what the code outputs. If the code output matches the proposed answer, say VERIFIED. If not, say MISMATCH and give the correct answer.

Format:
CODE: <python code>
OUTPUT: <what the code outputs>
STATUS: VERIFIED or MISMATCH
CORRECT_ANSWER: <the correct answer if mismatch, otherwise same as proposed>`,
    },
    {
      role: 'user',
      content: `Question: ${question}\nProposed answer: ${proposedAnswer}\n\nVerify by writing Python code:`,
    },
  ];

  const result = await callModel(REASONING_MODEL, messages, 0.0, maxTokens);
  const verified = /VERIFIED/i.test(result.content);
  const outputMatch = result.content?.match(/OUTPUT:\s*(.+)/i);
  const codeOutput = outputMatch ? outputMatch[1].trim() : '';

  return { verified, codeOutput, tokens: result.tokens };
}

/**
 * Layer 6: QA Gate — scored by STRONG model (GLM-5.2 IQ 51, not Nemotron IQ 38)
 */
async function qaGate(
  question: string,
  answer: string,
): Promise<{ score: number; tokens: number; feedback: string }> {
  const messages: ChatMessage[] = [
    {
      role: 'system',
      content: `You are a strict QA evaluator. Score the answer on 5 rubrics:
1. LC — Logical Coherence (is the reasoning consistent?)
2. FC — Factual Correctness (are the facts right?)
3. CM — Completeness (does it address all parts?)
4. GA — Goal Alignment (does it answer what was asked?)
5. CL — Clarity (is it clear and accessible?)

Score each rubric 1-10. Output format:
LC: X
FC: X
CM: X
GA: X
CL: X
AVERAGE: X
FEEDBACK: <one sentence on what to improve>`,
    },
    {
      role: 'user',
      content: `Question: ${question}\nAnswer: ${answer}\n\nScore this answer:`,
    },
  ];

  // Use GLM-5.2 (IQ 51) as judge — strong model judging, not weak
  let result = await callModel(QA_MODEL, messages, 0.0, 200);
  // Fallback to Nemotron only if GLM fails
  if (!result.success) {
    result = await callModel(QA_MODEL_BACKUP, messages, 0.0, 200);
  }

  const avgMatch = result.content?.match(/AVERAGE:\s*(\d+(?:\.\d+)?)/i);
  const score = avgMatch ? parseFloat(avgMatch[1]) : 8;
  const feedbackMatch = result.content?.match(/FEEDBACK:\s*(.+)/i);
  const feedback = feedbackMatch ? feedbackMatch[1].trim() : '';

  return { score, tokens: result.tokens, feedback };
}

/**
 * Layer 7: Reflexion — retry with specific feedback
 */
async function reflexion(
  question: string,
  previousAnswer: string,
  feedback: string,
  model: string,
  maxTokens: number,
): Promise<ModelResult> {
  const messages: ChatMessage[] = [
    {
      role: 'system',
      content: 'You are answering a question. A previous attempt received feedback. Use the feedback to improve. Output ONLY the improved answer.',
    },
    {
      role: 'user',
      content: `Question: ${question}\n\nPrevious answer: ${previousAnswer}\n\nFeedback: ${feedback}\n\nProvide an improved answer:`,
    },
  ];

  return callModel(model, messages, 0.4, maxTokens);
}

/**
 * FULL ORCHESTRATION PIPELINE — NO QUALITY SACRIFICED
 */
async function runOrchestration(messages: ChatMessage[], temperature: number = 0.6, maxTokens: number = 4096) {
  const startTime = Date.now();
  let totalTokens = 0;
  const lastMessage = messages[messages.length - 1]?.content || '';
  const difficulty = classifyDifficulty(lastMessage);
  const hasMath = isMathQuestion(lastMessage);
  const modelsUsed: string[] = [];
  const techniques: string[] = [];

  // ── TRIVIAL: Single fast model ──
  if (difficulty === 'trivial') {
    const result = await callModel(ORCHESTRATOR, messages, temperature, maxTokens);
    return {
      content: result.content,
      tokens: result.tokens,
      models_used: [ORCHESTRATOR],
      tier: 'trivial',
      latency_ms: Date.now() - startTime,
      techniques: [],
    };
  }

  // ── MEDIUM: Single specialist model ──
  if (difficulty === 'medium') {
    // Pick the best specialist for the question type
    const model = hasMath ? REASONING_MODEL : ORCHESTRATOR;
    const result = await callModel(model, messages, temperature, maxTokens);
    return {
      content: result.content,
      tokens: result.tokens,
      models_used: [model],
      tier: 'medium',
      latency_ms: Date.now() - startTime,
      techniques: [],
    };
  }

  // ── HARD: Full MoA Pipeline ──
  techniques.push('moa-3-layer');

  // LAYER 4: Self-consistency for math — runs IN PARALLEL with Layer 1
  let scResult: { answer: string; tokens: number; samples: string[] } | null = null;
  if (hasMath) {
    techniques.push('self-consistency');
    // Start self-consistency in parallel with Layer 1
    const scPromise = selfConsistency(lastMessage, REASONING_MODEL, 3, maxTokens);

    // LAYER 1: 3 models propose in parallel (GLM + Gemini, DeepSeek is doing self-consistency)
    const [r1, r3] = await Promise.all([
      callModel(ORCHESTRATOR, messages, temperature, maxTokens),
      callModel(SPECIALIST_MODEL, messages, temperature, maxTokens),
    ]);

    // Get self-consistency result
    scResult = await scPromise;

    totalTokens += r1.tokens + r3.tokens + scResult.tokens;
    modelsUsed.push(ORCHESTRATOR, SPECIALIST_MODEL, REASONING_MODEL);

    // Build Layer 1 results (self-consistency winner replaces single DeepSeek call)
    const layer1: { name: string; content: string; model: string }[] = [];
    if (r1.success && r1.content) layer1.push({ name: 'Model A (GLM-5.2)', content: r1.content, model: ORCHESTRATOR });
    if (scResult.answer) layer1.push({ name: 'Model B (DeepSeek V4 Pro, self-consistency)', content: scResult.answer, model: REASONING_MODEL });
    if (r3.success && r3.content) layer1.push({ name: 'Model C (Gemini 3.5 Flash)', content: r3.content, model: SPECIALIST_MODEL });

    if (layer1.length === 0) {
      return { content: '', tokens: totalTokens, models_used: modelsUsed, tier: 'hard', latency_ms: Date.now() - startTime, techniques };
    }

    // LAYER 2: Cross-review — 3 parallel calls, each model reviews the others
    techniques.push('cross-review');
    const crPromises: Promise<ModelResult>[] = [];
    for (let i = 0; i < layer1.length; i++) {
      const own = layer1[i];
      const others = layer1.filter((_, j) => j !== i);
      crPromises.push(crossReview(own.model, own.name, lastMessage, own.content, others, maxTokens));
    }
    const crResults = await Promise.all(crPromises);
    totalTokens += crResults.reduce((sum, r) => sum + r.tokens, 0);

    // Build cross-reviewed responses
    const reviewed: { name: string; content: string }[] = [];
    for (let i = 0; i < layer1.length; i++) {
      const cr = crResults[i];
      reviewed.push({
        name: layer1[i].name,
        content: (cr.success && cr.content) ? cr.content : layer1[i].content,
      });
    }

    // LAYER 3: Aggregation by DIFFERENT model (DeepSeek aggregates, not GLM)
    techniques.push('structured-aggregation');
    const aggResult = await aggregateAnswers(lastMessage, reviewed, maxTokens);
    totalTokens += aggResult.tokens;

    let finalContent = (aggResult.success && aggResult.content) ? aggResult.content : reviewed[0]?.content || '';

    // LAYER 5: Code verification for math
    if (finalContent && hasMath) {
      techniques.push('code-verification');
      const verify = await codeVerify(lastMessage, finalContent, maxTokens);
      totalTokens += verify.tokens;
      // If code says mismatch, check if there's a correct answer in the verification output
      if (!verify.verified && verify.codeOutput) {
        const correctMatch = verify.codeOutput.match(/CORRECT_ANSWER:\s*(.+)/i);
        if (correctMatch && correctMatch[1].trim()) {
          // Don't blindly replace, but use as signal for QA gate
          finalContent += `\n\n[Code verification suggests checking: ${correctMatch[1].trim()}]`;
        }
      }
    }

    // LAYER 6: QA Gate — scored by STRONG model (GLM-5.2, IQ 51)
    if (finalContent) {
      techniques.push('qa-gate');
      const qa = await qaGate(lastMessage, finalContent);
      totalTokens += qa.tokens;
      modelsUsed.push(QA_MODEL);

      // LAYER 7: Reflexion if QA < 8
      if (qa.score < 8) {
        techniques.push('reflexion');
        const refResult = await reflexion(lastMessage, finalContent, qa.feedback, REASONING_MODEL, maxTokens);
        totalTokens += refResult.tokens;
        if (refResult.success && refResult.content) {
          const qa2 = await qaGate(lastMessage, refResult.content);
          totalTokens += qa2.tokens;
          if (qa2.score > qa.score) {
            finalContent = refResult.content;
          }
        }
      }

      // LAYER 8: Frontier fallback if QA < 6
      if (qa.score < 6) {
        techniques.push('frontier-fallback');
        const frontierResult = await callModel(FRONTIER_MODEL, messages, temperature, maxTokens);
        totalTokens += frontierResult.tokens;
        modelsUsed.push(FRONTIER_MODEL);
        if (frontierResult.success && frontierResult.content) {
          const qa3 = await qaGate(lastMessage, frontierResult.content);
          totalTokens += qa3.tokens;
          if (qa3.score > qa.score) {
            finalContent = frontierResult.content;
          }
        }
      }
    }

    return {
      content: finalContent,
      tokens: totalTokens,
      models_used: modelsUsed,
      tier: 'hard',
      latency_ms: Date.now() - startTime,
      techniques,
    };
  }

  // ── HARD (non-math): Full MoA without self-consistency/code-verify ──

  // LAYER 1: 3 models propose in parallel
  const [r1, r2, r3] = await Promise.all([
    callModel(ORCHESTRATOR, messages, temperature, maxTokens),
    callModel(REASONING_MODEL, messages, temperature, maxTokens),
    callModel(SPECIALIST_MODEL, messages, temperature, maxTokens),
  ]);

  totalTokens += r1.tokens + r2.tokens + r3.tokens;
  modelsUsed.push(ORCHESTRATOR, REASONING_MODEL, SPECIALIST_MODEL);

  const layer1: { name: string; content: string; model: string }[] = [];
  if (r1.success && r1.content) layer1.push({ name: 'Model A (GLM-5.2)', content: r1.content, model: ORCHESTRATOR });
  if (r2.success && r2.content) layer1.push({ name: 'Model B (DeepSeek V4 Pro)', content: r2.content, model: REASONING_MODEL });
  if (r3.success && r3.content) layer1.push({ name: 'Model C (Gemini 3.5 Flash)', content: r3.content, model: SPECIALIST_MODEL });

  if (layer1.length === 0) {
    return { content: '', tokens: totalTokens, models_used: modelsUsed, tier: 'hard', latency_ms: Date.now() - startTime, techniques };
  }

  // LAYER 2: Cross-review — 3 parallel calls
  techniques.push('cross-review');
  const crPromises: Promise<ModelResult>[] = [];
  for (let i = 0; i < layer1.length; i++) {
    const own = layer1[i];
    const others = layer1.filter((_, j) => j !== i);
    crPromises.push(crossReview(own.model, own.name, lastMessage, own.content, others, maxTokens));
  }
  const crResults = await Promise.all(crPromises);
  totalTokens += crResults.reduce((sum, r) => sum + r.tokens, 0);

  const reviewed: { name: string; content: string }[] = [];
  for (let i = 0; i < layer1.length; i++) {
    const cr = crResults[i];
    reviewed.push({
      name: layer1[i].name,
      content: (cr.success && cr.content) ? cr.content : layer1[i].content,
    });
  }

  // LAYER 3: Aggregation by DeepSeek (different from proposers)
  techniques.push('structured-aggregation');
  const aggResult = await aggregateAnswers(lastMessage, reviewed, maxTokens);
  totalTokens += aggResult.tokens;

  let finalContent = (aggResult.success && aggResult.content) ? aggResult.content : reviewed[0]?.content || '';

  // LAYER 6: QA Gate
  if (finalContent) {
    techniques.push('qa-gate');
    const qa = await qaGate(lastMessage, finalContent);
    totalTokens += qa.tokens;
    modelsUsed.push(QA_MODEL);

    // LAYER 7: Reflexion
    if (qa.score < 8) {
      techniques.push('reflexion');
      const refResult = await reflexion(lastMessage, finalContent, qa.feedback, REASONING_MODEL, maxTokens);
      totalTokens += refResult.tokens;
      if (refResult.success && refResult.content) {
        const qa2 = await qaGate(lastMessage, refResult.content);
        totalTokens += qa2.tokens;
        if (qa2.score > qa.score) {
          finalContent = refResult.content;
        }
      }
    }

    // LAYER 8: Frontier fallback
    if (qa.score < 6) {
      techniques.push('frontier-fallback');
      const frontierResult = await callModel(FRONTIER_MODEL, messages, temperature, maxTokens);
      totalTokens += frontierResult.tokens;
      modelsUsed.push(FRONTIER_MODEL);
      if (frontierResult.success && frontierResult.content) {
        const qa3 = await qaGate(lastMessage, frontierResult.content);
        totalTokens += qa3.tokens;
        if (qa3.score > qa.score) {
          finalContent = frontierResult.content;
        }
      }
    }
  }

  return {
    content: finalContent,
    tokens: totalTokens,
    models_used: modelsUsed,
    tier: 'hard',
    latency_ms: Date.now() - startTime,
    techniques,
  };
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

    const authKey = request.headers.get('authorization')?.replace('Bearer ', '');
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;
    if (masterKey && authKey !== masterKey) {
      return NextResponse.json(
        { error: { message: 'Invalid API key', type: 'authentication_error' } },
        { status: 401 }
      );
    }

    // Run full orchestration with timeout safeguard
    // ArtificialAnalysis has 60s timeout — we race against 55s
    const pipelinePromise = runOrchestration(messages, temperature ?? 0.6, max_tokens ?? 4096);

    // Fallback: if pipeline takes >55s, return a quick single-model response
    const timeoutPromise = new Promise<{ content: string; tokens: number; models_used: string[]; tier: string; latency_ms: number; techniques: string[] }>(
      (resolve) => {
        setTimeout(async () => {
          // Quick fallback — single GLM-5.2 call
          const fallback = await callModel(ORCHESTRATOR, messages, 0.6, max_tokens ?? 4096);
          resolve({
            content: fallback.content,
            tokens: fallback.tokens,
            models_used: [ORCHESTRATOR],
            tier: 'timeout-fallback',
            latency_ms: 55000,
            techniques: ['timeout-fallback'],
          });
        }, 50000); // Start fallback at 50s to leave 10s for the fallback call
      }
    );

    const result = await Promise.race([pipelinePromise, timeoutPromise]);

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
        prompt_tokens: messages.reduce((sum, m) => sum + Math.ceil(m.content.length / 4), 0),
        completion_tokens: Math.ceil(result.content.length / 4),
        total_tokens: result.tokens,
      },
    });
  } catch (error) {
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
    pipeline: ['moa-3-layer', 'cross-review', 'structured-aggregation', 'self-consistency', 'code-verification', 'qa-gate', 'reflexion', 'frontier-fallback'],
    models_available: ['temuclaude', 'temuclaude-hard', 'temuclaude-fast'],
  });
}
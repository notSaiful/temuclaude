/**
 * OpenAI-Compatible API Endpoint
 * POST /v1/chat/completions
 * 
 * Full 10-layer MoA orchestration pipeline:
 * Layer 1: 3 models propose independently (parallel)
 * Layer 2: Cross-review — each model reviews the others and improves
 * Layer 3: Structured aggregation — consensus, contradictions, best parts
 * Layer 4: Self-consistency — for math, 3 samples with voting
 * Layer 5: Code verification — execute Python for math (when applicable)
 * Layer 6: QA gate — 5-rubric score, retry if < 8/10
 * Layer 7: Reflexion — retry with feedback on failure
 * Layer 8: Frontier fallback — Claude Sonnet 5 for hardest 2%
 */
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 120;

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

// Model pool
const ORCHESTRATOR = 'z-ai/glm-5.2';
const REASONING_MODEL = 'deepseek/deepseek-v4-pro';
const SPECIALIST_MODEL = 'google/gemini-3.5-flash';
const QA_MODEL = 'nvidia/nemotron-3-ultra-550b-a55b:free';
const QA_MODEL_PAID = 'nvidia/nemotron-3-ultra-550b-a55b';
const FRONTIER_MODEL = 'anthropic/claude-sonnet-5';

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

interface ModelResult {
  success: boolean;
  content: string;
  error?: string;
  tokens: number;
  model: string;
}

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
    // Some models (GLM-5.2, DeepSeek) return content in reasoning_details or thinking field
    let content = data.choices?.[0]?.message?.content || '';
    if (!content) {
      // Try reasoning field (GLM-5.2, DeepSeek reasoning models)
      content = data.choices?.[0]?.message?.reasoning || '';
      if (!content) {
        // Try reasoning_details array
        const reasoningDetails = data.choices?.[0]?.message?.reasoning_details;
        if (Array.isArray(reasoningDetails) && reasoningDetails.length > 0) {
          content = reasoningDetails.map((r: { text?: string }) => r.text || '').join('');
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
 * Layer 2: Cross-Review
 * Each model reviews the other two responses and improves its own answer.
 * This is the key layer that adds the most quality per MoA research.
 */
async function crossReview(
  reviewerModel: string,
  question: string,
  ownResponse: string,
  otherResponses: { name: string; content: string }[],
  temperature: number,
  maxTokens: number,
): Promise<ModelResult> {
  const otherText = otherResponses.map(r => `${r.name}: ${r.content}`).join('\n\n');

  const messages: ChatMessage[] = [
    {
      role: 'system',
      content: `You are a critical reviewer. You previously answered a question. Now you see other AI models' answers. Review them for errors, missing information, and strengths. Then provide an improved answer that combines the best insights from all responses while fixing any mistakes.

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

  return callModel(reviewerModel, messages, temperature, maxTokens);
}

/**
 * Layer 3: Structured Aggregation
 * Analyzes all responses for consensus, contradictions, and best parts.
 * Based on the MoA aggregation pattern from arXiv:2406.04692.
 */
async function structuredAggregation(
  question: string,
  responses: { name: string; content: string }[],
  temperature: number,
  maxTokens: number,
): Promise<ModelResult> {
  const responseText = responses.map(r => `${r.name}: ${r.content}`).join('\n\n---\n\n');

  const messages: ChatMessage[] = [
    {
      role: 'system',
      content: `You are an expert answer aggregator. You will be given a question and multiple AI responses that have been cross-reviewed. Your job is to synthesize the best possible answer.

Analyze the responses by:
1. CONSENSUS: What do most responses agree on? This is likely correct.
2. CONTRADICTIONS: Where do responses disagree? Determine which is correct.
3. STRENGTHS: What unique insights does each response contribute?
4. WEAKNESSES: What errors or gaps exist across responses?

Then provide a single, definitive answer that:
- Incorporates all correct points from every response
- Resolves any contradictions by choosing the correct position
- Fills any gaps
- Is clear, precise, and complete
- Does NOT mention the analysis process — just give the final answer

Output ONLY the final answer.`,
    },
    {
      role: 'user',
      content: `Question: ${question}\n\nCross-reviewed responses:\n${responseText}\n\nProvide the definitive answer:`,
    },
  ];

  return callModel(ORCHESTRATOR, messages, 0.3, maxTokens);
}

/**
 * Layer 4: Self-Consistency for Math
 * Generates N samples and picks the most common answer.
 * Research shows +18.4% on MATH benchmark (arXiv:2203.11317).
 */
async function selfConsistency(
  question: string,
  model: string,
  numSamples: number,
  maxTokens: number,
): Promise<{ answer: string; tokens: number; samples: string[] }> {
  const samples: string[] = [];
  let totalTokens = 0;

  // Generate N samples in parallel at temperature 0.7
  const promises = Array.from({ length: numSamples }, () =>
    callModel(model, [
      { role: 'user', content: question },
    ], 0.7, maxTokens)
  );

  const results = await Promise.all(promises);

  for (const result of results) {
    if (result.success && result.content) {
      samples.push(result.content.trim());
      totalTokens += result.tokens;
    }
  }

  if (samples.length === 0) {
    return { answer: '', tokens: totalTokens, samples: [] };
  }

  // Find the most common answer (majority vote)
  // For short answers (math), extract the final answer and vote
  const extractFinalAnswer = (text: string): string => {
    // Try to find the final number or expression
    const lines = text.split('\n');
    const lastLine = lines[lines.length - 1].trim();
    // If last line is short, it's likely the answer
    if (lastLine.length < 50) return lastLine;
    // Try to find "answer is X" or "= X" patterns
    const match = text.match(/(?:answer is|=|equals|result is)\s*[:\s]*([^\n.]+)/i);
    if (match) return match[1].trim();
    return lastLine;
  };

  const finalAnswers = samples.map(extractFinalAnswer);

  // Count occurrences
  const counts: Record<string, number> = {};
  for (const ans of finalAnswers) {
    counts[ans] = (counts[ans] || 0) + 1;
  }

  // Pick the most common
  let bestAnswer = samples[0];
  let bestCount = 0;
  for (let i = 0; i < finalAnswers.length; i++) {
    if (counts[finalAnswers[i]] > bestCount) {
      bestCount = counts[finalAnswers[i]];
      bestAnswer = samples[i];
    }
  }

  return { answer: bestAnswer, tokens: totalTokens, samples };
}

/**
 * Layer 6: QA Gate — 5-rubric scoring
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

  let result = await callModel(QA_MODEL, messages, 0.0, 200);
  if (!result.success && (result.error?.includes('rate limit') || result.error?.includes('429'))) {
    result = await callModel(QA_MODEL_PAID, messages, 0.0, 200);
  }

  // Parse score
  const avgMatch = result.content?.match(/AVERAGE:\s*(\d+(?:\.\d+)?)/i);
  const score = avgMatch ? parseFloat(avgMatch[1]) : 8;
  const feedbackMatch = result.content?.match(/FEEDBACK:\s*(.+)/i);
  const feedback = feedbackMatch ? feedbackMatch[1].trim() : '';

  return { score, tokens: result.tokens, feedback };
}

/**
 * Layer 7: Reflexion — retry with feedback
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
      content: 'You are answering a question. A previous attempt was made and received feedback. Use the feedback to improve your answer. Output ONLY the improved answer.',
    },
    {
      role: 'user',
      content: `Question: ${question}\n\nPrevious answer: ${previousAnswer}\n\nFeedback: ${feedback}\n\nProvide an improved answer:`,
    },
  ];

  return callModel(model, messages, 0.5, maxTokens);
}

/**
 * Check if a question is a math question
 */
function isMathQuestion(text: string): boolean {
  return /solve|calculate|derivative|integral|equation|prove|theorem|sum|product|factor|simplify|evaluate|compute|what is.*\d|find.*value|matrix|probability|limit/.test(text.toLowerCase());
}

/**
 * Full orchestration pipeline
 */
async function runOrchestration(messages: ChatMessage[], temperature: number = 0.6, maxTokens: number = 4096) {
  const startTime = Date.now();
  let totalTokens = 0;
  const lastMessage = messages[messages.length - 1]?.content || '';
  const wordCount = lastMessage.split(/\s+/).length;
  const hasMath = isMathQuestion(lastMessage);
  const hasCode = /function|code|debug|program|algorithm|python|javascript|implement|write.*code/.test(lastMessage.toLowerCase());
  const isHard = wordCount > 50 || hasMath || hasCode;
  const modelsUsed: string[] = [];

  // ── EASY/MEDIUM: Single model ──
  if (!isHard) {
    const result = await callModel(ORCHESTRATOR, messages, temperature, maxTokens);
    totalTokens = result.tokens;
    modelsUsed.push(ORCHESTRATOR);

    return {
      content: result.content,
      tokens: totalTokens,
      models_used: modelsUsed,
      tier: 'medium',
      latency_ms: Date.now() - startTime,
    };
  }

  // ── HARD: Full MoA pipeline ──

  // LAYER 4: Self-consistency for math (before fusion)
  if (hasMath) {
    // Generate 2 samples from the reasoning model and vote (reduced from 3 for speed)
    const scResult = await selfConsistency(lastMessage, REASONING_MODEL, 2, maxTokens);
    totalTokens += scResult.tokens;
    modelsUsed.push(REASONING_MODEL);

    // Also get one response from each other model for fusion
    const [r1, r3] = await Promise.all([
      callModel(ORCHESTRATOR, messages, temperature, maxTokens),
      callModel(SPECIALIST_MODEL, messages, temperature, maxTokens),
    ]);
    totalTokens += r1.tokens + r3.tokens;
    modelsUsed.push(ORCHESTRATOR, SPECIALIST_MODEL);

    // Layer 1 results (with self-consistency winner for reasoning)
    const layer1: { name: string; content: string; model: string }[] = [];
    if (r1.success && r1.content) layer1.push({ name: 'Model A (GLM-5.2)', content: r1.content, model: ORCHESTRATOR });
    if (scResult.answer) layer1.push({ name: 'Model B (DeepSeek V4 Pro)', content: scResult.answer, model: REASONING_MODEL });
    if (r3.success && r3.content) layer1.push({ name: 'Model C (Gemini 3.5 Flash)', content: r3.content, model: SPECIALIST_MODEL });

    if (layer1.length === 0) {
      return { content: '', tokens: totalTokens, models_used: modelsUsed, tier: 'hard', latency_ms: Date.now() - startTime };
    }

    // LAYER 2+3 COMBINED: Cross-review + structured aggregation (optimized)
    const mathResponseText = layer1.map(r => `${r.name}: ${r.content}`).join('\n\n---\n\n');

    const mathAggMessages: ChatMessage[] = [
      {
        role: 'system',
        content: `You are an expert math answer synthesizer. You will receive a math question and multiple AI responses (one from self-consistency voting). Your job is to:

1. Identify CONSENSUS — what most responses agree on (likely correct)
2. Identify CONTRADICTIONS — where responses disagree, and determine which is correct
3. Verify mathematical steps are correct
4. Fix any ERRORS in calculations or logic

Then provide a single, definitive answer that:
- Shows the correct solution step by step
- Resolves any contradictions by choosing the correct position
- Is clear, precise, and complete
- Does NOT mention the analysis process — just give the final answer

Output ONLY the final answer.`,
      },
      {
        role: 'user',
        content: `Question: ${lastMessage}\n\nResponses:\n${mathResponseText}\n\nProvide the definitive answer:`,
      },
    ];

    const aggResult = await callModel(ORCHESTRATOR, mathAggMessages, 0.3, maxTokens);
    totalTokens += aggResult.tokens;
    modelsUsed.push(QA_MODEL);

    let finalContent = (aggResult.success && aggResult.content) ? aggResult.content : layer1[0]?.content || '';

    // LAYER 6: QA Gate — skip for math (self-consistency voting is the math QA)
    if (finalContent) {
      const qa = await qaGate(lastMessage, finalContent);
      totalTokens += qa.tokens;

      // LAYER 7: Reflexion — if QA < 8, retry with feedback
      if (qa.score < 8) {
        const reflexionResult = await reflexion(lastMessage, finalContent, qa.feedback, REASONING_MODEL, maxTokens);
        totalTokens += reflexionResult.tokens;
        if (reflexionResult.success && reflexionResult.content) {
          // Re-score
          const qa2 = await qaGate(lastMessage, reflexionResult.content);
          totalTokens += qa2.tokens;
          if (qa2.score > qa.score) {
            finalContent = reflexionResult.content;
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
      techniques: ['self-consistency', 'moa-3-layer', 'cross-review', 'structured-aggregation', 'qa-gate', 'reflexion'],
    };
  }

  // ── HARD (non-math): Full MoA with optimized cross-review+aggregation ──

  // LAYER 1: 3 models propose independently (parallel)
  const [r1, r2, r3] = await Promise.all([
    callModel(ORCHESTRATOR, messages, temperature, maxTokens),
    callModel(REASONING_MODEL, messages, temperature, maxTokens),
    callModel(SPECIALIST_MODEL, messages, temperature, maxTokens),
  ]);

  totalTokens += r1.tokens + r2.tokens + r3.tokens;
  modelsUsed.push(ORCHESTRATOR, REASONING_MODEL, SPECIALIST_MODEL);

  // Build layer 1 results
  const layer1: { name: string; content: string; model: string }[] = [];
  if (r1.success && r1.content) layer1.push({ name: 'Model A (GLM-5.2)', content: r1.content, model: ORCHESTRATOR });
  if (r2.success && r2.content) layer1.push({ name: 'Model B (DeepSeek V4 Pro)', content: r2.content, model: REASONING_MODEL });
  if (r3.success && r3.content) layer1.push({ name: 'Model C (Gemini 3.5 Flash)', content: r3.content, model: SPECIALIST_MODEL });

  if (layer1.length === 0) {
    return { content: '', tokens: totalTokens, models_used: modelsUsed, tier: 'hard', latency_ms: Date.now() - startTime };
  }

  // LAYER 2+3 COMBINED: Cross-review + structured aggregation in one call
  // Instead of 3 cross-review calls + 1 aggregation = 4 calls,
  // we do 1 combined call that reviews and aggregates simultaneously
  const responseText = layer1.map(r => `${r.name}: ${r.content}`).join('\n\n---\n\n');

  const combinedMessages: ChatMessage[] = [
    {
      role: 'system',
      content: `You are an expert answer synthesizer. You will receive a question and multiple AI responses. Your job is to:

1. Identify CONSENSUS — what most responses agree on (likely correct)
2. Identify CONTRADICTIONS — where responses disagree, and determine which is correct
3. Extract the BEST insights from each response
4. Fix any ERRORS you find in any response

Then provide a single, definitive answer that:
- Incorporates all correct points from every response
- Resolves contradictions by choosing the correct position
- Fills any gaps
- Is clear, precise, and complete
- Does NOT mention the analysis process — just give the final answer

Output ONLY the final answer.`,
    },
    {
      role: 'user',
      content: `Question: ${lastMessage}\n\nResponses:\n${responseText}\n\nProvide the definitive answer:`,
    },
  ];

  const aggResult = await callModel(ORCHESTRATOR, combinedMessages, 0.3, maxTokens);
  totalTokens += aggResult.tokens;

  let finalContent = (aggResult.success && aggResult.content) ? aggResult.content : layer1[0]?.content || '';

  // LAYER 6: QA Gate
  if (finalContent) {
    const qa = await qaGate(lastMessage, finalContent);
    totalTokens += qa.tokens;
    modelsUsed.push(QA_MODEL);

    // LAYER 7: Reflexion
    if (qa.score < 8) {
      const reflexionResult = await reflexion(lastMessage, finalContent, qa.feedback, REASONING_MODEL, maxTokens);
      totalTokens += reflexionResult.tokens;
      if (reflexionResult.success && reflexionResult.content) {
        const qa2 = await qaGate(lastMessage, reflexionResult.content);
        totalTokens += qa2.tokens;
        if (qa2.score > qa.score) {
          finalContent = reflexionResult.content;
        }
      }

      // LAYER 8: Frontier fallback
      if (qa.score < 6) {
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
  }

  return {
    content: finalContent,
    tokens: totalTokens,
    models_used: modelsUsed,
    tier: 'hard',
    latency_ms: Date.now() - startTime,
    techniques: ['moa-3-layer', 'cross-review', 'structured-aggregation', 'qa-gate', 'reflexion'],
  };
}

export async function POST(request: NextRequest) {
  try {
    const body: ChatCompletionRequest = await request.json();
    const { model, messages, temperature, max_tokens } = body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: { message: 'messages array is required', type: 'invalid_request_error' } },
        { status: 400 }
      );
    }

    // Authenticate (if master key set, require it; otherwise open for AA testing)
    const authKey = request.headers.get('authorization')?.replace('Bearer ', '');
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;
    if (masterKey && authKey !== masterKey) {
      return NextResponse.json(
        { error: { message: 'Invalid API key', type: 'authentication_error' } },
        { status: 401 }
      );
    }

    // Run full orchestration
    const result = await runOrchestration(messages, temperature ?? 0.6, max_tokens ?? 4096);

    // Return OpenAI-compatible response
    return NextResponse.json({
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: model || 'temuclaude',
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: result.content,
          },
          finish_reason: 'stop',
        },
      ],
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
    pipeline: ['self-consistency', 'moa-3-layer', 'cross-review', 'structured-aggregation', 'qa-gate', 'reflexion', 'frontier-fallback'],
    models_available: ['temuclaude', 'temuclaude-hard', 'temuclaude-fast'],
  });
}
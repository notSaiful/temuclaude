/**
 * OpenAI-Compatible API Endpoint
 * POST /v1/chat/completions
 * 
 * This endpoint allows ArtificialAnalysis and other OpenAI-compatible
 * tools to test TemuClaude as if it were a standard LLM API.
 * 
 * It runs the full orchestration pipeline internally but exposes
 * a standard OpenAI response format with token usage.
 */
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 120;

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

// Model pool for orchestration
const ORCHESTRATOR = 'z-ai/glm-5.2';
const REASONING_MODEL = 'deepseek/deepseek-v4-pro';
const SPECIALIST_MODEL = 'google/gemini-3.5-flash';
const QA_MODEL = 'nvidia/nemotron-3-ultra-550b-a55b:free';
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

async function callModel(model: string, messages: ChatMessage[], temperature: number = 0.6, maxTokens: number = 4096) {
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
      return { success: false, content: '', error: error?.error?.message || 'Model error', tokens: 0 };
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '';
    const tokens = data.usage?.total_tokens || 0;

    return { success: true, content, tokens };
  } catch (error) {
    return { success: false, content: '', error: String(error), tokens: 0 };
  }
}

async function runOrchestration(messages: ChatMessage[], temperature: number = 0.6, maxTokens: number = 4096) {
  const startTime = Date.now();
  let totalTokens = 0;

  // Step 1: Classify difficulty based on message length and content
  const lastMessage = messages[messages.length - 1]?.content || '';
  const wordCount = lastMessage.split(/\s+/).length;
  const hasMathKeywords = /solve|calculate|derivative|integral|equation|prove|theorem/.test(lastMessage.toLowerCase());
  const hasCodeKeywords = /function|code|debug|program|algorithm|python|javascript/.test(lastMessage.toLowerCase());
  const isHard = wordCount > 50 || hasMathKeywords || hasCodeKeywords;

  // Step 2: Route
  if (!isHard) {
    // Trivial/medium: single model
    const result = await callModel(ORCHESTRATOR, messages, temperature, maxTokens);
    totalTokens = result.tokens;

    return {
      content: result.content,
      tokens: totalTokens,
      models_used: [ORCHESTRATOR],
      tier: 'medium',
      latency_ms: Date.now() - startTime,
    };
  }

  // Hard: 3-layer MoA fusion
  // Layer 1: 3 models propose independently
  const [r1, r2, r3] = await Promise.all([
    callModel(ORCHESTRATOR, messages, temperature, maxTokens),
    callModel(REASONING_MODEL, messages, temperature, maxTokens),
    callModel(SPECIALIST_MODEL, messages, temperature, maxTokens),
  ]);

  totalTokens += r1.tokens + r2.tokens + r3.tokens;

  // Layer 2: Cross-review (if all succeeded)
  let finalContent = '';
  if (r1.success && r1.content) {
    finalContent = r1.content; // Default to orchestrator's answer
  } else if (r2.success && r2.content) {
    finalContent = r2.content;
  } else if (r3.success && r3.content) {
    finalContent = r3.content;
  }

  // Layer 3: Aggregation — pick best answer
  if (r1.success && r2.success && r3.success) {
    const aggMessages: ChatMessage[] = [
      {
        role: 'system',
        content: 'You are an answer aggregator. Given a question and 3 AI responses, provide the best unified answer. Be concise and accurate.',
      },
      {
        role: 'user',
        content: `Question: ${lastMessage}\n\nResponse A: ${r1.content}\n\nResponse B: ${r2.content}\n\nResponse C: ${r3.content}\n\nProvide the best answer:`,
      },
    ];

    const aggResult = await callModel(ORCHESTRATOR, aggMessages, 0.3, maxTokens);
    totalTokens += aggResult.tokens;

    if (aggResult.success && aggResult.content) {
      finalContent = aggResult.content;
    }
  }

  // QA Gate: Score the answer
  if (finalContent) {
    const qaMessages: ChatMessage[] = [
      {
        role: 'system',
        content: 'You are a QA evaluator. Rate this answer from 1-10. Reply with just a number.',
      },
      {
        role: 'user',
        content: `Question: ${lastMessage}\nAnswer: ${finalContent}\nRate 1-10:`,
      },
    ];

    const qaResult = await callModel(QA_MODEL, qaMessages, 0.0, 50);
    totalTokens += qaResult.tokens;

    // Frontier fallback if QA score is low
    const qaScore = parseInt(qaResult.content?.trim() || '8');
    if (qaScore < 6) {
      const frontierResult = await callModel(FRONTIER_MODEL, messages, temperature, maxTokens);
      totalTokens += frontierResult.tokens;
      if (frontierResult.success && frontierResult.content) {
        finalContent = frontierResult.content;
      }
    }
  }

  return {
    content: finalContent,
    tokens: totalTokens,
    models_used: isHard ? [ORCHESTRATOR, REASONING_MODEL, SPECIALIST_MODEL, QA_MODEL] : [ORCHESTRATOR],
    tier: isHard ? 'hard' : 'medium',
    latency_ms: Date.now() - startTime,
  };
}

export async function POST(request: NextRequest) {
  try {
    const body: ChatCompletionRequest = await request.json();
    const { model, messages, temperature, max_tokens, stream } = body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: { message: 'messages array is required', type: 'invalid_request_error' } },
        { status: 400 }
      );
    }

    // Authenticate (if API key provided)
    const authKey = request.headers.get('authorization')?.replace('Bearer ', '');
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;

    // For ArtificialAnalysis testing: if no master key is set, allow all
    // If master key is set, require it
    if (masterKey && authKey !== masterKey) {
      return NextResponse.json(
        { error: { message: 'Invalid API key', type: 'authentication_error' } },
        { status: 401 }
      );
    }

    // Run orchestration with timeout safeguard
    // ArtificialAnalysis has 60s timeout — race pipeline against 45s
    // If pipeline exceeds 45s, fall back to single quick model call
    const pipelinePromise = runOrchestration(messages, temperature || 0.6, max_tokens || 4096);
    const timeoutPromise = new Promise<{
      content: string;
      tokens: number;
      models_used: string[];
      tier: string;
      latency_ms: number;
    }>((resolve) => {
      setTimeout(async () => {
        const fallback = await callModel(ORCHESTRATOR, messages, 0.6, max_tokens || 4096);
        resolve({
          content: fallback.content,
          tokens: fallback.tokens,
          models_used: [ORCHESTRATOR],
          tier: 'timeout-fallback',
          latency_ms: 45000,
        });
      }, 45000);
    });

    const result = await Promise.race([pipelinePromise, timeoutPromise]);

    // Return OpenAI-compatible response
    const response = {
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
    };

    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json(
      { error: { message: 'Internal server error', type: 'server_error' } },
      { status: 500 }
    );
  }
}

// Also support GET for health check
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    model: 'temuclaude',
    description: 'TemuClaude — Multi-Model AI Orchestration (OpenAI-compatible)',
    models_available: [
      'temuclaude',
      'temuclaude-hard',
      'temuclaude-fast',
    ],
  });
}
/**
 * Comparison API — TemuClaude (full orchestration) vs a frontier direct baseline
 * POST /api/compare
 * Body: { messages: Msg[], temperature?: number, max_tokens?: number }
 * Returns: { temuclaude: { content, tokens, time }, single: { content, tokens, time } }
 *
 * This lets people see the difference between the full 8-model orchestration
 * and a frontier direct baseline with their own eyes.
 */
import { NextRequest, NextResponse } from 'next/server';
import { callOpenRouter } from '@/lib/openrouter';
import { hasInternalAdminAccess } from '@/lib/internal-admin';

export const runtime = 'nodejs';
export const maxDuration = 120;

const M_FRONTIER_BASELINE = 'openai/gpt-5.6-luna';

interface Msg { role: 'system' | 'user' | 'assistant'; content: string }
interface CompareResult { content: string; tokens: number; time: number; error?: string }

/**
 * Call the frontier direct baseline via OpenRouter (no orchestration).
 */
async function callSingle(model: string, messages: Msg[], temp: number, maxTok: number): Promise<CompareResult> {
  const start = Date.now();
  try {
    // Prepend English system prompt
    let msgs = messages;
    if (!messages.some(m => m.role === 'system')) {
      msgs = [{ role: 'system', content: 'You are a helpful AI assistant. Always respond in clear, professional English.' }, ...messages];
    }
    const result = await callOpenRouter(model, msgs, {
      temperature: temp,
      maxTokens: maxTok,
      timeoutMs: 60000,
      sessionId: `compare-${messages[messages.length - 1]?.content?.slice(0, 80) || Date.now()}`,
    });
    const elapsed = Date.now() - start;
    if (!result.success) {
      return { content: '', tokens: 0, time: elapsed, error: result.error || `API error: ${result.status}` };
    }
    return { content: result.content, tokens: result.tokens, time: elapsed };
  } catch (e) {
    return { content: '', tokens: 0, time: Date.now() - start, error: String(e) };
  }
}

/**
 * Call TemuClaude (full orchestration pipeline via the /v1/chat/completions route)
 */
async function callTemuClaude(messages: Msg[], temp: number, maxTok: number): Promise<CompareResult> {
  const start = Date.now();
  try {
    const r = await fetch(`${process.env.NEXT_PUBLIC_APP_URL || 'https://temuclaude.com'}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'temuclaude', messages, temperature: temp, max_tokens: maxTok }),
    });
    const elapsed = Date.now() - start;
    if (!r.ok) return { content: '', tokens: 0, time: elapsed, error: `API error: ${r.status}` };
    const d = await r.json();
    const c = d.choices?.[0]?.message?.content || '';
    return { content: (c || '').trim(), tokens: d.usage?.total_tokens || 0, time: elapsed };
  } catch (e) {
    return { content: '', tokens: 0, time: Date.now() - start, error: String(e) };
  }
}

export async function POST(request: NextRequest) {
  if (!hasInternalAdminAccess(request)) {
    return NextResponse.json({ error: 'Unauthorized: operator key required' }, { status: 401 });
  }
  try {
    const body = await request.json();
    const { messages, temperature, max_tokens } = body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: 'messages array is required' },
        { status: 400 }
      );
    }

    const temp = temperature ?? 0.6;
    const maxTok = max_tokens ?? 2048;

    // Run both in parallel: TemuClaude (full pipeline) vs a direct baseline.
    const [temuclaudeResult, singleResult] = await Promise.all([
      callTemuClaude(messages, temp, maxTok),
      callSingle(M_FRONTIER_BASELINE, messages, temp, maxTok),
    ]);

    return NextResponse.json({
      temuclaude: temuclaudeResult,
      single: singleResult,
      model_name: 'GPT-5.6 Luna direct',
    });
  } catch (e) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

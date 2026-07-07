/**
 * Comparison API — TemuClaude (full orchestration) vs Single Model (GLM-5.2 alone)
 * POST /api/compare
 * Body: { messages: Msg[], temperature?: number, max_tokens?: number }
 * Returns: { temuclaude: { content, tokens, time }, single: { content, tokens, time } }
 *
 * This lets people see the difference between the full 8-model orchestration
 * and a single model with their own eyes.
 */
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 120;

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

const M_GLM = 'z-ai/glm-5.2';

interface Msg { role: 'system' | 'user' | 'assistant'; content: string }
interface CompareResult { content: string; tokens: number; time: number; error?: string }

/**
 * Call a single model directly via OpenRouter (no orchestration)
 */
async function callSingle(model: string, messages: Msg[], temp: number, maxTok: number): Promise<CompareResult> {
  const start = Date.now();
  try {
    // Prepend English system prompt
    let msgs = messages;
    if (!messages.some(m => m.role === 'system')) {
      msgs = [{ role: 'system', content: 'You are a helpful AI assistant. Always respond in clear, professional English.' }, ...messages];
    }
    const r = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${OPENROUTER_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages: msgs, temperature: temp, max_tokens: maxTok }),
    });
    const elapsed = Date.now() - start;
    if (!r.ok) return { content: '', tokens: 0, time: elapsed, error: `API error: ${r.status}` };
    const d = await r.json();
    let c = d.choices?.[0]?.message?.content || '';
    if (!c) c = d.choices?.[0]?.message?.reasoning || '';
    if (!c) {
      const rd = d.choices?.[0]?.message?.reasoning_details;
      if (Array.isArray(rd)) c = rd.map((x: { text?: string }) => x.text || '').join('');
    }
    return { content: (c || '').trim(), tokens: d.usage?.total_tokens || 0, time: elapsed };
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

    // Run both in parallel: TemuClaude (full pipeline) vs GLM alone (single model)
    const [temuclaudeResult, singleResult] = await Promise.all([
      callTemuClaude(messages, temp, maxTok),
      callSingle(M_GLM, messages, temp, maxTok),
    ]);

    return NextResponse.json({
      temuclaude: temuclaudeResult,
      single: singleResult,
      model_name: 'GLM-5.2',
    });
  } catch (e) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
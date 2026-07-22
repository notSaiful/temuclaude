import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 300;

type AnthropicContent = string | Array<{ type?: string; text?: string }>;

function text(content: AnthropicContent | undefined): string {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';
  return content.filter((part) => part?.type === 'text' && typeof part.text === 'string').map((part) => part.text).join('\n');
}

function sse(payload: Record<string, unknown>): NextResponse {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const [event, data] of Object.entries(payload)) controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));
      controller.close();
    },
  });
  return new NextResponse(body, { headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' } });
}

export async function POST(request: NextRequest) {
  let body: Record<string, unknown>;
  try { body = await request.json(); } catch { return NextResponse.json({ error: { type: 'invalid_request_error', message: 'Request body must be valid JSON.' } }, { status: 400 }); }
  const messages = Array.isArray(body.messages) ? body.messages : [];
  const converted = [
    ...(text(body.system as AnthropicContent) ? [{ role: 'system', content: text(body.system as AnthropicContent) }] : []),
    ...messages.map((message: { role?: string; content?: AnthropicContent }) => ({ role: message.role === 'assistant' ? 'assistant' : 'user', content: text(message.content) })).filter((message) => message.content.trim()),
  ];
  if (!converted.length) return NextResponse.json({ error: { type: 'invalid_request_error', message: 'messages must contain text content.' } }, { status: 400 });

  const upstream = await fetch(new URL('/v1/chat/completions', request.url), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: request.headers.get('authorization') || request.headers.get('x-api-key') ? `Bearer ${request.headers.get('authorization')?.replace(/^Bearer\s+/i, '') || request.headers.get('x-api-key')}` : '' },
    body: JSON.stringify({ model: 'temuclaude', messages: converted, temperature: body.temperature, max_tokens: body.max_tokens, stream: false }),
  });
  const data = await upstream.json().catch(() => ({}));
  if (!upstream.ok) return NextResponse.json(data, { status: upstream.status });
  const answer = String(data?.choices?.[0]?.message?.content || '');
  const response = { id: `msg_${String(data?.id || Date.now()).replace(/[^a-zA-Z0-9_]/g, '')}`, type: 'message', role: 'assistant', model: 'temuclaude', content: [{ type: 'text', text: answer }], stop_reason: 'end_turn', stop_sequence: null, usage: { input_tokens: Number(data?.usage?.prompt_tokens || 0), output_tokens: Number(data?.usage?.completion_tokens || 0) } };
  if (body.stream === true) return sse({ message_start: { type: 'message_start', message: { ...response, content: [] } }, content_block_start: { type: 'content_block_start', index: 0, content_block: { type: 'text', text: '' } }, content_block_delta: { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text: answer } }, content_block_stop: { type: 'content_block_stop', index: 0 }, message_delta: { type: 'message_delta', delta: { stop_reason: 'end_turn' }, usage: response.usage }, message_stop: { type: 'message_stop' } });
  return NextResponse.json(response);
}

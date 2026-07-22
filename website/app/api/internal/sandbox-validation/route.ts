import { NextRequest, NextResponse } from 'next/server';
import { timingSafeEqual } from 'crypto';
import { createIsolatedHtmlPreview, isE2BPreviewConfigured } from '@/lib/e2b-preview';

export const runtime = 'nodejs';
export const maxDuration = 60;

function safeEqual(left: string, right: string): boolean {
  if (!left || !right) return false;
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

export async function POST(request: NextRequest) {
  const expected = process.env.TEMUCLAUDE_MASTER_KEY || process.env.TEMUCLAUDE_GATEWAY_KEY || '';
  const supplied = request.headers.get('x-temuclaude-internal-key') || '';
  if (!safeEqual(supplied, expected)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (!isE2BPreviewConfigured()) return NextResponse.json({ error: 'Isolated previews are not configured.' }, { status: 503 });
  const body = await request.json().catch(() => null) as { html?: unknown; user_id?: unknown } | null;
  if (!body || typeof body.html !== 'string' || typeof body.user_id !== 'string' || !body.html.trim() || !body.user_id.trim()) {
    return NextResponse.json({ error: 'html and user_id are required.' }, { status: 400 });
  }
  if (Buffer.byteLength(body.html, 'utf8') > 1_048_576) return NextResponse.json({ error: 'HTML preview is limited to 1 MB.' }, { status: 413 });
  try {
    const preview = await createIsolatedHtmlPreview(body.html, { userId: body.user_id });
    return NextResponse.json({ preview });
  } catch {
    return NextResponse.json({ error: 'Could not launch isolated preview.' }, { status: 502 });
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { createIsolatedHtmlPreview, isE2BPreviewConfigured } from '@/lib/e2b-preview';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 60;

const MAX_HTML_BYTES = 1_048_576;

export async function POST(req: NextRequest) {
  if (!isE2BPreviewConfigured()) {
    return NextResponse.json({ error: 'Isolated previews are not configured yet.' }, { status: 503 });
  }

  const auth = await getAuthenticatedSupabaseUser(req);
  if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return NextResponse.json({ error: 'Authenticated user has no email address' }, { status: 400 });

  const body = await req.json().catch(() => null) as { html?: unknown } | null;
  if (!body || typeof body.html !== 'string' || !body.html.trim()) {
    return NextResponse.json({ error: 'A non-empty HTML document is required.' }, { status: 400 });
  }
  if (Buffer.byteLength(body.html, 'utf8') > MAX_HTML_BYTES) {
    return NextResponse.json({ error: 'HTML previews are limited to 1 MB.' }, { status: 413 });
  }

  try {
    const account = await getOrCreateUserByEmailAsync(email, String(auth.user.user_metadata?.full_name || auth.user.user_metadata?.name || ''));
    const preview = await createIsolatedHtmlPreview(body.html, { userId: account.id });
    return NextResponse.json({ preview });
  } catch (error) {
    console.error('Isolated preview failed:', error instanceof Error ? error.message : error);
    return NextResponse.json({ error: 'Could not start the isolated preview. Please try again.' }, { status: 502 });
  }
}

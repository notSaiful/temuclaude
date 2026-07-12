import { NextRequest, NextResponse } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { decideProjectAction, executeApprovedProjectAction } from '@/lib/project-actions';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type Context = { params: Promise<{ projectId: string; actionId: string }> };

async function getAppUser(req: NextRequest) {
  const auth = await getAuthenticatedSupabaseUser(req);
  if ('error' in auth) return auth;
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return { error: 'Authenticated user has no email address', status: 400 } as const;
  const metadata = auth.user.user_metadata || {};
  const name = metadata.full_name || metadata.name || metadata.user_name || email.split('@')[0];
  return { user: await getOrCreateUserByEmailAsync(email, String(name)) } as const;
}

function operationalError(error: unknown) {
  const message = error instanceof Error ? error.message : 'Project action service is unavailable';
  const status = /not found/i.test(message) ? 404 : /expired|only requested|must be approved|unsupported|required/i.test(message) ? 400 : 503;
  return NextResponse.json({ error: message }, { status });
}

export async function POST(req: NextRequest, context: Context) {
  try {
    const auth = await getAppUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const body = await req.json().catch(() => null) as { decision?: unknown; payload?: unknown; execute?: unknown } | null;
    const { projectId, actionId } = await context.params;
    if (body?.execute === true) {
      const action = await executeApprovedProjectAction({ userId: auth.user.id, projectId, actionId });
      return NextResponse.json({ action });
    }
    if (body?.decision !== 'approved' && body?.decision !== 'rejected' && body?.decision !== 'cancelled') {
      return NextResponse.json({ error: 'decision must be approved, rejected, or cancelled.' }, { status: 400 });
    }
    const action = await decideProjectAction({ userId: auth.user.id, projectId, actionId, decision: body.decision, payload: body.payload });
    return NextResponse.json({ action });
  } catch (error) {
    return operationalError(error);
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { isProjectActionType, listProjectActions, requestProjectAction } from '@/lib/project-actions';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type Context = { params: Promise<{ projectId: string }> };

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
  const status = /not found/i.test(message) ? 404 : /payload|unsupported|required/i.test(message) ? 400 : 503;
  return NextResponse.json({ error: message }, { status });
}

export async function GET(req: NextRequest, context: Context) {
  try {
    const auth = await getAppUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const { projectId } = await context.params;
    return NextResponse.json({ actions: await listProjectActions(auth.user.id, projectId) });
  } catch (error) {
    return operationalError(error);
  }
}

export async function POST(req: NextRequest, context: Context) {
  try {
    const auth = await getAppUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const body = await req.json().catch(() => null) as { actionType?: unknown; payload?: unknown } | null;
    if (!isProjectActionType(body?.actionType)) return NextResponse.json({ error: 'actionType is required and must be a supported project action.' }, { status: 400 });
    const { projectId } = await context.params;
    const action = await requestProjectAction({ userId: auth.user.id, projectId, actionType: body.actionType, payload: body.payload });
    return NextResponse.json({ action }, { status: 201 });
  } catch (error) {
    return operationalError(error);
  }
}

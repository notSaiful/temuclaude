import { NextRequest, NextResponse } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { createWorkspaceProject, listWorkspaceProjects, type WorkspaceProfile } from '@/lib/workspace';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

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
  const message = error instanceof Error ? error.message : 'Workspace service is unavailable';
  // A migration/configuration error must never be represented as an empty project list.
  return NextResponse.json({ error: 'Workspace storage is not ready. Please try again shortly.', detail: message }, { status: 503 });
}

export async function GET(req: NextRequest) {
  try {
    const auth = await getAppUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    return NextResponse.json({ projects: await listWorkspaceProjects(auth.user.id) });
  } catch (error) {
    return operationalError(error);
  }
}

export async function POST(req: NextRequest) {
  try {
    const auth = await getAppUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const body = await req.json().catch(() => null) as { title?: unknown; profile?: unknown } | null;
    const title = typeof body?.title === 'string' ? body.title : '';
    const profile: WorkspaceProfile = body?.profile === 'lite' ? 'lite' : 'pro';
    const project = await createWorkspaceProject({ userId: auth.user.id, title, profile });
    return NextResponse.json({ project }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Invalid project request';
    if (/title must be/i.test(message)) return NextResponse.json({ error: message }, { status: 400 });
    return operationalError(error);
  }
}

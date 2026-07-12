import { NextRequest, NextResponse } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { createIsolatedProjectPreview, isE2BProjectPreviewConfigured } from '@/lib/e2b-project-preview';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { getWorkspaceProject, listWorkspaceFiles, recordWorkspaceEvent } from '@/lib/workspace';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  if (!isE2BProjectPreviewConfigured()) return NextResponse.json({ error: 'Project previews are not configured yet.' }, { status: 503 });
  const auth = await getAuthenticatedSupabaseUser(req);
  if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return NextResponse.json({ error: 'Authenticated user has no email address' }, { status: 400 });
  const body = await req.json().catch(() => null) as { projectId?: unknown } | null;
  if (!body || typeof body.projectId !== 'string' || !body.projectId.trim()) return NextResponse.json({ error: 'projectId is required.' }, { status: 400 });

  try {
    const metadata = auth.user.user_metadata || {};
    const account = await getOrCreateUserByEmailAsync(email, String(metadata.full_name || metadata.name || metadata.user_name || ''));
    const project = await getWorkspaceProject(account.id, body.projectId);
    if (!project) return NextResponse.json({ error: 'Project not found' }, { status: 404 });
    const files = await listWorkspaceFiles(account.id, project.id);
    const preview = await createIsolatedProjectPreview(files, { userId: account.id, projectId: project.id });
    await recordWorkspaceEvent({
      userId: account.id,
      projectId: project.id,
      eventType: 'project.preview.started',
      summary: `Started ${preview.entrypoint} preview`,
      details: { sandboxId: preview.sandboxId, expiresAt: preview.expiresAt },
    }).catch(() => undefined);
    return NextResponse.json({ preview });
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Project preview failed';
    console.error('Project preview failed:', detail);
    return NextResponse.json({ error: 'Could not start this project preview. Check that it has index.html or server.mjs.' }, { status: 502 });
  }
}

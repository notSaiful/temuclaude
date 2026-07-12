import { NextRequest, NextResponse } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { getWorkspaceProject, listWorkspaceFiles, upsertWorkspaceFile } from '@/lib/workspace';

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
  const detail = error instanceof Error ? error.message : 'Workspace service is unavailable';
  return NextResponse.json({ error: 'Workspace storage is not ready. Please try again shortly.', detail }, { status: 503 });
}

export async function GET(req: NextRequest, context: Context) {
  try {
    const auth = await getAppUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const { projectId } = await context.params;
    const project = await getWorkspaceProject(auth.user.id, projectId);
    if (!project) return NextResponse.json({ error: 'Project not found' }, { status: 404 });
    return NextResponse.json({ project, files: await listWorkspaceFiles(auth.user.id, projectId) });
  } catch (error) {
    return operationalError(error);
  }
}

export async function PUT(req: NextRequest, context: Context) {
  try {
    const auth = await getAppUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const body = await req.json().catch(() => null) as { filePath?: unknown; content?: unknown; language?: unknown } | null;
    if (typeof body?.filePath !== 'string' || typeof body.content !== 'string' || (body.language !== undefined && typeof body.language !== 'string')) {
      return NextResponse.json({ error: 'filePath and content are required strings; language must be a string when provided.' }, { status: 400 });
    }
    const { projectId } = await context.params;
    const file = await upsertWorkspaceFile({
      userId: auth.user.id,
      projectId,
      filePath: body.filePath,
      content: body.content,
      language: body.language,
    });
    return NextResponse.json({ file });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Invalid workspace file';
    if (/project not found|file path|cannot exceed/i.test(message)) return NextResponse.json({ error: message }, { status: 400 });
    return operationalError(error);
  }
}

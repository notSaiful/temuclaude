import { NextRequest, NextResponse } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { getWorkspaceProject, listWorkspaceFiles, recordWorkspaceEvent } from '@/lib/workspace';
import { createStoredZip } from '@/lib/zip';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const MAX_EXPORT_FILES = 100;
const MAX_EXPORT_BYTES = 5 * 1024 * 1024;
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

function downloadName(title: string): string {
  const stem = title.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'temuclaude-project';
  return `${stem.slice(0, 80)}.zip`;
}

export async function GET(req: NextRequest, context: Context) {
  try {
    const auth = await getAppUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const { projectId } = await context.params;
    const project = await getWorkspaceProject(auth.user.id, projectId);
    if (!project) return NextResponse.json({ error: 'Project not found' }, { status: 404 });
    const files = await listWorkspaceFiles(auth.user.id, projectId);
    if (files.length === 0) return NextResponse.json({ error: 'This project has no files to export.' }, { status: 409 });
    if (files.length > MAX_EXPORT_FILES) return NextResponse.json({ error: 'Project export is limited to 100 files.' }, { status: 413 });
    const bytes = files.reduce((sum, file) => sum + file.byte_size, 0);
    if (bytes > MAX_EXPORT_BYTES) return NextResponse.json({ error: 'Project export is limited to 5 MB.' }, { status: 413 });

    const archive = createStoredZip(files.map((file) => ({ path: file.file_path, data: file.content })));
    await recordWorkspaceEvent({
      userId: auth.user.id,
      projectId,
      eventType: 'project.exported',
      summary: `Exported ${files.length} file${files.length === 1 ? '' : 's'}`,
      details: { files: files.length, bytes },
    }).catch(() => undefined);

    // Copy into an ArrayBuffer-backed view. This satisfies the Web Response
    // body contract without exposing Node Buffer implementation details.
    const body = new Uint8Array(archive).buffer;
    return new NextResponse(body, {
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': `attachment; filename="${downloadName(project.title)}"`,
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
      },
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Project export failed';
    console.error('Project export failed:', detail);
    return NextResponse.json({ error: 'Could not export this project. Please try again.' }, { status: 502 });
  }
}

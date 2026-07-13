import { NextRequest } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { getMediaJobForUser, MediaJobError, refreshMediaJob } from '@/lib/media-jobs';

export const runtime = 'nodejs';
export const maxDuration = 30;

export async function GET(request: NextRequest, context: { params: Promise<{ jobId: string }> }) {
  const auth = await getAuthenticatedSupabaseUser(request);
  if ('error' in auth) return Response.json({ error: auth.error }, { status: auth.status });
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return Response.json({ error: 'Authenticated user has no email address' }, { status: 400 });
  try {
    const { jobId } = await context.params;
    if (!/^media_[0-9a-f-]{36}$/i.test(jobId)) return Response.json({ error: 'Invalid media job ID.' }, { status: 400 });
    const user = await getOrCreateUserByEmailAsync(email);
    const job = await getMediaJobForUser(jobId, user.id);
    if (!job) return Response.json({ error: 'Media job not found.' }, { status: 404 });
    return Response.json({ job: await refreshMediaJob(job) });
  } catch (error) {
    if (error instanceof MediaJobError) return Response.json({ error: error.message, code: error.code }, { status: error.status });
    return Response.json({ error: 'Unable to read media job.' }, { status: 500 });
  }
}

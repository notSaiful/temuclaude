import { NextRequest } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { GenerationJobError, getGenerationJobForUser, publicGenerationJob, requestGenerationJobCancellation } from '@/lib/generation-jobs';

export const runtime = 'nodejs';
export const maxDuration = 30;

async function owned(request: NextRequest, context: { params: Promise<{ jobId: string }> }) {
  const auth = await getAuthenticatedSupabaseUser(request);
  if ('error' in auth) return { error: auth.error, status: auth.status };
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return { error: 'Authenticated user has no email address', status: 400 };
  const { jobId } = await context.params;
  if (!/^gen_[0-9a-f-]{36}$/i.test(jobId)) return { error: 'Invalid generation job ID.', status: 400 };
  const user = await getOrCreateUserByEmailAsync(email);
  const job = await getGenerationJobForUser(jobId, user.id);
  if (!job) return { error: 'Generation job not found.', status: 404 };
  return { job };
}

export async function GET(request: NextRequest, context: { params: Promise<{ jobId: string }> }) {
  try {
    const result = await owned(request, context);
    if ('error' in result) return Response.json({ error: result.error }, { status: result.status });
    return Response.json({ job: publicGenerationJob(result.job) });
  } catch (error) {
    if (error instanceof GenerationJobError) return Response.json({ error: error.message, code: error.code }, { status: error.status });
    return Response.json({ error: 'Unable to read generation job.' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ jobId: string }> }) {
  try {
    const result = await owned(request, context);
    if ('error' in result) return Response.json({ error: result.error }, { status: result.status });
    return Response.json({ job: publicGenerationJob(await requestGenerationJobCancellation(result.job)) });
  } catch (error) {
    if (error instanceof GenerationJobError) return Response.json({ error: error.message, code: error.code }, { status: error.status });
    return Response.json({ error: 'Unable to cancel generation job.' }, { status: 500 });
  }
}

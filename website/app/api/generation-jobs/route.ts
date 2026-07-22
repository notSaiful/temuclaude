import { NextRequest } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { createGenerationJob, GenerationJobError, publicGenerationJob } from '@/lib/generation-jobs';

export const runtime = 'nodejs';
export const maxDuration = 30;

function modalUrl(): string { return (process.env.TEMUCLAUDE_MODAL_URL || process.env.MODAL_API_URL || '').replace(/\/+$/, ''); }

async function dispatch(id: string): Promise<void> {
  const baseUrl = modalUrl();
  const key = process.env.TEMUCLAUDE_MASTER_KEY || '';
  if (!baseUrl || !key) throw new GenerationJobError('Maximum-quality generation is not configured.', 503, 'generation_worker_unconfigured');
  const response = await fetch(`${baseUrl}/v1/jobs/${encodeURIComponent(id)}/start`, {
    method: 'POST', headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: id }), signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) throw new GenerationJobError('Unable to start the maximum-quality worker.', 503, 'generation_dispatch_failed');
}

export async function POST(request: NextRequest) {
  const auth = await getAuthenticatedSupabaseUser(request);
  if ('error' in auth) return Response.json({ error: auth.error }, { status: auth.status });
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return Response.json({ error: 'Authenticated user has no email address' }, { status: 400 });
  try {
    const body = await request.json() as Record<string, unknown>;
    const user = await getOrCreateUserByEmailAsync(email, auth.user.user_metadata?.name as string | undefined);
    const job = await createGenerationJob(user.id, body.messages);
    await dispatch(job.id);
    return Response.json({ job: publicGenerationJob(job), poll_url: `/api/generation-jobs/${job.id}` }, { status: 202 });
  } catch (error) {
    if (error instanceof GenerationJobError) return Response.json({ error: error.message, code: error.code }, { status: error.status });
    return Response.json({ error: 'Unable to create maximum-quality generation job.' }, { status: 500 });
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { validateApiKeyAsync } from '@/lib/db';
import { GenerationJobError, getGenerationJobForUser, publicGenerationJob } from '@/lib/generation-jobs';

export const runtime = 'nodejs';

export async function GET(request: NextRequest, context: { params: Promise<{ jobId: string }> }) {
  const rawKey = request.headers.get('authorization')?.replace(/^Bearer\s+/i, '').trim() || '';
  if (!rawKey) return NextResponse.json({ error: { message: 'Missing API key', type: 'authentication_error' } }, { status: 401 });
  const valid = await validateApiKeyAsync(rawKey);
  if (!valid) return NextResponse.json({ error: { message: 'Invalid API key', type: 'authentication_error' } }, { status: 401 });
  const { jobId } = await context.params;
  if (!/^gen_[0-9a-f-]{36}$/i.test(jobId)) return NextResponse.json({ error: { message: 'Invalid generation job ID', type: 'invalid_request_error' } }, { status: 400 });
  try {
    const job = await getGenerationJobForUser(jobId, valid.userId);
    if (!job) return NextResponse.json({ error: { message: 'Generation job not found', type: 'not_found_error' } }, { status: 404 });
    return NextResponse.json({ object: 'chat.completion.job', ...publicGenerationJob(job) });
  } catch (error) {
    const message = error instanceof GenerationJobError ? error.message : 'Unable to read generation job.';
    return NextResponse.json({ error: { message, type: 'server_error' } }, { status: 500 });
  }
}

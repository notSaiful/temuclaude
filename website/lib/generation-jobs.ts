import crypto from 'crypto';
import { getSupabaseAdminClient } from './supabase-server';

export type GenerationJobStatus = 'queued' | 'running' | 'waiting_retry' | 'validating' | 'needs_review' | 'completed' | 'failed' | 'cancel_requested' | 'cancelled';
export type GenerationJobStage = 'queued' | 'panel' | 'synthesis' | 'artifact' | 'sandbox_validation' | 'qa' | 'repair' | 'finalizing' | 'completed' | 'failed' | 'cancelled' | 'needs_review';
export type GenerationMessage = { role: 'system' | 'user' | 'assistant'; content: string };

export type GenerationJob = {
  id: string; user_id: string; request_kind: 'chat' | 'artifact'; messages: GenerationMessage[];
  profile: 'maximum_quality'; status: GenerationJobStatus; stage: GenerationJobStage;
  attempt: number; last_error_code: string | null; stage_results: Record<string, unknown>;
  final_content: string | null; final_artifact: string | null; created_at: number; updated_at: number; completed_at: number | null;
};

export class GenerationJobError extends Error {
  constructor(message: string, readonly status = 400, readonly code = 'generation_job_invalid') { super(message); }
}

const MAX_MESSAGES = 50;
const MAX_MESSAGE_CHARS = 20_000;
const MAX_TOTAL_CHARS = 100_000;
const MAX_PENDING_PER_USER = 1;

function now(): number { return Math.floor(Date.now() / 1000); }
function admin() { return getSupabaseAdminClient(); }

export function validateGenerationMessages(value: unknown): GenerationMessage[] {
  if (!Array.isArray(value) || value.length === 0 || value.length > MAX_MESSAGES) {
    throw new GenerationJobError('messages must contain between 1 and 50 entries.');
  }
  let total = 0;
  const messages: GenerationMessage[] = [];
  for (const item of value) {
    if (!item || typeof item !== 'object') throw new GenerationJobError('Each message must be an object.');
    const { role, content } = item as Record<string, unknown>;
    if ((role !== 'system' && role !== 'user' && role !== 'assistant') || typeof content !== 'string' || !content.trim() || content.length > MAX_MESSAGE_CHARS) {
      throw new GenerationJobError('Each message requires a system, user, or assistant role and non-empty content of 20,000 characters or fewer.');
    }
    total += content.length;
    if (total > MAX_TOTAL_CHARS) throw new GenerationJobError('messages must be 100,000 characters or fewer in total.');
    messages.push({ role, content });
  }
  return messages;
}

function isArtifact(messages: GenerationMessage[]): boolean {
  const latest = messages[messages.length - 1]?.content || '';
  return /\b(build|create|generate|make|implement|write|develop)\b[\s\S]{0,120}\b(game|website|webpage|web page|site|web app|landing page|html|css|javascript|app|component|file)\b/i.test(latest);
}

export async function createGenerationJob(userId: string, rawMessages: unknown): Promise<GenerationJob> {
  const messages = validateGenerationMessages(rawMessages);
  const { count, error: countError } = await admin().from('temuclaude_generation_jobs').select('id', { count: 'exact', head: true }).eq('user_id', userId).in('status', ['queued', 'running', 'waiting_retry', 'validating', 'cancel_requested']);
  if (countError) throw new GenerationJobError('Generation job storage is unavailable.', 503, 'generation_storage_unavailable');
  if ((count || 0) >= MAX_PENDING_PER_USER) throw new GenerationJobError('You already have a maximum-quality task in progress.', 429, 'generation_pending_limit');
  const timestamp = now();
  const job: GenerationJob = {
    id: `gen_${crypto.randomUUID()}`, user_id: userId, request_kind: isArtifact(messages) ? 'artifact' : 'chat', messages,
    profile: 'maximum_quality', status: 'queued', stage: 'queued', attempt: 0, last_error_code: null,
    stage_results: {}, final_content: null, final_artifact: null, created_at: timestamp, updated_at: timestamp, completed_at: null,
  };
  const { error } = await admin().from('temuclaude_generation_jobs').insert(job);
  if (error) throw new GenerationJobError('Generation job storage is unavailable. Apply the durable-generation-jobs migration first.', 503, 'generation_storage_unavailable');
  await appendGenerationEvent(job.id, 'queued', 'created', { request_kind: job.request_kind });
  return job;
}

export async function appendGenerationEvent(jobId: string, stage: string, event: string, detail: Record<string, unknown> = {}): Promise<void> {
  const { error } = await admin().from('temuclaude_generation_job_events').insert({ job_id: jobId, stage, event, detail, created_at: now() });
  if (error) throw new GenerationJobError('Generation job event storage is unavailable.', 503, 'generation_storage_unavailable');
}

export async function getGenerationJobForUser(id: string, userId: string): Promise<GenerationJob | null> {
  const { data, error } = await admin().from('temuclaude_generation_jobs').select('*').eq('id', id).eq('user_id', userId).maybeSingle();
  if (error) throw new GenerationJobError('Generation job storage is unavailable.', 503, 'generation_storage_unavailable');
  return data as GenerationJob | null;
}

export async function requestGenerationJobCancellation(job: GenerationJob): Promise<GenerationJob> {
  if (['completed', 'failed', 'cancelled'].includes(job.status)) return job;
  const timestamp = now();
  const { data, error } = await admin().from('temuclaude_generation_jobs')
    .update({ status: 'cancel_requested', cancel_requested_at: timestamp, updated_at: timestamp })
    .eq('id', job.id).eq('user_id', job.user_id).select('*').single();
  if (error || !data) throw new GenerationJobError('Unable to cancel generation job.', 503, 'generation_storage_unavailable');
  await appendGenerationEvent(job.id, String(data.stage), 'cancel_requested');
  return data as GenerationJob;
}

export function publicGenerationJob(job: GenerationJob) {
  return {
    id: job.id, request_kind: job.request_kind, profile: job.profile, status: job.status, stage: job.stage,
    attempt: job.attempt, last_error_code: job.last_error_code, final_content: job.final_content,
    final_artifact: job.final_artifact, created_at: job.created_at, updated_at: job.updated_at, completed_at: job.completed_at,
  };
}

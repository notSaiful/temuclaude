import crypto from 'crypto';
import { getSupabaseAdminClient } from './supabase-server';
import { MEDIA_KINDS, type MediaKind, inferMediaKind } from './media-intent';

export { MEDIA_KINDS, inferMediaKind, type MediaKind } from './media-intent';
export type MediaJobStatus = 'queued' | 'processing' | 'completed' | 'failed';

export type MediaJob = {
  id: string;
  user_id: string;
  kind: MediaKind;
  prompt: string;
  status: MediaJobStatus;
  model: string;
  provider: 'aiml';
  provider_generation_id: string | null;
  output_url: string | null;
  output_mime_type: string | null;
  error_code: string | null;
  credits_reserved: number;
  credits_settled_at: number | null;
  created_at: number;
  updated_at: number;
};

type CreateMediaJobInput = {
  userId: string;
  kind: MediaKind;
  prompt: string;
  lyrics?: string;
  voice?: string;
};

const AIML_BASE = 'https://api.aimlapi.com';
const MAX_PROMPT_CHARS = 4_000;
const MAX_LYRICS_CHARS = 4_000;
const MAX_PENDING_PER_USER = 2;
const ASYNC_KINDS = new Set<MediaKind>(['video', 'music']);
const DEFAULT_MODELS: Record<MediaKind, string> = {
  image: process.env.AIML_IMAGE_MODEL || 'alibaba/z-image-turbo',
  video: process.env.AIML_VIDEO_MODEL || 'minimax/hailuo-2.3',
  speech: process.env.AIML_TTS_MODEL || 'openai/tts-1',
  music: process.env.AIML_MUSIC_MODEL || 'minimax/music-2.0',
};
const MEDIA_CREDIT_COSTS: Record<MediaKind, number> = {
  image: 2_500,
  speech: 1_000,
  music: 75_000,
  video: 125_000,
};


export class MediaJobError extends Error {
  constructor(message: string, readonly status = 400, readonly code = 'media_request_invalid') {
    super(message);
  }
}

function nowUnix(): number {
  return Math.floor(Date.now() / 1000);
}

function getAIMLKey(): string {
  const key = process.env.AIML_API_KEY?.trim();
  if (!key) throw new MediaJobError('Media generation is not configured yet.', 503, 'media_provider_unconfigured');
  return key;
}

function admin() {
  return getSupabaseAdminClient();
}

function providerHeaders(): HeadersInit {
  return { Authorization: `Bearer ${getAIMLKey()}`, 'Content-Type': 'application/json' };
}

function ensureUrl(value: unknown): string | null {
  if (typeof value !== 'string' || !value) return null;
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'https:' ? value : null;
  } catch {
    return null;
  }
}

function parseImageUrl(payload: Record<string, unknown>): string | null {
  const data = payload.data || payload.images;
  if (!Array.isArray(data) || data.length === 0 || typeof data[0] !== 'object' || data[0] === null) return null;
  return ensureUrl((data[0] as Record<string, unknown>).url);
}

function parseOutputUrl(payload: Record<string, unknown>): string | null {
  const candidates = [payload.url, payload.output, payload.audio, payload.video, payload.result];
  for (const candidate of candidates) {
    if (typeof candidate === 'object' && candidate !== null) {
      const record = candidate as Record<string, unknown>;
      const url = ensureUrl(record.url) || ensureUrl(record.audio_url) || ensureUrl(record.video_url);
      if (url) return url;
    }
    const direct = ensureUrl(candidate);
    if (direct) return direct;
  }
  return null;
}

function mediaMime(kind: MediaKind): string {
  return kind === 'image' ? 'image/*' : kind === 'video' ? 'video/*' : 'audio/*';
}

function safeProviderError(response: Response): Promise<never> {
  return response.text().then(() => {
    throw new MediaJobError('The media provider could not accept this request. Please try again later.', 502, 'media_provider_rejected');
  });
}

async function insertJob(job: MediaJob): Promise<MediaJob> {
  const { error } = await admin().from('temuclaude_media_jobs').insert(job);
  if (error) throw new MediaJobError('Media job storage is unavailable. Apply the media-jobs migration first.', 503, 'media_storage_unavailable');
  return job;
}

async function updateJob(id: string, changes: Partial<MediaJob>): Promise<MediaJob> {
  const { data, error } = await admin()
    .from('temuclaude_media_jobs')
    .update({ ...changes, updated_at: nowUnix() })
    .eq('id', id)
    .select('*')
    .single();
  if (error || !data) throw new MediaJobError('Media job storage is unavailable.', 503, 'media_storage_unavailable');
  return data as MediaJob;
}

async function reserveCredits(job: MediaJob): Promise<void> {
  const { data, error } = await admin().rpc('temuclaude_reserve_media_credits', {
    p_job_id: job.id, p_user_id: job.user_id, p_credits: MEDIA_CREDIT_COSTS[job.kind],
  });
  if (error) throw new MediaJobError('Media credit reservation is unavailable. Apply the media-jobs migration first.', 503, 'media_credit_reservation_unavailable');
  if (!data) throw new MediaJobError('Your current credit balance is too low for this media request.', 402, 'media_insufficient_credits');
}

async function settleCredits(job: MediaJob, success: boolean): Promise<void> {
  const { error } = await admin().rpc('temuclaude_settle_media_job', {
    p_job_id: job.id, p_user_id: job.user_id, p_success: success,
  });
  if (error) throw new MediaJobError('Media credit settlement is unavailable.', 503, 'media_credit_settlement_unavailable');
}

async function completeJob(job: MediaJob, outputUrl: string): Promise<MediaJob> {
  const completed = await updateJob(job.id, { status: 'completed', output_url: outputUrl, output_mime_type: mediaMime(job.kind) });
  // The output has already been produced. Do not turn a completed job into a
  // failed one if a transient ledger write is unavailable; a later poll can
  // retry settlement safely because the SQL function is idempotent.
  await settleCredits(completed, true).catch(() => undefined);
  return completed;
}

function validateInput(input: CreateMediaJobInput): void {
  if (!MEDIA_KINDS.includes(input.kind)) throw new MediaJobError('Unsupported media type.');
  if (!input.prompt.trim() || input.prompt.length > MAX_PROMPT_CHARS) {
    throw new MediaJobError(`Prompt must be between 1 and ${MAX_PROMPT_CHARS} characters.`);
  }
  if ((input.lyrics || '').length > MAX_LYRICS_CHARS) throw new MediaJobError(`Lyrics must be ${MAX_LYRICS_CHARS} characters or fewer.`);
}

async function enforcePendingLimit(userId: string): Promise<void> {
  const { count, error } = await admin()
    .from('temuclaude_media_jobs')
    .select('id', { count: 'exact', head: true })
    .eq('user_id', userId)
    .in('status', ['queued', 'processing']);
  if (error) throw new MediaJobError('Media job storage is unavailable.', 503, 'media_storage_unavailable');
  if ((count || 0) >= MAX_PENDING_PER_USER) {
    throw new MediaJobError('You already have two media jobs in progress. Wait for one to finish.', 429, 'media_pending_limit');
  }
}

async function submitProviderJob(job: MediaJob, input: CreateMediaJobInput): Promise<MediaJob> {
  const headers = providerHeaders();
  if (job.kind === 'image') {
    const response = await fetch(`${AIML_BASE}/v1/images/generations/`, {
      method: 'POST', headers,
      body: JSON.stringify({ model: job.model, prompt: input.prompt, n: 1, size: '1024x1024' }),
    });
    if (!response.ok) return safeProviderError(response);
    const outputUrl = parseImageUrl(await response.json() as Record<string, unknown>);
    if (!outputUrl) throw new MediaJobError('The image provider returned no usable image.', 502, 'media_provider_invalid_response');
    return completeJob(job, outputUrl);
  }
  if (job.kind === 'speech') {
    const response = await fetch(`${AIML_BASE}/v1/tts`, {
      method: 'POST', headers,
      body: JSON.stringify({ model: job.model, text: input.prompt, voice: input.voice || 'alloy', response_format: 'mp3', speed: 1 }),
    });
    if (!response.ok) return safeProviderError(response);
    const outputUrl = parseOutputUrl(await response.json() as Record<string, unknown>);
    if (!outputUrl) throw new MediaJobError('The speech provider returned no usable audio.', 502, 'media_provider_invalid_response');
    return completeJob(job, outputUrl);
  }
  const providerPath = job.kind === 'video' ? `video/${job.model.split('/')[0] || 'minimax'}/generation` : 'audio';
  const response = await fetch(`${AIML_BASE}/v2/generate/${providerPath}`, {
    method: 'POST', headers,
    body: JSON.stringify({ model: job.model, prompt: input.prompt, ...(input.lyrics?.trim() ? { lyrics: input.lyrics.trim() } : {}) }),
  });
  if (!response.ok) return safeProviderError(response);
  const payload = await response.json() as Record<string, unknown>;
  const outputUrl = parseOutputUrl(payload);
  if (outputUrl) return completeJob(job, outputUrl);
  const generationId = typeof payload.generation_id === 'string' ? payload.generation_id : typeof payload.id === 'string' ? payload.id : null;
  if (!generationId) throw new MediaJobError('The media provider returned no job identifier.', 502, 'media_provider_invalid_response');
  return updateJob(job.id, { status: 'processing', provider_generation_id: generationId });
}

export async function createMediaJob(input: CreateMediaJobInput): Promise<MediaJob> {
  validateInput(input);
  getAIMLKey();
  await enforcePendingLimit(input.userId);
  const now = nowUnix();
  const job: MediaJob = {
    id: `media_${crypto.randomUUID()}`,
    user_id: input.userId,
    kind: input.kind,
    prompt: input.prompt.trim(),
    status: 'queued',
    model: DEFAULT_MODELS[input.kind],
    provider: 'aiml',
    provider_generation_id: null,
    output_url: null,
    output_mime_type: null,
    error_code: null,
    credits_reserved: 0,
    credits_settled_at: null,
    created_at: now,
    updated_at: now,
  };
  await insertJob(job);
  try {
    await reserveCredits(job);
  } catch (error) {
    await updateJob(job.id, { status: 'failed', error_code: error instanceof MediaJobError ? error.code : 'media_credit_reservation_failed' }).catch(() => undefined);
    throw error;
  }
  try {
    return await submitProviderJob(job, input);
  } catch (error) {
    const code = error instanceof MediaJobError ? error.code : 'media_provider_failed';
    await updateJob(job.id, { status: 'failed', error_code: code }).catch(() => undefined);
    await settleCredits(job, false).catch(() => undefined);
    throw error;
  }
}

export async function getMediaJobForUser(id: string, userId: string): Promise<MediaJob | null> {
  const { data, error } = await admin().from('temuclaude_media_jobs').select('*').eq('id', id).eq('user_id', userId).maybeSingle();
  if (error) throw new MediaJobError('Media job storage is unavailable.', 503, 'media_storage_unavailable');
  return data as MediaJob | null;
}

export async function refreshMediaJob(job: MediaJob): Promise<MediaJob> {
  if (job.status === 'completed') {
    await settleCredits(job, true).catch(() => undefined);
    return job;
  }
  if (job.status === 'failed') {
    await settleCredits(job, false).catch(() => undefined);
    return job;
  }
  if (!ASYNC_KINDS.has(job.kind) || job.status !== 'processing' || !job.provider_generation_id) return job;
  const headers = providerHeaders();
  const endpoint = job.kind === 'video'
    ? `${AIML_BASE}/v2/generate/video/${job.model.split('/')[0] || 'minimax'}/generation?generation_id=${encodeURIComponent(job.provider_generation_id)}`
    : `${AIML_BASE}/v2/generate/audio/${encodeURIComponent(job.provider_generation_id)}`;
  const response = await fetch(endpoint, { headers, cache: 'no-store' });
  if (!response.ok) return job;
  const payload = await response.json() as Record<string, unknown>;
  const status = typeof payload.status === 'string' ? payload.status.toLowerCase() : 'processing';
  const outputUrl = parseOutputUrl(payload);
  if (outputUrl || ['completed', 'succeeded', 'success'].includes(status)) {
    if (outputUrl) return completeJob(job, outputUrl);
    const failed = await updateJob(job.id, { status: 'failed', error_code: 'media_provider_missing_output' });
    await settleCredits(failed, false);
    return failed;
  }
  if (['failed', 'cancelled', 'canceled', 'error'].includes(status)) {
    const failed = await updateJob(job.id, { status: 'failed', error_code: 'media_provider_failed' });
    await settleCredits(failed, false);
    return failed;
  }
  return job;
}

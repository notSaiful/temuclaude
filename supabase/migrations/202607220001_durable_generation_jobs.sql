-- Durable, owner-scoped jobs for maximum-quality text and code generation.
-- Workers claim a lease before changing a job so a retry cannot run a stage twice.
create table if not exists public.temuclaude_generation_jobs (
  id text primary key check (id ~ '^gen_[0-9a-fA-F-]{36}$'),
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  request_kind text not null check (request_kind in ('chat', 'artifact')),
  messages jsonb not null check (jsonb_typeof(messages) = 'array'),
  profile text not null default 'maximum_quality' check (profile = 'maximum_quality'),
  status text not null check (status in ('queued', 'running', 'waiting_retry', 'validating', 'completed', 'failed', 'cancel_requested', 'cancelled')),
  stage text not null check (stage in ('queued', 'panel', 'synthesis', 'artifact', 'sandbox_validation', 'qa', 'repair', 'finalizing', 'completed', 'failed', 'cancelled')),
  attempt integer not null default 0 check (attempt >= 0),
  lease_token text,
  lease_expires_at bigint,
  next_run_at bigint,
  cancel_requested_at bigint,
  last_error_code text,
  model_snapshot jsonb not null default '{}'::jsonb,
  stage_results jsonb not null default '{}'::jsonb,
  final_content text,
  final_artifact text,
  created_at bigint not null,
  updated_at bigint not null,
  completed_at bigint,
  check ((status = 'completed') = (final_content is not null) or status <> 'completed')
);

create index if not exists temuclaude_generation_jobs_user_updated_idx
  on public.temuclaude_generation_jobs(user_id, updated_at desc);
create index if not exists temuclaude_generation_jobs_recovery_idx
  on public.temuclaude_generation_jobs(status, lease_expires_at, next_run_at)
  where status in ('queued', 'running', 'waiting_retry', 'cancel_requested');

create table if not exists public.temuclaude_generation_job_events (
  id bigint generated always as identity primary key,
  job_id text not null references public.temuclaude_generation_jobs(id) on delete cascade,
  stage text not null,
  event text not null,
  detail jsonb not null default '{}'::jsonb,
  created_at bigint not null
);

create index if not exists temuclaude_generation_job_events_job_idx
  on public.temuclaude_generation_job_events(job_id, id asc);

alter table public.temuclaude_generation_jobs enable row level security;
alter table public.temuclaude_generation_job_events enable row level security;

create or replace function public.temuclaude_claim_generation_job(
  p_job_id text,
  p_lease_token text,
  p_lease_seconds bigint default 86370
) returns setof public.temuclaude_generation_jobs
language sql
security definer
set search_path = public
as $$
  update public.temuclaude_generation_jobs
  set status = 'running',
      stage = case when stage = 'queued' then 'panel' else stage end,
      attempt = attempt + 1,
      lease_token = p_lease_token,
      lease_expires_at = extract(epoch from now())::bigint + greatest(60, p_lease_seconds),
      updated_at = extract(epoch from now())::bigint
  where id = p_job_id
    and status in ('queued', 'waiting_retry')
    and (lease_expires_at is null or lease_expires_at < extract(epoch from now())::bigint)
  returning *;
$$;

revoke all on function public.temuclaude_claim_generation_job(text, text, bigint) from public;
grant execute on function public.temuclaude_claim_generation_job(text, text, bigint) to service_role;

-- The web app and Modal use the service role after authenticating the owner.
-- Browser clients receive only filtered DTOs from application routes.

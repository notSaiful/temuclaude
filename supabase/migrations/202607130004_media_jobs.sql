-- Persistent, owner-scoped media generation jobs. Provider credentials remain
-- server-side; browser clients only receive their own job metadata and output URL.
create table if not exists public.temuclaude_media_jobs (
  id text primary key check (id ~ '^media_[0-9a-fA-F-]{36}$'),
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  kind text not null check (kind in ('image', 'video', 'speech', 'music')),
  prompt text not null check (char_length(prompt) between 1 and 4000),
  status text not null check (status in ('queued', 'processing', 'completed', 'failed')),
  model text not null,
  provider text not null check (provider in ('aiml')),
  provider_generation_id text,
  output_url text,
  output_mime_type text,
  error_code text,
  credits_reserved bigint not null default 0 check (credits_reserved >= 0),
  credits_settled_at bigint,
  created_at bigint not null,
  updated_at bigint not null,
  check ((status = 'completed') = (output_url is not null) or status <> 'completed')
);

create index if not exists temuclaude_media_jobs_user_updated_idx
  on public.temuclaude_media_jobs(user_id, updated_at desc);
create index if not exists temuclaude_media_jobs_pending_idx
  on public.temuclaude_media_jobs(user_id, status)
  where status in ('queued', 'processing');

alter table public.temuclaude_media_jobs enable row level security;

-- The application uses the Supabase service key after authenticating the user
-- in Next.js. No browser-side direct table access is granted.

-- Atomically reserve a bounded number of product credits before a provider is
-- called. This prevents concurrent media requests from overspending a balance.
create or replace function public.temuclaude_reserve_media_credits(
  p_job_id text,
  p_user_id text,
  p_credits bigint
) returns boolean
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_credits <= 0 then return false; end if;
  update public.temuclaude_users
  set credit_balance = credit_balance - p_credits,
      updated_at = extract(epoch from now())::bigint
  where id = p_user_id and credit_balance >= p_credits;
  if not found then return false; end if;

  update public.temuclaude_media_jobs
  set credits_reserved = p_credits
  where id = p_job_id and user_id = p_user_id and status = 'queued' and credits_reserved = 0;
  if found then return true; end if;

  -- The job row unexpectedly disappeared; restore the balance before failing.
  update public.temuclaude_users
  set credit_balance = credit_balance + p_credits,
      updated_at = extract(epoch from now())::bigint
  where id = p_user_id;
  return false;
end;
$$;

create or replace function public.temuclaude_settle_media_job(
  p_job_id text,
  p_user_id text,
  p_success boolean
) returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  job public.temuclaude_media_jobs%rowtype;
begin
  select * into job from public.temuclaude_media_jobs
  where id = p_job_id and user_id = p_user_id
  for update;
  if not found or job.credits_settled_at is not null or job.credits_reserved <= 0 then return; end if;

  update public.temuclaude_media_jobs
  set credits_settled_at = extract(epoch from now())::bigint
  where id = job.id;

  if p_success then
    insert into public.temuclaude_usage_events (
      id, user_id, created_at, credits_spent, query_count, model_name, saved_usd
    ) values (
      'media_usage_' || job.id,
      job.user_id,
      extract(epoch from now())::bigint,
      job.credits_reserved,
      0,
      'media:' || job.kind || ':' || job.model,
      0
    ) on conflict (id) do nothing;
  else
    update public.temuclaude_users
    set credit_balance = credit_balance + job.credits_reserved,
        updated_at = extract(epoch from now())::bigint
    where id = job.user_id;
  end if;
end;
$$;

revoke all on function public.temuclaude_reserve_media_credits(text, text, bigint) from public;
revoke all on function public.temuclaude_settle_media_job(text, text, boolean) from public;
grant execute on function public.temuclaude_reserve_media_credits(text, text, bigint) to service_role;
grant execute on function public.temuclaude_settle_media_job(text, text, boolean) to service_role;

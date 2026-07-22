-- Expand the durable-job state machine after the initial production migration.
alter table public.temuclaude_generation_jobs
  drop constraint if exists temuclaude_generation_jobs_status_check;
alter table public.temuclaude_generation_jobs
  add constraint temuclaude_generation_jobs_status_check
  check (status in ('queued', 'running', 'waiting_retry', 'validating', 'needs_review', 'completed', 'failed', 'cancel_requested', 'cancelled'));

alter table public.temuclaude_generation_jobs
  drop constraint if exists temuclaude_generation_jobs_stage_check;
alter table public.temuclaude_generation_jobs
  add constraint temuclaude_generation_jobs_stage_check
  check (stage in ('queued', 'panel', 'synthesis', 'artifact', 'sandbox_validation', 'qa', 'repair', 'finalizing', 'completed', 'failed', 'cancelled', 'needs_review'));

create or replace function public.temuclaude_recover_generation_jobs(
  p_limit integer default 25
) returns setof public.temuclaude_generation_jobs
language sql
security definer
set search_path = public
as $$
  select * from public.temuclaude_generation_jobs
  where status in ('queued', 'waiting_retry')
     or (status = 'running' and lease_expires_at < extract(epoch from now())::bigint)
  order by updated_at asc
  limit greatest(1, least(p_limit, 100));
$$;

revoke all on function public.temuclaude_recover_generation_jobs(integer) from public;
grant execute on function public.temuclaude_recover_generation_jobs(integer) to service_role;

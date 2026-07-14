-- Accurate account usage requires event timestamps. Daily rollups cannot
-- represent a five-hour rolling window because they have no per-request time.

alter table public.temuclaude_users
  add column if not exists credit_balance bigint,
  add column if not exists credits_reset_at bigint,
  add column if not exists weekly_credit_allocation bigint;

-- The original constraint predates the Max tier. Replace it idempotently so
-- plans and their allocations stay in sync.
alter table public.temuclaude_users
  drop constraint if exists temuclaude_users_plan_check;
alter table public.temuclaude_users
  add constraint temuclaude_users_plan_check
  check (plan in ('free', 'developer', 'pro', 'max', 'enterprise'));

-- Preserve existing balances where possible. Older rows did not have a
-- weekly ledger, so give them the allocation for their current plan and begin
-- a predictable seven-day period from migration time.
update public.temuclaude_users
set weekly_credit_allocation = case plan
  when 'developer' then 1250000
  when 'pro' then 6000000
  when 'max' then 25000000
  when 'enterprise' then 75000000
  else 12500
end
where weekly_credit_allocation is null or weekly_credit_allocation <= 0;

update public.temuclaude_users
set credit_balance = weekly_credit_allocation
where credit_balance is null or credit_balance < 0;

update public.temuclaude_users
set credits_reset_at = extract(epoch from now())::bigint + 604800
where credits_reset_at is null or credits_reset_at <= 0;

alter table public.temuclaude_users
  alter column credit_balance set not null,
  alter column credits_reset_at set not null,
  alter column weekly_credit_allocation set not null;

create table if not exists public.temuclaude_usage_events (
  id text primary key,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  created_at bigint not null check (created_at > 0),
  credits_spent bigint not null default 0 check (credits_spent >= 0),
  query_count integer not null default 0 check (query_count >= 0),
  model_name text,
  saved_usd numeric(14, 8) not null default 0 check (saved_usd >= 0)
);

alter table public.temuclaude_usage_events
  add column if not exists model_name text,
  add column if not exists saved_usd numeric(14, 8) not null default 0;

create index if not exists temuclaude_usage_events_user_created_idx
  on public.temuclaude_usage_events(user_id, created_at asc);
create index if not exists temuclaude_usage_events_user_model_idx
  on public.temuclaude_usage_events(user_id, model_name)
  where model_name is not null;

alter table public.temuclaude_usage_events enable row level security;

comment on table public.temuclaude_usage_events is
  'Immutable per-request usage ledger. Five-hour capacity is calculated only from this table.';

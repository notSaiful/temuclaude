-- Upgrade installations where the event ledger was created before model and
-- savings analytics were introduced. Safe to run repeatedly.

alter table public.temuclaude_usage_events
  add column if not exists model_name text,
  add column if not exists saved_usd numeric(14, 8) not null default 0;

update public.temuclaude_usage_events
set saved_usd = 0
where saved_usd is null;

alter table public.temuclaude_usage_events
  alter column saved_usd set default 0,
  alter column saved_usd set not null;

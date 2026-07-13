-- Durable messages and stricter workflow-query support. Browser clients do
-- not access these tables directly; authenticated server routes use the
-- service role after verifying project ownership.

create table if not exists public.temuclaude_messages (
  id text primary key,
  project_id text not null references public.temuclaude_projects(id) on delete cascade,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  role text not null check (role in ('system', 'user', 'assistant', 'tool')),
  content text not null check (char_length(content) between 1 and 100000),
  metadata jsonb not null default '{}'::jsonb,
  created_at bigint not null
);

create index if not exists temuclaude_messages_project_created_idx
  on public.temuclaude_messages(project_id, created_at asc);
create index if not exists temuclaude_project_actions_user_status_idx
  on public.temuclaude_project_actions(user_id, status, created_at desc);
create index if not exists temuclaude_project_actions_expiry_idx
  on public.temuclaude_project_actions(expires_at)
  where status in ('requested', 'approved');

alter table public.temuclaude_messages enable row level security;

-- No browser policies: application user IDs intentionally differ from
-- auth.uid(). The Next.js API enforces ownership before service-role access.

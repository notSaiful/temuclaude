-- Persistent workspace data for Playground projects, generated files, and the
-- immutable activity trail shown in the Codex-style work log. These tables are
-- only accessed through the server with the Supabase service role; no browser
-- client receives direct table access.

create table if not exists public.temuclaude_projects (
  id text primary key,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  title text not null check (char_length(title) between 1 and 120),
  profile text not null default 'pro' check (profile in ('pro', 'lite')),
  status text not null default 'active' check (status in ('active', 'archived', 'deleted')),
  created_at bigint not null,
  updated_at bigint not null
);

create index if not exists temuclaude_projects_user_updated_idx
  on public.temuclaude_projects(user_id, updated_at desc);

create table if not exists public.temuclaude_project_files (
  id text primary key,
  project_id text not null references public.temuclaude_projects(id) on delete cascade,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  file_path text not null check (char_length(file_path) between 1 and 512),
  content text not null,
  language text,
  content_sha256 text not null,
  byte_size integer not null check (byte_size >= 0 and byte_size <= 1048576),
  created_at bigint not null,
  updated_at bigint not null,
  unique(project_id, file_path)
);

create index if not exists temuclaude_project_files_project_updated_idx
  on public.temuclaude_project_files(project_id, updated_at desc);

create table if not exists public.temuclaude_project_events (
  id text primary key,
  project_id text not null references public.temuclaude_projects(id) on delete cascade,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  event_type text not null check (char_length(event_type) between 1 and 80),
  summary text not null check (char_length(summary) between 1 and 280),
  details jsonb not null default '{}'::jsonb,
  created_at bigint not null
);

create index if not exists temuclaude_project_events_project_created_idx
  on public.temuclaude_project_events(project_id, created_at asc);

alter table public.temuclaude_projects enable row level security;
alter table public.temuclaude_project_files enable row level security;
alter table public.temuclaude_project_events enable row level security;

-- Deliberately no client-facing RLS policies. The product's application user
-- ids are distinct from auth.uid(), so direct browser access would be unsafe.
-- The authenticated Next.js API verifies ownership before each service-role
-- operation.

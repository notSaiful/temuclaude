-- Durable project history and approval records. All access remains through
-- authenticated server routes with service-role ownership checks.

create table if not exists public.temuclaude_project_artifacts (
  id text primary key,
  project_id text not null references public.temuclaude_projects(id) on delete cascade,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  artifact_kind text not null check (artifact_kind in ('source', 'html', 'image', 'video', 'audio', 'archive')),
  file_path text not null check (char_length(file_path) between 1 and 512),
  revision integer not null check (revision >= 1),
  content text not null,
  content_sha256 text not null,
  byte_size integer not null check (byte_size between 0 and 1048576),
  metadata jsonb not null default '{}'::jsonb,
  created_at bigint not null,
  unique(project_id, file_path, revision)
);

create index if not exists temuclaude_project_artifacts_project_created_idx
  on public.temuclaude_project_artifacts(project_id, created_at desc);

create table if not exists public.temuclaude_project_actions (
  id text primary key,
  project_id text not null references public.temuclaude_projects(id) on delete cascade,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  action_type text not null check (action_type in ('agent.run', 'package.install', 'network.enable', 'github.connect', 'deploy.preview', 'deploy.production')),
  status text not null check (status in ('requested', 'approved', 'rejected', 'executing', 'completed', 'failed', 'cancelled')),
  requested_payload jsonb not null default '{}'::jsonb,
  decision_payload jsonb not null default '{}'::jsonb,
  requested_at bigint not null,
  decided_at bigint,
  expires_at bigint not null,
  created_at bigint not null,
  updated_at bigint not null
);

create index if not exists temuclaude_project_actions_project_status_idx
  on public.temuclaude_project_actions(project_id, status, created_at desc);

alter table public.temuclaude_project_artifacts enable row level security;
alter table public.temuclaude_project_actions enable row level security;

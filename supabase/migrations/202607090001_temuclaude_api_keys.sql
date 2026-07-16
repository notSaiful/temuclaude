create table if not exists public.temuclaude_users (
  id text primary key,
  email text not null unique,
  name text,
  plan text not null default 'free' check (plan in ('free', 'developer', 'pro', 'enterprise')),
  razorpay_customer_id text,
  created_at bigint not null,
  updated_at bigint not null
);

create table if not exists public.temuclaude_api_keys (
  id text primary key,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  key_hash text not null unique,
  key_prefix text not null,
  name text not null default 'default',
  last_used bigint,
  created_at bigint not null
);

create index if not exists temuclaude_api_keys_user_id_idx
  on public.temuclaude_api_keys(user_id);

create table if not exists public.temuclaude_usage (
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  query_date date not null,
  query_count integer not null default 0,
  input_tokens integer not null default 0,
  output_tokens integer not null default 0,
  primary key (user_id, query_date)
);

create table if not exists public.temuclaude_subscriptions (
  id text primary key,
  user_id text not null references public.temuclaude_users(id) on delete cascade,
  razorpay_subscription_id text not null unique,
  razorpay_plan_id text not null,
  plan text not null,
  status text not null,
  current_period_start bigint,
  current_period_end bigint,
  created_at bigint not null,
  updated_at bigint not null
);

create table if not exists public.temuclaude_payments (
  id text primary key,
  user_id text references public.temuclaude_users(id) on delete set null,
  razorpay_order_id text not null,
  razorpay_payment_id text,
  razorpay_signature text,
  amount integer not null,
  currency text not null default 'INR',
  status text not null,
  type text not null,
  plan text,
  created_at bigint not null
);

alter table public.temuclaude_users enable row level security;
alter table public.temuclaude_api_keys enable row level security;
alter table public.temuclaude_usage enable row level security;
alter table public.temuclaude_subscriptions enable row level security;
alter table public.temuclaude_payments enable row level security;

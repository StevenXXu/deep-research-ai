-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. PROFILES TABLE (Syncs with Clerk)
create table public.profiles (
  user_id text primary key, -- Matches Clerk User ID
  email text not null,
  full_name text,
  credits_remaining int default 3, -- Free Trial: 3 credits
  subscription_status text default 'free', -- free, pro, enterprise
  stripe_customer_id text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. REPORTS TABLE (Stores generated analysis)
create table public.reports (
  id uuid default uuid_generate_v4() primary key,
  user_id text references public.profiles(user_id) not null,
  target_url text not null,
  status text default 'queued', -- queued, processing, completed, failed
  report_content text, -- The Markdown content
  pdf_url text, -- Optional S3 link
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. RLS POLICIES (Security)
alter table public.profiles enable row level security;
alter table public.reports enable row level security;

-- Users can only read their own profile
create policy "Users can view own profile" on public.profiles
  for select using (auth.uid()::text = user_id);

-- Users can only read/insert their own reports
create policy "Users can view own reports" on public.reports
  for select using (auth.uid()::text = user_id);

create policy "Users can insert own reports" on public.reports
  for insert with check (auth.uid()::text = user_id);

-- SERVICE ROLE (Backend) can do everything (Bypass RLS)
-- Note: Supabase Service Key bypasses RLS automatically.
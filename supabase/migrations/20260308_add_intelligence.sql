-- 1. Profiles Table: Add Role (Admin/User)
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS role text DEFAULT 'user';

-- 2. Reports Table: Add Intelligence & Cost Fields
ALTER TABLE public.reports 
ADD COLUMN IF NOT EXISTS company_name text,
ADD COLUMN IF NOT EXISTS sector_tags text[], -- Array of strings e.g. ['AI', 'SaaS']
ADD COLUMN IF NOT EXISTS cost_usd numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS usage_meta jsonb DEFAULT '{}'; 
-- usage_meta example: { "exa_calls": 5, "llm_tokens": 4000, "apify_runs": 1 }

-- 3. Security: Admin Access Policies
-- Allow Admins to read ALL reports (for Dashboard)
CREATE POLICY "Admins can view all reports" ON public.reports
    FOR SELECT
    USING (
        (SELECT role FROM public.profiles WHERE user_id = auth.uid()::text) = 'admin'
    );

-- Allow Admins to read ALL profiles (for User Management)
CREATE POLICY "Admins can view all profiles" ON public.profiles
    FOR SELECT
    USING (
        (SELECT role FROM public.profiles WHERE user_id = auth.uid()::text) = 'admin'
    );

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY; // Optional Admin Key

// Default Client (For Frontend)
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Admin Client (For API Routes - Bypasses RLS)
export const supabaseAdmin = supabaseServiceKey 
    ? createClient(supabaseUrl, supabaseServiceKey) 
    : supabase;
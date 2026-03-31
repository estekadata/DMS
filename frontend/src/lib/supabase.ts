import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Client-side Supabase client (used in React components)
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// For server-side direct DB access (API routes), we use the DB URL
export const DB_URL = process.env.SUPABASE_DB_URL;

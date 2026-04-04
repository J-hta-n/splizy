import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

let client: SupabaseClient | null = null;
if (supabaseUrl && supabaseKey) {
  client = createClient(supabaseUrl, supabaseKey, {
    auth: { persistSession: false },
  });
} else if (
  typeof process !== "undefined" &&
  process.env.NODE_ENV !== "production"
) {
  console.warn(
    "SUPABASE_URL or SUPABASE_KEY is not configured. API routes will fail until these environment variables are set.",
  );
}

export const supabase = client;

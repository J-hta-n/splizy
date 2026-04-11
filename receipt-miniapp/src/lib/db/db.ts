import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { env } from "@/lib/config";

const supabaseUrl = env.SUPABASE_URL;
const supabaseKey = env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error(
    "Database is not configured. Set SUPABASE_URL and SUPABASE_KEY environment variables.",
  );
}

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseKey, {
  auth: { persistSession: false },
});

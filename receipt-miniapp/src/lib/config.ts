export const env = {
  SUPABASE_URL: process.env.SUPABASE_URL,
  SUPABASE_KEY: process.env.SUPABASE_KEY,
  MOCK_RECEIPTS_API: process.env.MOCK_RECEIPTS_API?.toLowerCase() == "true",
} as const;

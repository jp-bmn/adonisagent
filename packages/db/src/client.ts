/**
 * Supabase client factories.
 *
 * Two flavors:
 *   - createBrowserClient(): public anon key, RLS enforced. Used in the Next.js client.
 *   - createServerClient(): service-role key, full access. Used in agent workers only.
 *
 * NEVER use the service-role client in browser-shipped code.
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_KEY;
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_KEY;

if (!url) {
  throw new Error('SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL is not set');
}

export function createBrowserClient(): SupabaseClient {
  if (!anonKey) {
    throw new Error('NEXT_PUBLIC_SUPABASE_ANON_KEY is not set');
  }
  return createClient(url!, anonKey);
}

export function createServerClient(): SupabaseClient {
  if (!serviceKey) {
    throw new Error(
      'SUPABASE_SERVICE_ROLE_KEY is not set — required for server / agent operations'
    );
  }
  return createClient(url!, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

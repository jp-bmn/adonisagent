'use server';

import { createClient } from '@/utils/supabase/server';

export async function getAuthTokenAction() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token;
}

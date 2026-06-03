import type { Hospital, Signal, Contact, Rep, Digest, SignalPriority } from '@adonis/shared';
import type { SupabaseClient } from '@supabase/supabase-js';

/**
 * High-level query helpers. The web app and agents both use these.
 * Keeping queries here means schema changes update in one place.
 */

export async function listHospitals(db: SupabaseClient): Promise<Hospital[]> {
  const { data, error } = await db.from('hospitals').select('*').order('display_name');
  if (error) throw error;
  return data ?? [];
}

export async function getHospital(db: SupabaseClient, id: string): Promise<Hospital | null> {
  const { data, error } = await db.from('hospitals').select('*').eq('id', id).maybeSingle();
  if (error) throw error;
  return data;
}

export async function listContactsForHospital(
  db: SupabaseClient,
  hospitalId: string
): Promise<Contact[]> {
  const { data, error } = await db
    .from('contacts')
    .select('*')
    .eq('hospital_id', hospitalId)
    .order('role');
  if (error) throw error;
  return data ?? [];
}

interface ListSignalsOptions {
  hospitalIds?: string[];
  priority?: SignalPriority | SignalPriority[];
  since?: Date;
  limit?: number;
}

export async function listSignals(
  db: SupabaseClient,
  opts: ListSignalsOptions = {}
): Promise<Signal[]> {
  let q = db.from('signals').select('*').order('detected_at', { ascending: false });
  if (opts.hospitalIds && opts.hospitalIds.length > 0) {
    q = q.in('hospital_id', opts.hospitalIds);
  }
  if (opts.priority) {
    const priorities = Array.isArray(opts.priority) ? opts.priority : [opts.priority];
    q = q.in('priority', priorities);
  }
  if (opts.since) {
    q = q.gte('detected_at', opts.since.toISOString());
  }
  if (opts.limit) {
    q = q.limit(opts.limit);
  }
  const { data, error } = await q;
  if (error) throw error;
  return data ?? [];
}

export async function listHospitalsForUser(
  db: SupabaseClient,
  userId: string
): Promise<Hospital[]> {
  // Admin sees everything; AEs see only their assigned hospitals.
  const { data: user, error: ue } = await db
    .from('users')
    .select('role')
    .eq('id', userId)
    .single();
  if (ue) throw ue;

  if (user.role === 'admin') {
    return listHospitals(db);
  }

  const { data, error } = await db
    .from('user_hospitals')
    .select('hospitals(*)')
    .eq('user_id', userId);
  if (error) throw error;
  // @ts-expect-error - supabase typing through joins
  return (data ?? []).map((row) => row.hospitals);
}

export async function insertSignal(
  db: SupabaseClient,
  signal: Omit<Signal, 'id' | 'created_at' | 'updated_at'>
): Promise<Signal> {
  const { data, error } = await db.from('signals').insert(signal).select().single();
  if (error) throw error;
  return data;
}

import { NextResponse } from 'next/server';

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY!;

const HOSPITAL_NAMES: Record<string, string> = {
  'a4725891-7354-4187-a6c1-93d7ea9a078f': 'Ascension',
  '7b836e62-3ee8-4d10-b30e-028734a5f812': 'CommonSpirit Health',
  'a17f653f-8479-4159-9149-63e65d2d50a2': 'Jefferson Health',
  'f0f6b915-3e9d-4040-ba4d-c89339a1e134': 'NewYork-Presbyterian',
  'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476': 'UMass Memorial',
  '3aebd89a-1d2c-465c-a22b-08ced9613027': 'University of Arkansas Medical Sciences',
};

export async function GET() {
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    return NextResponse.json([]);
  }
  try {
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/contacts?is_active=eq.false&order=created_at.desc`,
      {
        headers: {
          apikey: SUPABASE_KEY,
          Authorization: `Bearer ${SUPABASE_KEY}`,
        },
      }
    );
    const contacts = await res.json();
    const enriched = contacts.map((c: { hospital_id: string }) => ({
      ...c,
      hospital_name: HOSPITAL_NAMES[c.hospital_id] ?? 'Unknown',
    }));
    return NextResponse.json(enriched);
  } catch {
    return NextResponse.json([]);
  }
}

import { NextResponse } from 'next/server';

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY!;

const HOSPITAL_ORDER: Record<string, number> = {
  'a4725891-7354-4187-a6c1-93d7ea9a078f': 0, // Ascension
  '7b836e62-3ee8-4d10-b30e-028734a5f812': 1, // CommonSpirit Health
  'a17f653f-8479-4159-9149-63e65d2d50a2': 2, // Jefferson Health
  'f0f6b915-3e9d-4040-ba4d-c89339a1e134': 3, // NewYork-Presbyterian
  'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476': 4, // UMass Memorial
  '3aebd89a-1d2c-465c-a22b-08ced9613027': 5, // University of Arkansas Medical Sciences
};

const HOSPITAL_NAMES: Record<string, string> = {
  'a4725891-7354-4187-a6c1-93d7ea9a078f': 'Ascension',
  '7b836e62-3ee8-4d10-b30e-028734a5f812': 'CommonSpirit Health',
  'a17f653f-8479-4159-9149-63e65d2d50a2': 'Jefferson Health',
  'f0f6b915-3e9d-4040-ba4d-c89339a1e134': 'NewYork-Presbyterian',
  'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476': 'UMass Memorial',
  '3aebd89a-1d2c-465c-a22b-08ced9613027': 'University of Arkansas Medical Sciences',
};

const ROLE_ORDER: Record<string, number> = {
  ceo: 0,
  cfo: 1,
  cro: 2,
  'vp revenue cycle': 3,
};

function roleOrder(role: string): number {
  const r = role.toLowerCase();
  if (r.includes('chief executive') || r === 'ceo') return 0;
  if (r.includes('chief financial') || r === 'cfo') return 1;
  if (r.includes('chief revenue') || r === 'cro') return 2;
  if (r.includes('revenue cycle')) return 3;
  return ROLE_ORDER[r] ?? 99;
}

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
    const enriched = contacts.map((c: { hospital_id: string; role: string }) => ({
      ...c,
      hospital_name: HOSPITAL_NAMES[c.hospital_id] ?? 'Unknown',
    }));

    enriched.sort(
      (a: { hospital_id: string; role: string }, b: { hospital_id: string; role: string }) => {
        const hospitalDiff =
          (HOSPITAL_ORDER[a.hospital_id] ?? 99) - (HOSPITAL_ORDER[b.hospital_id] ?? 99);
        if (hospitalDiff !== 0) return hospitalDiff;
        return roleOrder(a.role) - roleOrder(b.role);
      }
    );

    return NextResponse.json(enriched);
  } catch {
    return NextResponse.json([]);
  }
}

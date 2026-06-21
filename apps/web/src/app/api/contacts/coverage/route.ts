import { NextResponse } from 'next/server';

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY!;

const HOSPITALS = [
  { id: 'a4725891-7354-4187-a6c1-93d7ea9a078f', name: 'Ascension' },
  { id: '7b836e62-3ee8-4d10-b30e-028734a5f812', name: 'CommonSpirit Health' },
  { id: 'a17f653f-8479-4159-9149-63e65d2d50a2', name: 'Jefferson Health' },
  { id: 'f0f6b915-3e9d-4040-ba4d-c89339a1e134', name: 'NewYork-Presbyterian' },
  { id: 'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476', name: 'UMass Memorial' },
  { id: '3aebd89a-1d2c-465c-a22b-08ced9613027', name: 'University of Arkansas Medical Sciences' },
];

const ROLES = ['CEO', 'CFO', 'CRO', 'VP Revenue Cycle'];

function matchRole(role: string): string | null {
  const r = role.toLowerCase();
  if (
    r.includes('chief executive') ||
    r === 'ceo' ||
    r.includes('president and ceo') ||
    r.includes('president & chief executive')
  )
    return 'CEO';
  if (r.includes('chief financial') || r === 'cfo' || r.includes('evp & cfo')) return 'CFO';
  if (r.includes('chief revenue') || r === 'cro' || (r.includes('revenue') && r.includes('cro')))
    return 'CRO';
  if (
    r.includes('revenue cycle') &&
    (r.includes('vp') || r.includes('vice president') || r.includes('svp'))
  )
    return 'VP Revenue Cycle';
  return null;
}

export async function GET() {
  const res = await fetch(
    `${SUPABASE_URL}/rest/v1/contacts?select=full_name,role,hospital_id,is_active,linkedin_url`,
    { headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` } }
  );
  const all = (await res.json()) as {
    full_name: string;
    role: string;
    hospital_id: string;
    is_active: boolean;
    linkedin_url: string | null;
  }[];

  const coverage = HOSPITALS.map((hospital) => {
    const hospitalContacts = all.filter((c) => c.hospital_id === hospital.id);

    const roles = ROLES.map((roleLabel) => {
      const active = hospitalContacts.find((c) => c.is_active && matchRole(c.role) === roleLabel);
      const pending = !active
        ? hospitalContacts.find((c) => !c.is_active && matchRole(c.role) === roleLabel)
        : null;

      return {
        role: roleLabel,
        status: active ? 'filled' : pending ? 'pending' : 'missing',
        name: active?.full_name ?? pending?.full_name ?? null,
        linkedin_url: active?.linkedin_url ?? null,
      };
    });

    return { id: hospital.id, name: hospital.name, roles };
  });

  return NextResponse.json(coverage);
}

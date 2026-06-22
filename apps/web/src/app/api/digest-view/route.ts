import { NextRequest, NextResponse } from 'next/server';

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY!;
const RAILWAY_URL = 'https://adonisagents-production.up.railway.app/api/v1';

export async function POST(req: NextRequest) {
  const { ae_id, digest_id } = await req.json();

  if (!ae_id) return NextResponse.json({ error: 'ae_id required' }, { status: 400 });

  // Store in Supabase (upsert by ae_id — keeps only the latest view per AE)
  if (SUPABASE_URL && SUPABASE_KEY) {
    await fetch(`${SUPABASE_URL}/rest/v1/digest_views`, {
      method: 'POST',
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        'Content-Type': 'application/json',
        Prefer: 'resolution=merge-duplicates',
      },
      body: JSON.stringify({
        ae_id,
        digest_id: digest_id ?? null,
        viewed_at: new Date().toISOString(),
      }),
    }).catch(() => {});
  }

  // Also fire Joel's endpoint (fails silently if not live yet)
  fetch(`${RAILWAY_URL}/digest-views`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-Id': ae_id },
    body: JSON.stringify({ digest_id: digest_id ?? null }),
  }).catch(() => {});

  return NextResponse.json({ ok: true });
}

export async function GET() {
  if (!SUPABASE_URL || !SUPABASE_KEY) return NextResponse.json([]);

  const res = await fetch(
    `${SUPABASE_URL}/rest/v1/digest_views?select=ae_id,viewed_at,digest_id&order=viewed_at.desc`,
    {
      headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` },
    }
  );

  if (!res.ok) return NextResponse.json([]);
  const data = await res.json();
  return NextResponse.json(Array.isArray(data) ? data : []);
}

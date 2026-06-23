import { NextResponse } from 'next/server';

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY!;
const SERPER_API_KEY = process.env.SERPER_API_KEY!;
const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY!;

const HOSPITALS = [
  { id: 'a4725891-7354-4187-a6c1-93d7ea9a078f', name: 'Ascension', domain: 'ascension.org' },
  {
    id: '7b836e62-3ee8-4d10-b30e-028734a5f812',
    name: 'CommonSpirit Health',
    domain: 'commonspirithealth.org',
  },
  {
    id: 'a17f653f-8479-4159-9149-63e65d2d50a2',
    name: 'Jefferson Health',
    domain: 'jeffersonhealth.org',
  },
  { id: 'f0f6b915-3e9d-4040-ba4d-c89339a1e134', name: 'NewYork-Presbyterian', domain: 'nyp.org' },
  {
    id: 'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476',
    name: 'UMass Memorial',
    domain: 'umassmemorial.org',
  },
  {
    id: '3aebd89a-1d2c-465c-a22b-08ced9613027',
    name: 'University of Arkansas Medical Sciences',
    domain: 'uams.edu',
  },
];

const ROLES = [
  { title: 'CEO', keywords: 'Chief Executive Officer' },
  { title: 'CFO', keywords: 'Chief Financial Officer' },
  { title: 'CRO', keywords: 'Chief Revenue Officer' },
  { title: 'VP Revenue Cycle', keywords: 'Vice President Revenue Cycle' },
];

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

const serperCache = new Map<string, { title: string; link: string; snippet: string }[]>();

async function searchSerper(query: string) {
  if (serperCache.has(query)) return serperCache.get(query)!;
  try {
    const res = await fetch('https://google.serper.dev/search', {
      method: 'POST',
      headers: { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: query, num: 5 }),
    });
    const data = await res.json();
    const results = (data.organic || []) as { title: string; link: string; snippet: string }[];
    serperCache.set(query, results);
    return results;
  } catch {
    return [];
  }
}

async function multiLaneSearch(hospital: (typeof HOSPITALS)[0], role: (typeof ROLES)[0]) {
  const { title, keywords } = role;
  const allResults: {
    lane: string;
    results: { title: string; link: string; snippet: string }[];
  }[] = [];

  const [l1, l2, l3, l4, l5] = await Promise.all([
    searchSerper(`"${hospital.name}" "${keywords}" site:linkedin.com/in`),
    searchSerper(`"${hospital.name}" "appoints" OR "names" "${keywords}" OR "${title}"`),
    searchSerper(
      `"${hospital.name}" "${title}" site:beckershospitalreview.com OR site:modernhealthcare.com OR site:fiercehealthcare.com`
    ),
    searchSerper(
      `site:${hospital.domain} leadership OR "executive team" "${title}" OR "${keywords}"`
    ),
    searchSerper(`"${hospital.name}" current "${keywords}" 2024 OR 2025 OR 2026`),
  ]);

  if (l1.length) allResults.push({ lane: 'LinkedIn', results: l1 });
  if (l2.length) allResults.push({ lane: 'Press Release', results: l2 });
  if (l3.length) allResults.push({ lane: 'Healthcare News', results: l3 });
  if (l4.length) allResults.push({ lane: 'Hospital Website', results: l4 });
  if (l5.length) allResults.push({ lane: 'General Search', results: l5 });

  return allResults;
}

async function verifyWithClaude(
  hospital: (typeof HOSPITALS)[0],
  role: (typeof ROLES)[0],
  laneResults: { lane: string; results: { title: string; link: string; snippet: string }[] }[]
) {
  const formatted = laneResults
    .map(({ lane, results }) => {
      const snippets = results
        .slice(0, 3)
        .map((r) => `  - ${r.title} | ${r.link}\n    ${r.snippet || ''}`)
        .join('\n');
      return `[${lane}]\n${snippets}`;
    })
    .join('\n\n');

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 768,
      messages: [
        {
          role: 'user',
          content: `You are verifying the current ${role.title} (${role.keywords}) of ${hospital.name}.

Search results from 5 sources:

${formatted}

Identify the most likely current ${role.title} of ${hospital.name}.
- Look for name consensus across multiple lanes
- Prefer recent appointments (2024-2026)
- A LinkedIn /in/ URL is a strong signal

Respond ONLY with valid JSON:
{
  "full_name": "First Last",
  "role": "${role.title}",
  "linkedin_url": "https://www.linkedin.com/in/..." or null,
  "prior_employer": "previous company" or null,
  "confidence": 0.0,
  "sources_agreed": 0,
  "reasoning": "one sentence"
}

Rules:
- linkedin_url must be /in/ format only
- confidence: 0.9+ if 3+ lanes agree, 0.7-0.9 if 2 lanes agree, 0.5-0.7 if 1 strong source, below 0.5 if uncertain
- If uncertain, set confidence below 0.5`,
        },
      ],
    }),
  });

  const data = await res.json();
  const text = data?.content?.[0]?.text ?? '';
  try {
    const json = text.match(/\{[\s\S]*\}/)?.[0];
    const parsed = JSON.parse(json ?? 'null');
    if (!parsed) throw new Error('Null JSON');
    return parsed;
  } catch {
    return {
      full_name: '—',
      role: role.title,
      linkedin_url: null,
      prior_employer: null,
      confidence: 0,
      sources_agreed: 0,
      reasoning: 'Failed to parse LLM response',
    };
  }
}

async function getActiveContacts() {
  const res = await fetch(
    `${SUPABASE_URL}/rest/v1/contacts?is_active=eq.true&select=hospital_id,role`,
    {
      headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` },
    }
  );
  return (await res.json()) as { hospital_id: string; role: string }[];
}

async function upsertContact(
  hospitalId: string,
  contact: {
    full_name: string;
    role: string;
    linkedin_url: string | null;
    prior_employer: string | null;
    reasoning: string;
  },
  pending: boolean
) {
  const checkRes = await fetch(
    `${SUPABASE_URL}/rest/v1/contacts?hospital_id=eq.${hospitalId}&role=eq.${encodeURIComponent(contact.role)}&select=id,is_active`,
    { headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` } }
  );
  const existing = await checkRes.json();

  if (existing.length > 0 && existing[0].is_active && pending) return 'skipped';

  if (existing.length > 0) {
    await fetch(`${SUPABASE_URL}/rest/v1/contacts?id=eq.${existing[0].id}`, {
      method: 'PATCH',
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        full_name: contact.full_name,
        linkedin_url: contact.linkedin_url,
        prior_employer: contact.prior_employer,
        linkedin_verified: !!contact.linkedin_url,
        is_active: !pending,
        review_note: contact.reasoning,
        updated_at: new Date().toISOString(),
      }),
    });
    return pending ? 'pending' : 'updated';
  } else {
    await fetch(`${SUPABASE_URL}/rest/v1/contacts`, {
      method: 'POST',
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        hospital_id: hospitalId,
        full_name: contact.full_name,
        role: contact.role,
        linkedin_url: contact.linkedin_url,
        prior_employer: contact.prior_employer,
        linkedin_verified: !!contact.linkedin_url,
        is_active: !pending,
        review_note: contact.reasoning,
      }),
    });
    return pending ? 'pending' : 'inserted';
  }
}

export async function POST() {
  if (!ANTHROPIC_API_KEY || !SERPER_API_KEY || !SUPABASE_URL || !SUPABASE_KEY) {
    return NextResponse.json({ error: 'Missing env vars' }, { status: 500 });
  }

  const activeContacts = await getActiveContacts();
  const activeSet = new Set(activeContacts.map((c) => `${c.hospital_id}::${c.role.toLowerCase()}`));

  // Flatten iterations
  const searchTasks: { hospital: (typeof HOSPITALS)[0]; role: (typeof ROLES)[0] }[] = [];
  for (const hospital of HOSPITALS) {
    for (const role of ROLES) {
      const key = `${hospital.id}::${role.title.toLowerCase()}`;
      if (!activeSet.has(key)) {
        searchTasks.push({ hospital, role });
      }
    }
  }

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const promises = searchTasks.map(async ({ hospital, role }, index) => {
          // Stagger starts heavily to prevent 429 rate limit
          await sleep(index * 2000);

          const laneResults = await multiLaneSearch(hospital, role);
          if (!laneResults.length) {
            const res = {
              hospital: hospital.name,
              role: role.title,
              name: '—',
              action: 'no results',
              confidence: 0,
            };
            controller.enqueue(encoder.encode(`data: ${JSON.stringify(res)}\n\n`));
            return res;
          }

          const contact = await verifyWithClaude(hospital, role, laneResults);
          if (!contact || contact.confidence < 0.3) {
            const res = {
              hospital: hospital.name,
              role: role.title,
              name: contact?.full_name ?? '—',
              action: 'skipped (low confidence)',
              confidence: contact?.confidence ?? 0,
            };
            controller.enqueue(encoder.encode(`data: ${JSON.stringify(res)}\n\n`));
            return res;
          }

          const isPending = contact.confidence < 0.55;
          const action = await upsertContact(hospital.id, contact, isPending);
          const res = {
            hospital: hospital.name,
            role: role.title,
            name: contact.full_name,
            action,
            confidence: contact.confidence,
          };
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(res)}\n\n`));
          return res;
        });

        await Promise.all(promises);
        controller.enqueue(encoder.encode(`data: [DONE]\n\n`));
      } catch (err) {
        console.error(err);
      } finally {
        controller.close();
      }
    },
  });

  return new NextResponse(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}

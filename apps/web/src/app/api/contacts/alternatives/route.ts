import { NextRequest, NextResponse } from 'next/server';

const SERPER_API_KEY = process.env.SERPER_API_KEY!;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY!;

const HOSPITAL_DOMAINS: Record<string, string> = {
  Ascension: 'ascension.org',
  'CommonSpirit Health': 'commonspirithealth.org',
  'Jefferson Health': 'jeffersonhealth.org',
  'NewYork-Presbyterian': 'nyp.org',
  'UMass Memorial': 'umassmemorial.org',
  'University of Arkansas Medical Sciences': 'uams.edu',
};

async function search(query: string) {
  const res = await fetch('https://google.serper.dev/search', {
    method: 'POST',
    headers: { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ q: query, num: 5 }),
  });
  const data = await res.json();
  return (data.organic || []) as { title: string; link: string; snippet: string }[];
}

export async function POST(req: NextRequest) {
  const { hospital_name, role } = await req.json();
  const domain = HOSPITAL_DOMAINS[hospital_name] ?? '';

  // 4 alternative search strategies
  const [r1, r2, r3, r4] = await Promise.all([
    search(`"${hospital_name}" "${role}" 2025 OR 2026 leadership`),
    search(`site:${domain} "${role}" OR "leadership team"`),
    search(
      `"${hospital_name}" "${role}" site:beckershospitalreview.com OR site:modernhealthcare.com`
    ),
    search(`"${hospital_name}" "appoints" OR "names" OR "hires" "${role}" 2024 OR 2025 OR 2026`),
  ]);

  const allSnippets = [
    { lane: 'Recent News', results: r1 },
    { lane: 'Hospital Website', results: r2 },
    { lane: 'Healthcare Press', results: r3 },
    { lane: 'Appointment Announcements', results: r4 },
  ]
    .map(({ lane, results }) => {
      const text = results
        .slice(0, 3)
        .map((r) => `  - ${r.title} | ${r.link}\n    ${r.snippet || ''}`)
        .join('\n');
      return `[${lane}]\n${text}`;
    })
    .join('\n\n');

  const msg = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: `Find the current ${role} of ${hospital_name}. Search results from 4 sources:

${allSnippets}

Return up to 3 distinct candidate people for this role. For each, provide evidence from the search results.

Respond ONLY with valid JSON array:
[
  {
    "full_name": "First Last",
    "linkedin_url": "https://www.linkedin.com/in/..." or null,
    "prior_employer": "previous company" or null,
    "confidence": 0.0,
    "evidence": "one sentence explaining why this person"
  }
]

Rules:
- Only include real people explicitly mentioned in the search results
- linkedin_url must be /in/ format only
- Order by confidence descending
- If only 1 person found, return array with 1 item
- If no one found, return empty array []`,
        },
      ],
    }),
  });

  const data = await msg.json();
  const text = data?.content?.[0]?.text ?? '[]';
  try {
    const json = text.match(/\[[\s\S]*\]/)?.[0];
    const candidates = JSON.parse(json ?? '[]');
    return NextResponse.json(candidates);
  } catch {
    return NextResponse.json([]);
  }
}

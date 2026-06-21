import { NextRequest, NextResponse } from 'next/server';

const SERPER_API_KEY = process.env.SERPER_API_KEY!;

async function search(query: string) {
  const res = await fetch('https://google.serper.dev/search', {
    method: 'POST',
    headers: { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ q: query, num: 5 }),
  });
  const data = await res.json();
  return (data.organic || []) as { title: string; link: string; snippet: string }[];
}

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return url;
  }
}

export async function POST(req: NextRequest) {
  const { title, hospital_name } = await req.json();

  const [r1, r2, r3] = await Promise.all([
    search(
      `"${hospital_name}" ${title} site:beckershospitalreview.com OR site:modernhealthcare.com OR site:fiercehealthcare.com`
    ),
    search(`"${hospital_name}" ${title} site:healthcarefinancenews.com OR site:healthsystemcio.com OR site:healthcareitnews.com`),
    search(`"${hospital_name}" ${title} -site:linkedin.com -site:facebook.com`),
  ]);

  const seen = new Set<string>();
  const results: { title: string; url: string; snippet: string; source: string }[] = [];

  for (const r of [...r1, ...r2, ...r3]) {
    if (seen.has(r.link)) continue;
    seen.add(r.link);
    results.push({
      title: r.title,
      url: r.link,
      snippet: r.snippet || '',
      source: extractDomain(r.link),
    });
    if (results.length >= 5) break;
  }

  return NextResponse.json(results);
}

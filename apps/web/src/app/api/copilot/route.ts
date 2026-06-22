import { NextRequest, NextResponse } from 'next/server';
import { fetchSignals, fetchHospitals, fetchHospitalContacts } from '@/lib/api';

const SYSTEM_PROMPT_BASE = `You are Iris, an AI co-pilot for Adonis Account Intelligence — a sales intelligence tool for the Adonis healthcare RCM (Revenue Cycle Management) sales team.

Your job is to help account executives interpret signals, prioritize outreach, and act fast on opportunities. You have access to live signals and revenue & finance leadership contacts for the rep's assigned hospitals.

Always tie answers to RCM — denial rates, billing operations, Epic migrations, CFO transitions, vendor evaluations, revenue cycle staffing. Adonis sells RCM automation and revenue cycle optimization to hospitals.

Be direct and confident. Do not use emojis — keep all output professional and text-only. If no signals or contacts are available in the system context, state exactly that. Do NOT fabricate or hallucinate any signals, contacts, or URLs.

When citing a signal, include the source as a markdown link: [Source Name](url). Only link sources explicitly provided in the CURRENT LIVE SIGNALS IN THE SYSTEM context. Do not invent links.

SPECIAL BEHAVIORS:
- When asked for a "briefing" or "brief me": give a structured morning brief with (1) urgent signals ranked by priority, (2) top 2-3 outreach opportunities with the contact name and why now, (3) one sentence on what to ignore this week. Use bold headers.
- When asked "who should I call": rank the rep's accounts by urgency + timing window. For each, give the contact name, why now, and the pitch angle in one sentence.
- When asked to "draft an email" or "write an outreach email": always start your response with "Subject:" on the first line, then a blank line, then the email body addressed to the specific contact if known. Keep it under 150 words. Make it specific to the signal — no generic language.`;

export async function POST(req: NextRequest) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ reply: 'API key not configured.' }, { status: 200 });
  }

  const { message, history, userId, isAdmin } = await req.json();

  let signalsContext = 'No live signals available.';
  let contactsContext = 'No contacts available.';
  let territoryContext = '';

  try {
    const [signals, hospitals] = await Promise.all([fetchSignals(), fetchHospitals()]);

    // Determine this user's territory
    const myHospitals = isAdmin
      ? hospitals
      : hospitals.filter((h) => h.ae_users.some((u) => u.id === userId));

    const myHospitalIds = new Set(myHospitals.map((h) => h.id));
    const hospitalMap = Object.fromEntries(hospitals.map((h) => [h.id, h.name]));

    // Find the user's name
    let userName = 'the rep';
    for (const h of hospitals) {
      const match = h.ae_users.find((u) => u.id === userId);
      if (match) {
        userName = match.name;
        break;
      }
    }

    territoryContext = isAdmin
      ? `You are speaking with ${userName} (Admin — sees all accounts).`
      : `You are speaking with ${userName}. Their accounts: ${myHospitals.map((h) => h.name).join(', ')}.`;

    // Contacts for this user's hospitals only
    const allContacts = await Promise.all(
      myHospitals.map((h) =>
        fetchHospitalContacts(h.id)
          .then((contacts) => contacts.map((c) => ({ ...c, hospitalName: h.name })))
          .catch(() => [])
      )
    );
    const contacts = allContacts.flat().filter((c) => c.full_name);
    if (contacts.length > 0) {
      contactsContext = contacts
        .map((c) => {
          const parts = [`${c.hospitalName} · ${c.full_name}`];
          if (c.role) parts.push(c.role);
          if (c.linkedin_url) parts.push(`LinkedIn: ${c.linkedin_url}`);
          if (c.email) parts.push(`Email: ${c.email}`);
          return parts.join(' · ');
        })
        .join('\n');
    }

    // Signals for this user's hospitals only
    const relevant = signals
      .filter((s) => s.tier !== 'filtered_out' && myHospitalIds.has(s.hospital_id))
      .slice(0, 60);

    if (relevant.length > 0) {
      signalsContext = relevant
        .map((s) => {
          const hospitalName = hospitalMap[s.hospital_id] || 'Unknown Hospital';
          const date = (s.published_date || s.created_at).split('T')[0];
          const tier = s.tier === 'urgent' ? 'URGENT' : 'UPDATE';
          const parts = [
            `[${date}] ${tier} · ${hospitalName} · ${s.signal_type.replace(/_/g, ' ')}`,
            `Title: ${s.title || s.signal_type}`,
          ];
          if (s.summary) parts.push(`Summary: ${s.summary}`);
          if (s.why_it_matters) parts.push(`Why it matters: ${s.why_it_matters}`);
          if (s.source_name && s.source_url)
            parts.push(`Source: [${s.source_name}](${s.source_url})`);
          else if (s.source_url) parts.push(`Source: ${s.source_url}`);
          return parts.join('\n');
        })
        .join('\n\n');
    }
  } catch (err) {
    console.error('Failed to fetch context for copilot:', err);
  }

  const systemPrompt = `${SYSTEM_PROMPT_BASE}

${territoryContext}

REVENUE & FINANCE LEADERSHIP CONTACTS (name · title · LinkedIn · email):
${contactsContext}

CURRENT LIVE SIGNALS IN THE SYSTEM:
${signalsContext}`;

  const messages = [
    ...(history ?? []).map((m: { role: string; text: string }) => ({
      role: m.role as 'user' | 'assistant',
      content: m.text,
    })),
    { role: 'user' as const, content: String(message) },
  ];

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 1024,
      system: systemPrompt,
      messages,
    }),
  });

  const data = await res.json();
  const reply = data?.content?.[0]?.text ?? 'No response.';
  return NextResponse.json({ reply });
}

import { NextRequest, NextResponse } from 'next/server';
import { fetchSignals, fetchHospitals, fetchHospitalContacts } from '@/lib/api';

const SYSTEM_PROMPT_BASE = `You are an AI co-pilot for Adonis Account Intelligence, a sales intelligence tool for the Adonis healthcare RCM (Revenue Cycle Management) sales team.

Your job is to help account executives interpret signals and decide how to act. You do NOT need live database access — the rep will describe the signal or account situation, and you provide strategic guidance.

When a rep mentions a hospital, signal, or event, immediately give them:
- What it means for their sales opportunity
- The specific outreach angle to take
- The timing window if relevant

Always tie answers to RCM — denial rates, billing operations, Epic migrations, CFO transitions, vendor evaluations, revenue cycle staffing. Adonis sells RCM automation and revenue cycle optimization to hospitals.

Be direct and confident. No disclaimers about missing data or system access. 2-4 sentences max unless more detail is requested.

When citing a signal, include the source as a markdown link at the end of the relevant sentence, like: [Source Name](url). Only link sources that are provided in the signal data.`;

export async function POST(req: NextRequest) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ reply: 'API key not configured.' }, { status: 200 });
  }

  const { message, history } = await req.json();

  let signalsContext = 'No live signals available.';
  let contactsContext = 'No contacts available.';
  try {
    const [signals, hospitals] = await Promise.all([
      fetchSignals(),
      fetchHospitals(),
    ]);
    const hospitalMap = Object.fromEntries(hospitals.map((h) => [h.id, h.name]));

    // Fetch contacts for all hospitals in parallel
    const allContacts = await Promise.all(
      hospitals.map((h) =>
        fetchHospitalContacts(h.id)
          .then((contacts) => contacts.map((c) => ({ ...c, hospitalName: h.name })))
          .catch(() => [])
      )
    );
    const contacts = allContacts.flat().filter((c) => c.name);
    if (contacts.length > 0) {
      contactsContext = contacts
        .map((c) => {
          const parts = [`${c.hospitalName} · ${c.name}`];
          if (c.title) parts.push(c.title);
          if (c.linkedin_url) parts.push(`LinkedIn: ${c.linkedin_url}`);
          if (c.email) parts.push(`Email: ${c.email}`);
          return parts.join(' · ');
        })
        .join('\n');
    }

    const relevant = signals
      .filter((s) => s.tier !== 'filtered_out')
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
          if (s.source_name && s.source_url) parts.push(`Source: [${s.source_name}](${s.source_url})`);
          else if (s.source_url) parts.push(`Source: ${s.source_url}`);
          return parts.join('\n');
        })
        .join('\n\n');
    }
  } catch (err) {
    console.error('Failed to fetch context for copilot:', err);
  }

  const systemPrompt = `${SYSTEM_PROMPT_BASE}

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
      max_tokens: 512,
      system: systemPrompt,
      messages,
    }),
  });

  const data = await res.json();
  const reply = data?.content?.[0]?.text ?? 'No response.';
  return NextResponse.json({ reply });
}

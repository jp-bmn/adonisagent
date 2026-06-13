import { NextRequest, NextResponse } from 'next/server';
import { fetchSignals, fetchHospitals } from '@/lib/api';

const SYSTEM_PROMPT_BASE = `You are an AI co-pilot for Adonis Account Intelligence, a sales intelligence tool for the Adonis healthcare RCM (Revenue Cycle Management) sales team.

Your job is to help account executives interpret signals and decide how to act. You do NOT need live database access — the rep will describe the signal or account situation, and you provide strategic guidance.

When a rep mentions a hospital, signal, or event, immediately give them:
- What it means for their sales opportunity
- The specific outreach angle to take
- The timing window if relevant

Always tie answers to RCM — denial rates, billing operations, Epic migrations, CFO transitions, vendor evaluations, revenue cycle staffing. Adonis sells RCM automation and revenue cycle optimization to hospitals.

Be direct and confident. No disclaimers about missing data or system access. 2-4 sentences max unless more detail is requested.`;

export async function POST(req: NextRequest) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ reply: 'API key not configured.' }, { status: 200 });
  }

  const { message, history } = await req.json();

  let signalsContext = 'No live signals available.';
  try {
    const [signals, hospitals] = await Promise.all([
      fetchSignals(undefined, { limit: 50 }),
      fetchHospitals(),
    ]);
    const hospitalMap = Object.fromEntries(hospitals.map((h) => [h.id, h.name]));

    if (signals.length > 0) {
      signalsContext = signals
        .map((s) => {
          const hospitalName = hospitalMap[s.hospital_id] || 'Unknown Hospital';
          const date = s.published_date || s.created_at.split('T')[0];
          return `[${date}] ${hospitalName} (${s.tier}) - ${s.title || s.signal_type}. Why it matters: ${s.why_it_matters || 'N/A'}`;
        })
        .join('\n');
    }
  } catch (err) {
    console.error('Failed to fetch context for copilot:', err);
  }

  const systemPrompt = `${SYSTEM_PROMPT_BASE}
  
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

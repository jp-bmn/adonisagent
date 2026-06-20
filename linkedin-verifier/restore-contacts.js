/**
 * restore-contacts.js
 *
 * Searches for current revenue & finance leadership at all 6 hospitals,
 * verifies LinkedIn URLs via Claude, and upserts into Supabase.
 * Safe to run multiple times — never wipes existing data.
 *
 * Usage:
 *   node restore-contacts.js
 */

require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const SERPER_API_KEY = process.env.SERPER_API_KEY;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;

const client = new Anthropic({ apiKey: ANTHROPIC_API_KEY });

const HOSPITALS = [
  { id: 'a4725891-7354-4187-a6c1-93d7ea9a078f', name: 'Ascension' },
  { id: '7b836e62-3ee8-4d10-b30e-028734a5f812', name: 'CommonSpirit Health' },
  { id: 'a17f653f-8479-4159-9149-63e65d2d50a2', name: 'Jefferson Health' },
  { id: 'f0f6b915-3e9d-4040-ba4d-c89339a1e134', name: 'NewYork-Presbyterian' },
  { id: 'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476', name: 'UMass Memorial' },
  { id: '3aebd89a-1d2c-465c-a22b-08ced9613027', name: 'University of Arkansas Medical Sciences' },
];

const ROLES = ['CEO', 'CFO', 'CRO', 'VP Revenue Cycle'];

async function searchSerper(query) {
  const res = await fetch('https://google.serper.dev/search', {
    method: 'POST',
    headers: {
      'X-API-KEY': SERPER_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ q: query, num: 5 }),
  });
  return res.json();
}

async function verifyWithClaude(hospital, role, searchResults) {
  const snippets =
    searchResults.organic
      ?.slice(0, 5)
      .map((r) => `Title: ${r.title}\nURL: ${r.link}\nSnippet: ${r.snippet}`)
      .join('\n\n') || 'No results';

  const msg = await client.messages.create({
    model: 'claude-haiku-4-5-20251001',
    max_tokens: 512,
    messages: [
      {
        role: 'user',
        content: `Find the current ${role} of ${hospital}. Here are search results:

${snippets}

Respond ONLY with valid JSON — no explanation:
{
  "full_name": "First Last",
  "role": "${role}",
  "linkedin_url": "https://www.linkedin.com/in/..." or null,
  "prior_employer": "previous company" or null,
  "confidence": 0.0
}

Rules:
- linkedin_url must be a /in/ profile URL only — never /posts/ or /company/
- Only include linkedin_url if you are certain it belongs to this exact person at ${hospital}
- prior_employer is the most recent employer before this role
- confidence: how sure you are this is the correct current ${role} (0.0–1.0)
- Return null for any field you cannot confirm`,
      },
    ],
  });

  try {
    const text = msg.content[0].text;
    const json = text.match(/\{[\s\S]*\}/)?.[0];
    return JSON.parse(json);
  } catch {
    return null;
  }
}

async function upsertContact(hospitalId, contact) {
  const checkRes = await fetch(
    `${SUPABASE_URL}/rest/v1/contacts?hospital_id=eq.${hospitalId}&role=eq.${encodeURIComponent(contact.role)}&select=id`,
    {
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
      },
    }
  );
  const existing = await checkRes.json();

  if (existing.length > 0) {
    const id = existing[0].id;
    await fetch(`${SUPABASE_URL}/rest/v1/contacts?id=eq.${id}`, {
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
        updated_at: new Date().toISOString(),
      }),
    });
    return 'updated';
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
        is_active: true,
      }),
    });
    return 'inserted';
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  if (!ANTHROPIC_API_KEY || !SERPER_API_KEY || !SUPABASE_URL || !SUPABASE_KEY) {
    console.error('Missing required env vars. Check .env file.');
    process.exit(1);
  }

  console.log('Restoring contacts for all 6 hospitals...\n');

  let inserted = 0;
  let updated = 0;
  let failed = 0;

  for (const hospital of HOSPITALS) {
    console.log(`\n${hospital.name}`);

    for (const role of ROLES) {
      process.stdout.write(`  ${role}... `);

      try {
        const query = `"${hospital.name}" ${role} site:linkedin.com/in`;
        const results = await searchSerper(query);
        const contact = await verifyWithClaude(hospital.name, role, results);

        if (!contact || contact.confidence < 0.5) {
          console.log(`skipped (low confidence)`);
          failed++;
          await sleep(500);
          continue;
        }

        const action = await upsertContact(hospital.id, contact);
        const linkedinTag = contact.linkedin_url ? ' + LinkedIn' : '';
        console.log(`${action}: ${contact.full_name}${linkedinTag}`);

        if (action === 'inserted') inserted++;
        else updated++;
      } catch (err) {
        console.log(`error: ${err.message}`);
        failed++;
      }

      await sleep(700);
    }
  }

  console.log('\n========================================');
  console.log(`Inserted: ${inserted}`);
  console.log(`Updated:  ${updated}`);
  console.log(`Failed:   ${failed}`);
  console.log('========================================');
}

main().catch(console.error);

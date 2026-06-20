/**
 * restore-contacts-v2.js
 *
 * Multi-lane contact search — 5 independent sources per role.
 * Cross-references results before inserting. Much more accurate than v1.
 *
 * Lanes:
 *   1. LinkedIn profiles (site:linkedin.com/in)
 *   2. Hospital press releases / appointment announcements
 *   3. Healthcare news (Becker's, Modern Healthcare, Fierce Healthcare)
 *   4. Hospital website leadership pages
 *   5. General executive search
 *
 * Usage:
 *   node restore-contacts-v2.js
 */

require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const SERPER_API_KEY = process.env.SERPER_API_KEY;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;

const client = new Anthropic({ apiKey: ANTHROPIC_API_KEY });

const HOSPITALS = [
  { id: 'a4725891-7354-4187-a6c1-93d7ea9a078f', name: 'Ascension', domain: 'ascension.org' },
  { id: '7b836e62-3ee8-4d10-b30e-028734a5f812', name: 'CommonSpirit Health', domain: 'commonspirithealth.org' },
  { id: 'a17f653f-8479-4159-9149-63e65d2d50a2', name: 'Jefferson Health', domain: 'jeffersonhealth.org' },
  { id: 'f0f6b915-3e9d-4040-ba4d-c89339a1e134', name: 'NewYork-Presbyterian', domain: 'nyp.org' },
  { id: 'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476', name: 'UMass Memorial', domain: 'umassmemorial.org' },
  { id: '3aebd89a-1d2c-465c-a22b-08ced9613027', name: 'University of Arkansas Medical Sciences', domain: 'uams.edu' },
];

const ROLES = [
  { title: 'CEO', keywords: 'Chief Executive Officer' },
  { title: 'CFO', keywords: 'Chief Financial Officer' },
  { title: 'CRO', keywords: 'Chief Revenue Officer' },
  { title: 'VP Revenue Cycle', keywords: 'Vice President Revenue Cycle' },
];

// Only target hospitals/roles that are missing or low confidence
const TARGETS = [
  { hospitalName: 'Ascension', roles: ['CFO', 'CRO'] },
  { hospitalName: 'NewYork-Presbyterian', roles: ['CEO', 'CFO', 'CRO', 'VP Revenue Cycle'] },
  { hospitalName: 'University of Arkansas Medical Sciences', roles: ['CEO', 'CFO', 'CRO', 'VP Revenue Cycle'] },
  { hospitalName: 'UMass Memorial', roles: ['VP Revenue Cycle'] },
  { hospitalName: 'CommonSpirit Health', roles: ['CRO'] },
  { hospitalName: 'Jefferson Health', roles: ['CEO', 'CRO'] },
];

async function searchSerper(query) {
  try {
    const res = await fetch('https://google.serper.dev/search', {
      method: 'POST',
      headers: {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ q: query, num: 5 }),
    });
    const data = await res.json();
    return data.organic || [];
  } catch {
    return [];
  }
}

async function multiLaneSearch(hospital, role) {
  const { title, keywords } = role;
  const allResults = [];

  // Lane 1: LinkedIn profiles
  const lane1 = await searchSerper(`"${hospital.name}" "${keywords}" site:linkedin.com/in`);
  if (lane1.length) allResults.push({ lane: 'LinkedIn', results: lane1 });
  await sleep(300);

  // Lane 2: Press releases / appointment announcements
  const lane2 = await searchSerper(`"${hospital.name}" "appoints" OR "names" "${keywords}" OR "${title}"`);
  if (lane2.length) allResults.push({ lane: 'Press Release', results: lane2 });
  await sleep(300);

  // Lane 3: Healthcare news publications
  const lane3 = await searchSerper(
    `"${hospital.name}" "${title}" OR "${keywords}" site:beckershospitalreview.com OR site:modernhealthcare.com OR site:fiercehealthcare.com`
  );
  if (lane3.length) allResults.push({ lane: 'Healthcare News', results: lane3 });
  await sleep(300);

  // Lane 4: Hospital website leadership page
  const lane4 = await searchSerper(`site:${hospital.domain} leadership OR "executive team" "${title}" OR "${keywords}"`);
  if (lane4.length) allResults.push({ lane: 'Hospital Website', results: lane4 });
  await sleep(300);

  // Lane 5: General executive search
  const lane5 = await searchSerper(`"${hospital.name}" current "${keywords}" 2024 OR 2025 OR 2026`);
  if (lane5.length) allResults.push({ lane: 'General Search', results: lane5 });

  return allResults;
}

async function verifyWithClaude(hospital, role, laneResults) {
  const formatted = laneResults.map(({ lane, results }) => {
    const snippets = results
      .slice(0, 3)
      .map((r) => `  - ${r.title} | ${r.link}\n    ${r.snippet || ''}`)
      .join('\n');
    return `[${lane}]\n${snippets}`;
  }).join('\n\n');

  const msg = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 768,
    messages: [
      {
        role: 'user',
        content: `You are verifying the current ${role.title} (${role.keywords}) of ${hospital.name}.

I searched 5 different sources. Here are all results:

${formatted}

Task: Identify the most likely current ${role.title} of ${hospital.name} based on all evidence above.
- Look for name consensus across multiple lanes
- Prefer recent appointments (2024-2026)
- A LinkedIn /in/ URL is a strong signal if the name matches
- Prior employer = their job before joining ${hospital.name}

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
- linkedin_url must be /in/ format only — never /posts/ or /company/ or /pub/
- confidence: 0.9+ if 3+ lanes agree, 0.7-0.9 if 2 lanes agree, 0.5-0.7 if 1 strong source, below 0.5 if uncertain
- sources_agreed: how many lanes pointed to this same person
- If you cannot identify with reasonable certainty, set confidence below 0.5`,
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

  console.log('Multi-lane contact search — targeting missing/low-confidence contacts\n');

  let inserted = 0;
  let updated = 0;
  let skipped = 0;

  for (const target of TARGETS) {
    const hospital = HOSPITALS.find((h) => h.name === target.hospitalName);
    if (!hospital) continue;

    console.log(`\n${hospital.name}`);

    for (const roleTitle of target.roles) {
      const role = ROLES.find((r) => r.title === roleTitle);
      if (!role) continue;

      process.stdout.write(`  ${roleTitle}... `);

      const laneResults = await multiLaneSearch(hospital, role);

      if (laneResults.length === 0) {
        console.log('no results across all lanes');
        skipped++;
        continue;
      }

      const contact = await verifyWithClaude(hospital, role, laneResults);

      if (!contact || contact.confidence < 0.55) {
        console.log(`skipped (confidence: ${contact?.confidence?.toFixed(2) ?? 'n/a'} — ${contact?.reasoning ?? 'no match'})`);
        skipped++;
        await sleep(500);
        continue;
      }

      const action = await upsertContact(hospital.id, contact);
      const linkedinTag = contact.linkedin_url ? ' + LinkedIn' : '';
      const sourcesTag = contact.sources_agreed > 1 ? ` [${contact.sources_agreed} sources]` : '';
      console.log(`${action}: ${contact.full_name}${linkedinTag}${sourcesTag} (${(contact.confidence * 100).toFixed(0)}% confident)`);
      console.log(`    reason: ${contact.reasoning}`);

      if (action === 'inserted') inserted++;
      else updated++;

      await sleep(800);
    }
  }

  console.log('\n========================================');
  console.log(`Inserted: ${inserted}`);
  console.log(`Updated:  ${updated}`);
  console.log(`Skipped:  ${skipped}`);
  console.log('========================================');
}

main().catch(console.error);

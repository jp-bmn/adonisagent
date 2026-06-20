/**
 * run-all.js
 *
 * Pulls all contacts from the Adonis API, finds ones with missing LinkedIn URLs,
 * runs them through the LinkedIn verifier, and prints a Supabase update script.
 *
 * Usage:
 *   ANTHROPIC_API_KEY=your_key node run-all.js
 *
 * Output:
 *   - Live results printed as each contact is verified
 *   - At the end: a summary + SQL UPDATE statements to paste into Supabase
 */

require('dotenv').config();
const { verifyWithFallback } = require('./verifier');

const API_BASE = 'https://adonisagents-production.up.railway.app/api/v1';
const USER_ID = 'df7c14fd-cde3-4025-be00-ca42f4d31741';

const HOSPITALS = [
  { id: 'a4725891-7354-4187-a6c1-93d7ea9a078f', name: 'Ascension' },
  { id: '7b836e62-3ee8-4d10-b30e-028734a5f812', name: 'CommonSpirit Health' },
  { id: 'a17f653f-8479-4159-9149-63e65d2d50a2', name: 'Jefferson Health' },
  { id: 'f0f6b915-3e9d-4040-ba4d-c89339a1e134', name: 'NewYork-Presbyterian' },
  { id: 'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476', name: 'UMass Memorial' },
  { id: '3aebd89a-1d2c-465c-a22b-08ced9613027', name: 'University of Arkansas Medical Sciences' },
];

async function fetchContacts(hospitalId) {
  const res = await fetch(`${API_BASE}/hospitals/${hospitalId}/contacts`, {
    headers: { 'X-User-Id': USER_ID },
  });
  if (!res.ok) return [];
  return res.json();
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error('❌ ANTHROPIC_API_KEY not set. Add it to linkedin-verifier/.env');
    process.exit(1);
  }

  console.log('🔍 Pulling contacts from all 6 hospitals...\n');

  const updates = [];
  const failed = [];

  for (const hospital of HOSPITALS) {
    console.log(`\n📍 ${hospital.name}`);
    const contacts = await fetchContacts(hospital.id);

    if (!contacts.length) {
      console.log('  No contacts found');
      continue;
    }

    // Only process contacts missing a valid LinkedIn URL
    const needsVerification = contacts.filter(
      (c) => !c.linkedin_url || c.linkedin_url.includes('/posts/')
    );

    const alreadyVerified = contacts.filter(
      (c) => c.linkedin_url && c.linkedin_url.includes('/in/')
    );

    if (alreadyVerified.length > 0) {
      console.log(`  ✅ ${alreadyVerified.length} already have valid LinkedIn URLs — skipping`);
    }

    if (!needsVerification.length) {
      console.log('  ✅ All contacts verified — nothing to do');
      continue;
    }

    console.log(`  🔄 Verifying ${needsVerification.length} contacts...`);

    for (const contact of needsVerification) {
      console.log(`  → ${contact.full_name} (${contact.role})`);

      const result = await verifyWithFallback({
        id: contact.id,
        name: contact.full_name,
        role: contact.role,
        hospital: hospital.name,
        currentUrl: contact.linkedin_url,
      });

      if (result.status === 'verified' || result.status === 'conflict') {
        if (result.suggestedUrl) {
          console.log(`     ✅ Found: ${result.suggestedUrl}`);
          console.log(`     💬 ${result.reasoning}`);
          updates.push({
            id: contact.id,
            name: contact.full_name,
            hospital: hospital.name,
            url: result.suggestedUrl,
            reasoning: result.reasoning,
          });
        }
      } else {
        console.log(`     ❌ ${result.status}: ${result.reasoning}`);
        failed.push({ name: contact.full_name, hospital: hospital.name, reason: result.reasoning });
      }

      await sleep(600); // rate limit buffer
    }
  }

  // Summary
  console.log('\n\n========================================');
  console.log(`✅ VERIFIED: ${updates.length} contacts`);
  console.log(`❌ FAILED:   ${failed.length} contacts`);
  console.log('========================================\n');

  if (updates.length > 0) {
    console.log('📋 SUPABASE SQL — paste this into your Supabase SQL editor:\n');
    for (const u of updates) {
      console.log(`-- ${u.name} (${u.hospital})`);
      console.log(`UPDATE contacts SET linkedin_url = '${u.url}' WHERE id = '${u.id}';\n`);
    }
  }

  if (failed.length > 0) {
    console.log('\n⚠️  CONTACTS THAT NEED MANUAL LOOKUP:');
    for (const f of failed) {
      console.log(`  - ${f.name} @ ${f.hospital}: ${f.reason}`);
    }
  }
}

main().catch(console.error);

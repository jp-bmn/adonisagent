/**
 * Build the digest and print it to stdout without sending.
 * Use to iterate on the email template visually:
 *   pnpm --filter @adonis/agents digest:preview > preview.html && open preview.html
 */

import { createServerClient, listHospitals, listSignals } from '@adonis/db';
import { renderDigestHtml, renderDigestText } from '../pipeline/render.js';

const db = createServerClient();
const since = new Date();
since.setDate(since.getDate() - 7);
const [hospitals, signals] = await Promise.all([
  listHospitals(db),
  listSignals(db, { since, limit: 200 }),
]);

const byId = new Map(hospitals.map((h) => [h.id, h]));
const map = new Map<string, typeof signals>();
for (const s of signals) {
  const list = map.get(s.hospital_id) ?? [];
  list.push(s);
  map.set(s.hospital_id, list);
}
const groups = Array.from(map.entries())
  .map(([hid, list]) => {
    const hospital = byId.get(hid);
    return hospital ? { hospital, signals: list } : null;
  })
  .filter(
    (g): g is { hospital: (typeof hospitals)[number]; signals: typeof signals } => g !== null
  );

const mode = process.argv[2] ?? 'html';
if (mode === 'text') {
  console.log(renderDigestText(groups));
} else {
  console.log(renderDigestHtml(groups));
}
process.exit(0);

/**
 * Weekly digest builder.
 *
 * Per the final PRD: every Monday at 8 AM ET, agents compile a digest of all
 * signals from the past week and email it to Danielle. She reviews and
 * forwards the relevant sections to each AE.
 *
 * For Phase 2 we also build per-AE digests filtered by territory.
 * For now, Phase 1 ships the admin digest to Danielle only.
 */

import { Resend } from 'resend';
import { createServerClient, listSignals, listHospitals } from '@adonis/db';
import type { Signal, Hospital } from '@adonis/shared';
import { log } from '../lib/log.js';
import { renderDigestHtml, renderDigestText } from './render.js';

const resendKey = process.env.RESEND_API_KEY;
const resend = resendKey ? new Resend(resendKey) : null;

const FROM_ADDRESS = process.env.DIGEST_FROM ?? 'Adonis Intel <digest@example.com>';
const DANIELLE_EMAIL = process.env.DANIELLE_EMAIL ?? 'danielle.ferdon@adonis.io';

export interface DigestResult {
  digestsBuilt: number;
  digestsSent: number;
  errors: string[];
}

export async function buildAndSendDigests(): Promise<DigestResult> {
  const result: DigestResult = { digestsBuilt: 0, digestsSent: 0, errors: [] };

  const db = createServerClient();
  const since = new Date();
  since.setDate(since.getDate() - 7);

  const [hospitals, signals] = await Promise.all([
    listHospitals(db),
    listSignals(db, { since, limit: 200 }),
  ]);

  if (signals.length === 0) {
    log.info('no signals this week — skipping digest');
    return result;
  }

  const grouped = groupByHospital(signals, hospitals);
  const html = renderDigestHtml(grouped);
  const text = renderDigestText(grouped);

  result.digestsBuilt = 1;

  if (!resend) {
    log.warn('RESEND_API_KEY not set — digest built but not sent. Preview follows:');
    console.log(text);
    return result;
  }

  try {
    const weekOf = new Date().toISOString().slice(0, 10);
    const subj = `Adonis Account Intelligence — week of ${weekOf}`;
    const resp = await resend.emails.send({
      from: FROM_ADDRESS,
      to: DANIELLE_EMAIL,
      subject: subj,
      html,
      text,
    });
    log.info('digest sent', { id: resp.data?.id });
    result.digestsSent += 1;

    // TODO: persist a row in `digests` table marking signals as delivered_in_digest=true
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    log.error('digest send failed', err);
    result.errors.push(msg);
  }

  return result;
}

interface HospitalGroup {
  hospital: Hospital;
  signals: Signal[];
}

function groupByHospital(signals: Signal[], hospitals: Hospital[]): HospitalGroup[] {
  const byId = new Map(hospitals.map((h) => [h.id, h]));
  const map = new Map<string, Signal[]>();
  for (const s of signals) {
    const list = map.get(s.hospital_id) ?? [];
    list.push(s);
    map.set(s.hospital_id, list);
  }
  return Array.from(map.entries())
    .map(([hospitalId, list]) => {
      const hospital = byId.get(hospitalId);
      if (!hospital) return null;
      return { hospital, signals: list.sort((a, b) => b.score - a.score) };
    })
    .filter((g): g is HospitalGroup => g !== null)
    .sort((a, b) => {
      // Hospitals with urgent signals sort first
      const aUrgent = a.signals.some((s) => s.priority === 'urgent');
      const bUrgent = b.signals.some((s) => s.priority === 'urgent');
      if (aUrgent !== bUrgent) return aUrgent ? -1 : 1;
      return a.hospital.display_name.localeCompare(b.hospital.display_name);
    });
}

import type { Hospital } from '@adonis/shared';
import type { RawItem } from './types.js';
import { log } from '../lib/log.js';

/**
 * Becker's Hospital Review / Becker's Health IT.
 *
 * From the kickoff (Reed): "Beckers is one example of a publication that you can sign
 * up for, you don't have to pay for. There are other ones..."
 *
 * Strategy: Becker's publishes a high volume of healthcare news, indexed by Google
 * and reachable via serper.dev queries that scope `site:beckershospitalreview.com`.
 * We can also subscribe to email digests as an additional input path.
 *
 * TODO (week 1-2):
 *   - Approach A: serper.dev with `site:beckershospitalreview.com "{hospital}"`
 *     — simplest, no rate-limit risk on our side
 *   - Approach B: RSS feeds if Becker's exposes them per-topic
 *   - Approach C: scrape the search page directly — last resort, fragile
 *   - Start with A
 */
export async function scrapeBeckers(hospital: Hospital): Promise<RawItem[]> {
  log.info(`[beckers] would query for ${hospital.display_name}`);
  // TODO
  return [];
}

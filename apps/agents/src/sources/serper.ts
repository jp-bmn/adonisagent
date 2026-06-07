import type { Hospital } from '@adonis/shared';
import type { RawItem } from './types.js';
import { log } from '../lib/log.js';

/**
 * serper.dev search source.
 * The PRD names this as the primary news aggregator ("pennies per search").
 *
 * Strategy: per hospital, run a small set of revenue-cycle-relevant queries.
 * Examples:
 *   "{hospital_name}" CRO OR "Chief Revenue Officer"
 *   "{hospital_name}" "revenue cycle"
 *   "{hospital_name}" Epic OR EHR
 *   "{hospital_name}" acquisition OR merger
 *   "{hospital_name}" outsourcing
 *
 * TODO (week 1-2):
 *   - Wire SERPER_API_KEY from env
 *   - Use the /news endpoint with `tbs=qdr:w` (past week) to keep results fresh
 *   - Dedup by URL within a single run
 *   - Map serper results to RawItem
 *   - Budget: ~5 queries/hospital × 5 hospitals × 3 runs/week ≈ 75 calls/week
 *     (negligible cost on serper's pricing)
 */
export async function scrapeSerper(hospital: Hospital): Promise<RawItem[]> {
  const key = process.env.SERPER_API_KEY;
  if (!key) {
    log.warn('SERPER_API_KEY not set — skipping serper scrape');
    return [];
  }
  log.info(`[serper] would query for ${hospital.display_name}`);
  // TODO: implement serper.dev queries
  return [];
}

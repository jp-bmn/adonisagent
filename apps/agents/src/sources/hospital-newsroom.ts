import type { Hospital } from '@adonis/shared';
import type { RawItem } from './types.js';
import { log } from '../lib/log.js';

/**
 * Scrapes a hospital's own newsroom page.
 * This is the cleanest source for verified personnel and contract announcements —
 * hospitals only publish things they've officially confirmed.
 *
 * TODO (week 1-2):
 *   - For each hospital with newsroom_url, fetch and parse the page
 *   - Use Cheerio for static HTML, Playwright for JS-rendered (NYP is dynamic)
 *   - Respect robots.txt; identify our User-Agent
 *   - Extract: title, summary text, publication date, item URL
 *   - Limit to the last 7-14 days so we don't reprocess old items
 *   - Return as RawItem[]
 */
export async function scrapeHospitalNewsroom(hospital: Hospital): Promise<RawItem[]> {
  if (!hospital.newsroom_url) {
    log.debug(`no newsroom_url for ${hospital.id} — skipping`);
    return [];
  }
  log.info(`[hospital_newsroom] would scrape ${hospital.newsroom_url}`);
  // TODO: implement actual scrape
  return [];
}

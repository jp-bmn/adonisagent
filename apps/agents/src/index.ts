/**
 * Agent worker entry point.
 *
 * Runs on a schedule (Mon/Wed/Fri per the PRD; configurable via env).
 * On each tick, fans out to per-source scrapers, scores the results,
 * and writes signals to the database.
 *
 * Mondays additionally build and send the weekly email digest.
 */

import cron from 'node-cron';
import { runFullScrape } from './pipeline/scrape.js';
import { buildAndSendDigests } from './pipeline/digest.js';
import { log } from './lib/log.js';

const SCRAPE_CRON = process.env.SCRAPE_CRON ?? '0 7 * * 1,3,5'; // Mon/Wed/Fri 7:00 AM
const DIGEST_CRON = process.env.DIGEST_CRON ?? '0 8 * * 1'; // Mondays 8:00 AM
const TZ = process.env.TZ ?? 'America/New_York';

async function main() {
  log.info('agent worker starting', { scrapeCron: SCRAPE_CRON, digestCron: DIGEST_CRON, tz: TZ });

  // Mon/Wed/Fri: pull from every source, score, persist signals
  cron.schedule(
    SCRAPE_CRON,
    async () => {
      log.info('scheduled scrape run starting');
      try {
        const summary = await runFullScrape();
        log.info('scheduled scrape run complete', summary);
      } catch (err) {
        log.error('scheduled scrape failed', err);
      }
    },
    { timezone: TZ }
  );

  // Mondays only: build digests and email Danielle
  cron.schedule(
    DIGEST_CRON,
    async () => {
      log.info('weekly digest job starting');
      try {
        const result = await buildAndSendDigests();
        log.info('weekly digest job complete', result);
      } catch (err) {
        log.error('weekly digest failed', err);
      }
    },
    { timezone: TZ }
  );

  log.info('agent worker ready — waiting for next scheduled run');

  // Keep process alive
  process.stdin.resume();
}

main().catch((err) => {
  log.error('fatal error in agent worker', err);
  process.exit(1);
});

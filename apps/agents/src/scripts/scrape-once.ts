/**
 * One-shot scrape — run the full pipeline once, without waiting for cron.
 * Useful in development to test source wiring.
 *
 * Run: `pnpm --filter @adonis/agents scrape:once`
 */

import { runFullScrape } from '../pipeline/scrape.js';
import { log } from '../lib/log.js';

const summary = await runFullScrape();
log.info('one-shot scrape complete', summary);
process.exit(0);

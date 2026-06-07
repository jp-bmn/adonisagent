/**
 * Scrape pipeline.
 * Runs every source in parallel, then scores results, then writes signals.
 *
 * Adding a new source = add a file in ./sources/ and register it below.
 */

import { createServerClient, listHospitals } from '@adonis/db';
import { scrapeHospitalNewsroom } from '../sources/hospital-newsroom.js';
import { scrapeSerper } from '../sources/serper.js';
import { scrapeBeckers } from '../sources/beckers.js';
import { scoreAndPersist } from './score.js';
import { log } from '../lib/log.js';

export interface ScrapeRunSummary {
  hospitalsProcessed: number;
  rawItemsFound: number;
  signalsCreated: number;
  durationMs: number;
  errors: string[];
}

export async function runFullScrape(): Promise<ScrapeRunSummary> {
  const start = Date.now();
  const db = createServerClient();
  const hospitals = await listHospitals(db);
  log.info(`scrape: ${hospitals.length} hospitals queued`);

  const summary: ScrapeRunSummary = {
    hospitalsProcessed: 0,
    rawItemsFound: 0,
    signalsCreated: 0,
    durationMs: 0,
    errors: [],
  };

  // Per-hospital fan-out. Parallelism kept modest to be polite to source sites.
  const CONCURRENCY = 3;
  for (let i = 0; i < hospitals.length; i += CONCURRENCY) {
    const batch = hospitals.slice(i, i + CONCURRENCY);
    await Promise.all(
      batch.map(async (hospital) => {
        try {
          const items = (
            await Promise.all([
              scrapeHospitalNewsroom(hospital),
              scrapeSerper(hospital),
              scrapeBeckers(hospital),
            ])
          ).flat();
          summary.rawItemsFound += items.length;
          const created = await scoreAndPersist(db, hospital, items);
          summary.signalsCreated += created;
          summary.hospitalsProcessed += 1;
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          log.error(`scrape failed for ${hospital.id}`, { hospital: hospital.id, error: msg });
          summary.errors.push(`${hospital.id}: ${msg}`);
        }
      })
    );
  }

  summary.durationMs = Date.now() - start;
  return summary;
}

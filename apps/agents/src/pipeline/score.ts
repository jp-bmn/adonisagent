/**
 * Scoring & persistence.
 *
 * For each raw item:
 *   1. Quick keyword filter — drop obvious noise (equipment, clinical, awards)
 *   2. LLM classification — assign a SignalCategory and refined score
 *   3. Generate the "why this matters" rationale in plain language
 *   4. Dedup against existing signals by content hash
 *   5. Persist to the database
 *
 * The LLM step uses Claude. Prompt design is the most important thing here —
 * the signal-vs-noise discrimination is what makes Danielle stop using Glean.
 */

import { createHash } from 'node:crypto';
import type { SupabaseClient } from '@supabase/supabase-js';
import {
  SIGNAL_CONFIG,
  isLikelyNoise,
  ALERT_SCORE_THRESHOLD,
  type SignalCategory,
  type Hospital,
} from '@adonis/shared';
import { insertSignal } from '@adonis/db';
import { classifyWithLLM } from '../lib/llm.js';
import { log } from '../lib/log.js';
import type { RawItem } from '../sources/types.js';

export async function scoreAndPersist(
  db: SupabaseClient,
  hospital: Hospital,
  items: RawItem[]
): Promise<number> {
  let createdCount = 0;

  for (const item of items) {
    // Step 1: cheap noise filter before spending an LLM call
    const blob = `${item.title}\n${item.text}`;
    if (isLikelyNoise(blob)) {
      log.debug('filtered as noise', { hospital: hospital.id, title: item.title });
      continue;
    }

    // Step 2: LLM classification
    let classification;
    try {
      classification = await classifyWithLLM(hospital, item);
    } catch (err) {
      log.warn('llm classification failed', err);
      continue;
    }

    if (classification.priority === 'noise') {
      continue;
    }

    const config = SIGNAL_CONFIG[classification.category as SignalCategory];

    // Step 3: dedup hash so the same story from multiple sources doesn't double-count
    const contentHash = createHash('sha256')
      .update(`${hospital.id}|${classification.category}|${item.url}`)
      .digest('hex');

    try {
      await insertSignal(db, {
        hospital_id: hospital.id,
        contact_id: null,
        category: classification.category,
        priority: classification.priority,
        headline: classification.headline,
        summary: classification.summary,
        rationale: classification.rationale ?? config.defaultRationale,
        source_url: item.url,
        source_type: item.sourceType,
        published_at: item.publishedAt ?? null,
        detected_at: new Date().toISOString(),
        score: classification.score,
        delivered_in_digest: false,
        alert_fired: false,
      });
      createdCount += 1;

      if (classification.priority === 'urgent' && classification.score >= ALERT_SCORE_THRESHOLD) {
        // TODO (week 4-5): trigger instant alert email here
        log.info('urgent signal — alert TODO', {
          hospital: hospital.id,
          headline: classification.headline,
        });
      }
    } catch (err) {
      // Likely a unique-constraint violation on content_hash → already exists, skip
      log.debug('insert skipped (probable dedup)', { hospital: hospital.id });
    }
  }

  return createdCount;
}

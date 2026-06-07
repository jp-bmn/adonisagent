/**
 * Claude-based signal classifier.
 *
 * Takes a raw news item, returns a structured classification:
 *   - category (one of SignalCategory)
 *   - priority (urgent | standard | noise)
 *   - headline, summary, rationale
 *   - score 0-100
 *
 * The system prompt embeds the taxonomy from packages/shared/src/signals.ts.
 * Keep the prompt and the taxonomy in sync.
 */

import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';
import type { Hospital, SignalCategory, SignalPriority } from '@adonis/shared';
import type { RawItem } from '../sources/types.js';
import { log } from './log.js';

const apiKey = process.env.ANTHROPIC_API_KEY;
const client = apiKey ? new Anthropic({ apiKey }) : null;

const ClassificationSchema = z.object({
  category: z.enum([
    'LEADERSHIP_HIRE',
    'LEADERSHIP_DEPARTURE',
    'MERGER_ACQUISITION',
    'VENDOR_CHANGE',
    'EPIC_EVENT',
    'REGULATORY',
    'STRATEGY_CHANGE',
    'AUTOMATION_INITIATIVE',
    'PARTNERSHIP',
    'FINANCIAL_PERFORMANCE',
    'LEADERSHIP_OTHER',
    'REFERENCE_MATERIAL',
    'NOISE',
  ]),
  priority: z.enum(['urgent', 'standard', 'noise']),
  headline: z.string().max(120),
  summary: z.string().max(500),
  rationale: z.string().max(400),
  score: z.number().int().min(0).max(100),
});

export interface Classification {
  category: SignalCategory;
  priority: SignalPriority;
  headline: string;
  summary: string;
  rationale: string;
  score: number;
}

const SYSTEM_PROMPT = `You are a healthcare-sales signal classifier for Adonis, an RCM software company that sells to hospitals.

Your job: read a news item about a hospital and decide whether it's worth surfacing to a sales rep.

CATEGORIES (urgent — fires an alert):
- LEADERSHIP_HIRE: new CRO, CFO, VP Revenue Cycle, Director RCM
- LEADERSHIP_DEPARTURE: senior revenue/finance leader departs
- MERGER_ACQUISITION: hospital M&A or system expansion
- VENDOR_CHANGE: RCM vendor or outsourcing change
- EPIC_EVENT: Epic go-live, migration, or expansion
- REGULATORY: regulatory concern, financial review, credit downgrade

CATEGORIES (standard — included in weekly digest):
- STRATEGY_CHANGE, AUTOMATION_INITIATIVE, PARTNERSHIP, FINANCIAL_PERFORMANCE,
  LEADERSHIP_OTHER (non-revenue exec changes), REFERENCE_MATERIAL (interview, podcast — useful prep)

NOISE — do not surface:
- Equipment / facility / capital projects, clinical or research news, community/awards/philanthropy,
  general AI news not specific to the hospital's revenue operations.

For each item, return STRICT JSON:
{
  "category": "<category>",
  "priority": "urgent" | "standard" | "noise",
  "headline": "<one-line headline, max 120 chars>",
  "summary": "<2-3 sentence factual summary>",
  "rationale": "<one-sentence why-this-matters for the rep>",
  "score": <integer 0-100>
}

Score guidance: 80-100 urgent, 40-79 standard, 0-39 noise.

Be conservative: when in doubt, score lower. False positives erode rep trust faster than false negatives.`;

export async function classifyWithLLM(hospital: Hospital, item: RawItem): Promise<Classification> {
  if (!client) {
    throw new Error('ANTHROPIC_API_KEY not configured');
  }

  const userPrompt = `Hospital: ${hospital.display_name} (${hospital.state})
Source: ${item.sourceType}
URL: ${item.url}
Title: ${item.title}

Content:
${item.text.slice(0, 4000)}

Classify this item.`;

  const resp = await client.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 800,
    system: SYSTEM_PROMPT,
    messages: [{ role: 'user', content: userPrompt }],
  });

  const text = resp.content[0]?.type === 'text' ? resp.content[0].text : '';

  // Strip ```json fences if Claude wrapped the response
  const cleaned = text
    .replace(/```json\s*/g, '')
    .replace(/```\s*/g, '')
    .trim();

  let parsed;
  try {
    parsed = ClassificationSchema.parse(JSON.parse(cleaned));
  } catch (err) {
    log.warn('llm response failed to parse', { text: cleaned.slice(0, 200) });
    throw err;
  }

  // If category is NOISE, normalize to a standard category but mark priority as noise
  if (parsed.category === 'NOISE') {
    return {
      category: 'REFERENCE_MATERIAL' as SignalCategory,
      priority: 'noise',
      headline: parsed.headline,
      summary: parsed.summary,
      rationale: parsed.rationale,
      score: parsed.score,
    };
  }

  return parsed as Classification;
}

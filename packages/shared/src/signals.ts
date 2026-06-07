/**
 * Signal scoring configuration.
 *
 * This is the codified version of what Reed and Danielle described as
 * "what changes a sales conversation" vs. "what's just noise."
 *
 * The numbers (priority, default score) are STARTING values from the kickoff.
 * They get tuned with Danielle during the workflow walkthrough and
 * refined against real data before Demo Day.
 */

import type { SignalCategory, SignalPriority } from './types';

export interface SignalConfig {
  category: SignalCategory;
  priority: SignalPriority;
  /** Starting score 0-100; the LLM adjusts up/down based on context */
  baseScore: number;
  /** Human-readable label for the UI */
  label: string;
  /** Keywords that hint this is the category — used as a first-pass filter */
  keywordHints: string[];
  /** Default 'why this matters' framing for the rep */
  defaultRationale: string;
}

export const SIGNAL_CONFIG: Record<SignalCategory, SignalConfig> = {
  // ---------- URGENT ----------
  LEADERSHIP_HIRE: {
    category: 'LEADERSHIP_HIRE',
    priority: 'urgent',
    baseScore: 90,
    label: 'New revenue/finance leader hired',
    keywordHints: [
      'chief revenue officer',
      'CRO',
      'CFO',
      'VP revenue cycle',
      'vice president of revenue cycle',
      'appointed',
      'named',
      'joins',
      'welcome',
      'new hire',
    ],
    defaultRationale:
      'New revenue leadership typically re-evaluates vendor relationships within the first 90 days. This is the moment to get on their radar.',
  },
  LEADERSHIP_DEPARTURE: {
    category: 'LEADERSHIP_DEPARTURE',
    priority: 'urgent',
    baseScore: 85,
    label: 'Senior leader departure',
    keywordHints: ['departs', 'steps down', 'resigns', 'transitions', 'former', 'previously'],
    defaultRationale:
      'A leadership gap creates uncertainty — and an opportunity to introduce Adonis to the incoming successor.',
  },
  MERGER_ACQUISITION: {
    category: 'MERGER_ACQUISITION',
    priority: 'urgent',
    baseScore: 92,
    label: 'M&A activity',
    keywordHints: [
      'acquires',
      'acquisition',
      'merger',
      'merges with',
      'to acquire',
      'completes acquisition',
    ],
    defaultRationale:
      'Acquisitions create immediate revenue-cycle complexity, new payer contracts, and consolidation pressure. A sure sign of upcoming RCM problems to solve.',
  },
  VENDOR_CHANGE: {
    category: 'VENDOR_CHANGE',
    priority: 'urgent',
    baseScore: 88,
    label: 'RCM vendor / outsourcing change',
    keywordHints: [
      'outsourcing',
      'in-house',
      'vendor',
      'R1',
      'Conifer',
      'Optum',
      'ends partnership',
      'terminates',
      'transitions away from',
    ],
    defaultRationale:
      'Vendor changes signal active reassessment of revenue-cycle operations — exactly when a new approach lands well.',
  },
  EPIC_EVENT: {
    category: 'EPIC_EVENT',
    priority: 'urgent',
    baseScore: 78,
    label: 'Epic implementation event',
    keywordHints: ['Epic go-live', 'Epic migration', 'Epic expansion', 'Epic rollout', 'EHR'],
    defaultRationale:
      'Epic go-lives reshape revenue-cycle workflows — a natural moment to discuss integration and automation.',
  },
  REGULATORY: {
    category: 'REGULATORY',
    priority: 'urgent',
    baseScore: 80,
    label: 'Regulatory / financial review',
    keywordHints: [
      'credit rating',
      'downgrade',
      'fitch',
      'moody',
      'S&P',
      'regulatory',
      'fine',
      'penalty',
      'lawsuit',
    ],
    defaultRationale:
      'Financial pressure makes revenue optimization a board-level priority — the case for Adonis writes itself.',
  },

  // ---------- STANDARD ----------
  STRATEGY_CHANGE: {
    category: 'STRATEGY_CHANGE',
    priority: 'standard',
    baseScore: 55,
    label: 'Revenue strategy change',
    keywordHints: ['strategic plan', 'restructuring', 'transformation', 'realignment'],
    defaultRationale: 'Strategic shifts often precede operational changes. Worth tracking.',
  },
  AUTOMATION_INITIATIVE: {
    category: 'AUTOMATION_INITIATIVE',
    priority: 'standard',
    baseScore: 65,
    label: 'AI / automation initiative',
    keywordHints: [
      'AI',
      'artificial intelligence',
      'automation',
      'machine learning',
      'announces partnership',
    ],
    defaultRationale:
      "They're already buying. The question is whether they're buying the right thing.",
  },
  PARTNERSHIP: {
    category: 'PARTNERSHIP',
    priority: 'standard',
    baseScore: 50,
    label: 'New partnership or joint venture',
    keywordHints: ['partnership', 'joint venture', 'collaborates with', 'announces alliance'],
    defaultRationale: 'Partnership patterns reveal where they invest and who they trust.',
  },
  FINANCIAL_PERFORMANCE: {
    category: 'FINANCIAL_PERFORMANCE',
    priority: 'standard',
    baseScore: 60,
    label: 'Financial performance',
    keywordHints: [
      'earnings',
      'revenue',
      'margin',
      'losses',
      'profitable',
      'Q1',
      'Q2',
      'Q3',
      'Q4',
      'fiscal',
    ],
    defaultRationale:
      'Margin pressure makes revenue recovery a CFO priority. Performance trends shape urgency.',
  },
  LEADERSHIP_OTHER: {
    category: 'LEADERSHIP_OTHER',
    priority: 'standard',
    baseScore: 35,
    label: 'Other leadership change',
    keywordHints: ['appointed', 'named', 'joins'],
    defaultRationale: 'Useful context, even if not a direct decision-maker.',
  },
  REFERENCE_MATERIAL: {
    category: 'REFERENCE_MATERIAL',
    priority: 'standard',
    baseScore: 25,
    label: 'Interview / podcast / post',
    keywordHints: ['interview', 'podcast', 'spoke at', 'panel', 'op-ed', 'wrote'],
    defaultRationale:
      'Useful for meeting prep — quote them or reference their position. Not alert-worthy on its own.',
  },
};

/**
 * Phrases that should DOWNGRADE a signal to noise.
 * Used as a sanity check after categorization.
 */
export const NOISE_PATTERNS: string[] = [
  // Equipment / facilities — explicitly out of scope per Reed
  'MRI machine',
  'CT scanner',
  'new wing',
  'building',
  'renovation',
  'parking',
  'cafeteria',
  // Clinical news — different audience
  'clinical trial',
  'cancer treatment',
  'study finds',
  'researchers',
  'patients responded',
  // Community / awards
  'gala',
  'fundraiser',
  'awards ceremony',
  'community event',
  'philanthropy',
];

/**
 * Quickly classify a piece of text as likely-noise.
 * First-pass filter before we spend tokens on an LLM call.
 */
export function isLikelyNoise(text: string): boolean {
  const lower = text.toLowerCase();
  return NOISE_PATTERNS.some((p) => lower.includes(p.toLowerCase()));
}

/**
 * The priority threshold for firing an instant Slack alert vs. waiting for the weekly digest.
 * Tuned by Danielle in week 2-3 based on real signal volume.
 */
export const ALERT_SCORE_THRESHOLD = 75;

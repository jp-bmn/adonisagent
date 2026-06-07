/**
 * Core data types for the Adonis Account Intelligence system.
 *
 * These types are the contract between the web app, the agents, and the database.
 * If you change one of these, both sides update together.
 */

// ============================================================
// Hospital — a prospect account we monitor
// ============================================================

export interface Hospital {
  id: string;
  name: string;
  /** Canonical short name used for display, e.g. 'NewYork-Presbyterian' */
  display_name: string;
  /** Parent system if applicable, e.g. 'Mount Sinai Health System' for 'Mount Sinai Beth Israel' */
  parent_system: string | null;
  /** State (US) — used for territory assignment */
  state: string;
  /** City, used for display */
  city: string | null;
  /** Hospital website root, e.g. 'https://nyp.org' */
  website: string | null;
  /** Newsroom URL if known, scraped on a regular cadence */
  newsroom_url: string | null;
  /** A short note about why this hospital is being tracked */
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================
// Contact — a person at a hospital we care about
// ============================================================

export type RevenueRole =
  | 'CRO' // Chief Revenue Officer
  | 'CFO' // Chief Financial Officer
  | 'VP_REV_CYCLE' // VP / Director of Revenue Cycle
  | 'COO'
  | 'CIO'
  | 'CEO'
  | 'OTHER';

export interface Contact {
  id: string;
  hospital_id: string;
  full_name: string;
  role: RevenueRole;
  role_title_raw: string; // The exact title as scraped, before normalization
  /** Previous employer, if known */
  prior_employer: string | null;
  /** How recently they started this role */
  start_date: string | null;
  /** Source URL where we confirmed this contact */
  source_url: string | null;
  /** Has this person changed recently? Drives the 'NEW' badge in the UI. */
  is_recent_change: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================
// Signal — a single piece of intelligence about a hospital
// ============================================================

/**
 * Signal categories, locked down with Reed and Danielle in the kickoff.
 * Driven by what changes a sales conversation, not what's interesting in general.
 */
export type SignalCategory =
  // Urgent — instant alert
  | 'LEADERSHIP_HIRE' // New CRO, CFO, VP RCM, etc.
  | 'LEADERSHIP_DEPARTURE' // Senior revenue/finance leader leaves
  | 'MERGER_ACQUISITION'
  | 'VENDOR_CHANGE' // RCM vendor swap, outsourcing change
  | 'EPIC_EVENT' // Epic go-live, migration, expansion
  | 'REGULATORY' // Regulatory concern, credit-rating change
  // Standard — weekly digest
  | 'STRATEGY_CHANGE'
  | 'AUTOMATION_INITIATIVE'
  | 'PARTNERSHIP'
  | 'FINANCIAL_PERFORMANCE'
  | 'LEADERSHIP_OTHER' // Non-revenue exec changes
  | 'REFERENCE_MATERIAL'; // Interview, podcast, LinkedIn post — context, not alert

/** Priority drives delivery: urgent → surface immediately in the dashboard + flag in next digest; standard → weekly digest */
export type SignalPriority = 'urgent' | 'standard' | 'noise';

export interface Signal {
  id: string;
  hospital_id: string;
  /** Optional — if the signal is about a specific person */
  contact_id: string | null;
  category: SignalCategory;
  priority: SignalPriority;
  /** Short headline for the UI: 'New CRO appointed' */
  headline: string;
  /** Longer LLM-generated summary, ~2-3 sentences */
  summary: string;
  /** The 'why this matters' rationale for the sales rep */
  rationale: string;
  /** Source URL — every signal must link back somewhere */
  source_url: string;
  /** Where the signal came from, e.g. 'beckers' | 'newsapi' | 'hospital_newsroom' */
  source_type: string;
  /** Publication date of the source content, if known */
  published_at: string | null;
  /** When we ingested this signal */
  detected_at: string;
  /** Numeric score 0-100 from the scoring model */
  score: number;
  /** Has this signal been included in a digest yet? */
  delivered_in_digest: boolean;
  /** Has an instant alert been fired for this signal? */
  alert_fired: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================
// User — the four people who use the tool
// ============================================================

/**
 * Per Joel's PRD: Danielle is the admin (full visibility, compiles & sends the digest).
 * Michael, Jeff, and David are AEs with territory-filtered views.
 */
export type UserRole = 'admin' | 'ae';

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  /** Territory the AE covers, e.g. 'Northeast' | 'West'. Admins see all territories. */
  territory: string | null;
  /** Hospitals assigned to this user (by hospital_id). Empty for admin (sees all). */
  assigned_hospital_ids: string[];
  created_at: string;
  updated_at: string;
}

// ============================================================
// Digest — Monday email briefing
// ============================================================

export interface Digest {
  id: string;
  /** User who received the digest (typically the admin, who then forwards to AEs) */
  user_id: string;
  /** ISO date string for the Monday this digest was sent */
  week_of: string;
  /** Signal IDs included in this digest */
  signal_ids: string[];
  /** Rendered HTML body of the email */
  rendered_html: string;
  /** Provider message ID (Resend / SendGrid) for tracking delivery */
  email_message_id: string | null;
  delivered_at: string;
  created_at: string;
}

// ============================================================
// Alert — flagged urgent signal in the dashboard
// (No instant push for MVP — surfaces in dashboard + next digest;
//  email notifications can be added in Phase 2.)
// ============================================================

export interface Alert {
  id: string;
  user_id: string;
  signal_id: string;
  /** Email body if we end up sending an immediate notification */
  rendered_text: string;
  /** Provider message ID if a notification was sent; null if dashboard-only */
  email_message_id: string | null;
  delivered_at: string;
  created_at: string;
}

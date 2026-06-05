/**
 * API client for the Adonis Account Intelligence backend.
 * Base URL: https://adonisagents-production.up.railway.app/api/v1
 * Auth: X-User-Id header (Danielle's admin ID hardcoded until T-11 wires real auth)
 */

const BASE_URL = 'https://adonisagents-production.up.railway.app/api/v1';

// Danielle's admin ID — sees all hospitals and signals.
// Swapped for the real session user in T-11.
const DEFAULT_USER_ID = 'df7c14fd-cde3-4025-be00-ca42f4d31741';

// ---------------------------------------------------------------------------
// Types — derived from live API responses (backend uses snake_case field names)
// ---------------------------------------------------------------------------

export type SignalTier = 'urgent' | 'worth_knowing' | 'filtered_out';

export type SignalType =
  | 'ai_adoption_outside_rcm'
  | 'automation_proof'
  | 'epic_go_live'
  | 'filtered_out'
  | 'financial_event'
  | 'leadership_change'
  | 'ma_acquisition'
  | 'named_automation_owner'
  | 'new_hospital_launch'
  | 'post_golive_friction'
  | 'rcm_hiring_spike'
  | 'restructuring'
  | 'thought_leadership'
  | 'vendor_change'
  | 'vendor_dispute';

export type ReviewStatus = 'pending' | 'approved' | 'dismissed';

export interface ApiSignal {
  id: string;
  hospital_id: string;
  signal_type: SignalType;
  tier: SignalTier;
  confidence_score: number;
  review_status: ReviewStatus;
  title: string | null;
  summary: string | null;
  source_url: string;
  source_name: string | null;
  published_date: string | null;
  created_at: string;
  included_in_digest: boolean;
  urgent_sent: boolean;
}

export interface ApiHospital {
  id: string;
  name: string;
  website_url: string | null;
  division_note: string | null;
  created_at: string;
  ae_users: ApiAeUser[];
}

export interface ApiAeUser {
  id: string;
  name: string;
  is_admin: boolean;
}

export interface ApiMe {
  id: string;
  name: string;
  is_admin: boolean;
}

export interface ApiStatus {
  api_version: string;
  last_scraper_run: string | null;
  next_scraper_run: string | null;
  total_signals_stored: number;
  total_hospitals_monitored: number;
  pending_review_count: number;
  message: string;
}

// ---------------------------------------------------------------------------
// Display labels for each signal_type — used in SignalCard badge
// ---------------------------------------------------------------------------

export const SIGNAL_TYPE_LABELS: Record<SignalType, string> = {
  leadership_change:        'Leadership change',
  epic_go_live:             'Epic go-live',
  vendor_change:            'Vendor change',
  vendor_dispute:           'Vendor dispute',
  ma_acquisition:           'M&A activity',
  financial_event:          'Financial event',
  rcm_hiring_spike:         'RCM hiring',
  restructuring:            'Restructuring',
  automation_proof:         'Automation',
  ai_adoption_outside_rcm:  'AI adoption',
  named_automation_owner:   'Automation owner',
  new_hospital_launch:      'New launch',
  post_golive_friction:     'Post go-live',
  thought_leadership:       'Thought leadership',
  filtered_out:             'Filtered out',
};

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  userId: string = DEFAULT_USER_ID,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId,
      ...init?.headers,
    },
    next: { revalidate: 60 }, // Next.js cache: revalidate every 60s
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export async function fetchHospitals(userId?: string): Promise<ApiHospital[]> {
  return apiFetch<ApiHospital[]>('/hospitals', userId);
}

export async function fetchSignals(
  userId?: string,
  opts: { tier?: SignalTier; ae_id?: string; limit?: number } = {}
): Promise<ApiSignal[]> {
  const params = new URLSearchParams();
  if (opts.tier)   params.set('tier', opts.tier);
  if (opts.ae_id)  params.set('ae_id', opts.ae_id);
  if (opts.limit)  params.set('limit', String(opts.limit));
  const qs = params.size > 0 ? `?${params}` : '';
  return apiFetch<ApiSignal[]>(`/signals${qs}`, userId);
}

export async function fetchHospitalSignals(
  hospitalId: string,
  userId?: string
): Promise<ApiSignal[]> {
  return apiFetch<ApiSignal[]>(`/hospitals/${hospitalId}/signals`, userId);
}

export async function fetchMe(userId: string): Promise<ApiMe> {
  return apiFetch<ApiMe>('/me', userId);
}

export async function fetchStatus(userId?: string): Promise<ApiStatus> {
  return apiFetch<ApiStatus>('/status', userId);
}

export async function fetchPendingReview(userId?: string): Promise<ApiSignal[]> {
  return apiFetch<ApiSignal[]>('/signals/pending-review', userId);
}

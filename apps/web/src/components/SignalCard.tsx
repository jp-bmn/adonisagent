import type { Signal } from '@adonis/shared';
import { SIGNAL_CONFIG } from '@adonis/shared';

interface SignalCardProps {
  signal: Signal;
  /** Display name of the hospital — pass from the parent. Falls back to hospital_id. */
  hospitalName?: string;
}

export default function SignalCard({ signal, hospitalName }: SignalCardProps) {
  const config = SIGNAL_CONFIG[signal.category];
  const isUrgent = signal.priority === 'urgent';

  return (
    <div className="bg-white border border-line rounded-xl p-5 space-y-3">
      {/* Top row: badge + hospital tag */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span
            className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded font-semibold ${
              isUrgent ? 'bg-urgentBg text-urgent' : 'bg-standard/10 text-standard'
            }`}
          >
            {isUrgent ? 'Urgent' : 'Update'}
          </span>
          <span className="text-xs text-slate-500">{config.label}</span>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {hospitalName ?? signal.hospital_id}
        </span>
      </div>

      {/* Headline */}
      <p className="font-serif text-base font-semibold text-ink leading-snug">{signal.headline}</p>

      {/* Summary */}
      <p className="text-sm text-slate-600 leading-relaxed">{signal.summary}</p>

      {/* Rationale */}
      <div className="border-l-2 border-line pl-3">
        <p className="text-xs text-slate-500 leading-relaxed">
          <span className="font-semibold text-slate-600">Why this matters · </span>
          {signal.rationale}
        </p>
      </div>

      {/* Footer: source + date */}
      <div className="flex items-center justify-between gap-3 pt-1">
        <a
          href={signal.source_url}
          target="_blank"
          rel="noreferrer"
          className="text-xs text-accent hover:underline truncate max-w-[60%]"
        >
          {sourceHostname(signal.source_url)}
        </a>
        <span className="text-xs text-slate-400 flex-none">
          {formatDate(signal.published_at ?? signal.detected_at)}
        </span>
      </div>
    </div>
  );
}

function sourceHostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// ---------------------------------------------------------------------------
// Preview signals — development only, remove before production
// ---------------------------------------------------------------------------
export const PREVIEW_SIGNALS: Signal[] = [
  {
    id: 'preview-1',
    hospital_id: 'nyp',
    contact_id: null,
    category: 'LEADERSHIP_HIRE',
    priority: 'urgent',
    headline: 'New CFO appointed at NewYork-Presbyterian',
    summary:
      'NewYork-Presbyterian has named Dr. Sarah Chen as its new Chief Financial Officer, effective March 1. Chen joins from Mount Sinai Health System, where she led a multi-year revenue cycle transformation that reduced denial rates by 22%.',
    rationale: SIGNAL_CONFIG.LEADERSHIP_HIRE.defaultRationale,
    source_url: 'https://www.nyp.org/news/cfo-appointment-2026',
    source_type: 'hospital_newsroom',
    published_at: '2026-05-28T09:00:00Z',
    detected_at: '2026-05-28T10:14:00Z',
    score: 92,
    delivered_in_digest: false,
    alert_fired: false,
    created_at: '2026-05-28T10:14:00Z',
    updated_at: '2026-05-28T10:14:00Z',
  },
  {
    id: 'preview-2',
    hospital_id: 'commonspirit',
    contact_id: null,
    category: 'EPIC_EVENT',
    priority: 'urgent',
    headline: 'CommonSpirit completes Epic migration across 40 facilities',
    summary:
      "CommonSpirit Health announced the completion of its Epic EHR rollout across 40 facilities in the Mountain Division, the largest single-phase go-live in the system's history. The migration affects approximately 6,200 clinicians and will consolidate billing operations previously split across three legacy platforms.",
    rationale: SIGNAL_CONFIG.EPIC_EVENT.defaultRationale,
    source_url: 'https://www.beckershospitalreview.com/ehrs/commonspirit-epic-migration.html',
    source_type: 'beckers',
    published_at: '2026-05-30T14:00:00Z',
    detected_at: '2026-05-30T15:02:00Z',
    score: 81,
    delivered_in_digest: false,
    alert_fired: false,
    created_at: '2026-05-30T15:02:00Z',
    updated_at: '2026-05-30T15:02:00Z',
  },
  {
    id: 'preview-3',
    hospital_id: 'umass-memorial',
    contact_id: null,
    category: 'FINANCIAL_PERFORMANCE',
    priority: 'standard',
    headline: 'UMass Memorial reports $47M operating loss in FY2025',
    summary:
      'UMass Memorial Health posted a $47 million operating loss for FY2025, citing increased labor costs and declining reimbursement rates. CFO David Polakoff noted the system is actively evaluating "revenue cycle performance improvements" as a key lever for FY2026 recovery.',
    rationale: SIGNAL_CONFIG.FINANCIAL_PERFORMANCE.defaultRationale,
    source_url: 'https://www.modernhealthcare.com/finance/umass-memorial-fy2025-results',
    source_type: 'serper',
    published_at: '2026-05-25T11:30:00Z',
    detected_at: '2026-05-25T12:45:00Z',
    score: 68,
    delivered_in_digest: false,
    alert_fired: false,
    created_at: '2026-05-25T12:45:00Z',
    updated_at: '2026-05-25T12:45:00Z',
  },
];

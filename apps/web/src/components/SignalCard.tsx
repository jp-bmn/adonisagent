import type { ApiSignal } from '@/lib/api';
import { SIGNAL_TYPE_LABELS } from '@/lib/api';

interface SignalCardProps {
  signal: ApiSignal;
  /** Display name of the hospital — pass from the parent. Falls back to hospital_id. */
  hospitalName?: string;
}

export default function SignalCard({ signal, hospitalName }: SignalCardProps) {
  const isUrgent = signal.tier === 'urgent';
  // worth_knowing = standard digest signal; filtered_out should not be rendered
  const label = SIGNAL_TYPE_LABELS[signal.signal_type] ?? signal.signal_type;
  const headline = signal.title ?? label;
  const date = signal.published_date ?? signal.created_at;

  return (
    <div className="bg-white border border-line rounded-xl p-5 space-y-3">
      {/* Top row: tier badge + category label + hospital tag */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span
            className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded font-semibold ${
              isUrgent ? 'bg-urgentBg text-urgent' : 'bg-standard/10 text-standard'
            }`}
          >
            {isUrgent ? 'Urgent' : 'Update'}
          </span>
          <span className="text-xs text-slate-500">{label}</span>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {hospitalName ?? signal.hospital_id}
        </span>
      </div>

      {/* Headline */}
      <p className="font-serif text-base font-semibold text-ink leading-snug">{headline}</p>

      {/* Summary */}
      {signal.summary && (
        <p className="text-sm text-slate-600 leading-relaxed">{signal.summary}</p>
      )}

      {/* Footer: source + date */}
      <div className="flex items-center justify-between gap-3 pt-1">
        <a
          href={signal.source_url}
          target="_blank"
          rel="noreferrer"
          className="text-xs text-accent hover:underline truncate max-w-[60%]"
        >
          {signal.source_name ?? sourceHostname(signal.source_url)}
        </a>
        <span className="text-xs text-slate-400 flex-none">
          {formatDate(date)}
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
// Preview signals — matches real ApiSignal shape from the backend
// Used on the signal feed before live data is wired (T-04)
// ---------------------------------------------------------------------------
export const PREVIEW_SIGNALS: ApiSignal[] = [
  {
    id: 'preview-1',
    hospital_id: 'f0f6b915-3e9d-4040-ba4d-c89339a1e134',
    signal_type: 'leadership_change',
    tier: 'urgent',
    confidence_score: 92,
    review_status: 'approved',
    title: 'New CFO appointed at NewYork-Presbyterian',
    summary:
      'NewYork-Presbyterian has named Dr. Sarah Chen as Chief Financial Officer, effective March 1. Chen joins from Mount Sinai Health System where she led a revenue cycle transformation that reduced denial rates by 22%.',
    source_url: 'https://www.nyp.org/news/cfo-appointment-2026',
    source_name: 'NYP Newsroom',
    published_date: '2026-05-28T09:00:00Z',
    created_at: '2026-05-28T10:14:00Z',
    included_in_digest: false,
    urgent_sent: false,
  },
  {
    id: 'preview-2',
    hospital_id: '7b836e62-3ee8-4d10-b30e-028734a5f812',
    signal_type: 'epic_go_live',
    tier: 'urgent',
    confidence_score: 81,
    review_status: 'approved',
    title: 'CommonSpirit completes Epic migration across 40 facilities',
    summary:
      "CommonSpirit Health announced the completion of its Epic EHR rollout across 40 facilities in the Mountain Division, the largest single-phase go-live in the system's history. The migration consolidates billing operations previously split across three legacy platforms.",
    source_url: 'https://www.beckershospitalreview.com/ehrs/commonspirit-epic-migration.html',
    source_name: "Becker's Hospital Review",
    published_date: '2026-05-30T14:00:00Z',
    created_at: '2026-05-30T15:02:00Z',
    included_in_digest: false,
    urgent_sent: false,
  },
  {
    id: 'preview-3',
    hospital_id: 'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476',
    signal_type: 'financial_event',
    tier: 'worth_knowing',
    confidence_score: 68,
    review_status: 'approved',
    title: 'UMass Memorial reports $47M operating loss in FY2025',
    summary:
      'UMass Memorial Health posted a $47 million operating loss for FY2025, citing increased labor costs and declining reimbursement rates. CFO David Polakoff noted the system is actively evaluating revenue cycle performance improvements as a key lever for FY2026 recovery.',
    source_url: 'https://www.modernhealthcare.com/finance/umass-memorial-fy2025-results',
    source_name: 'Modern Healthcare',
    published_date: '2026-05-25T11:30:00Z',
    created_at: '2026-05-25T12:45:00Z',
    included_in_digest: false,
    urgent_sent: false,
  },
];

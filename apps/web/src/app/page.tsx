import Link from 'next/link';
import { Suspense } from 'react';
import { fetchSignals, fetchHospitals, fetchStatus, SignalType, SIGNAL_TYPE_LABELS } from '@/lib/api';
import { SignalCard, TerritoryFilter } from '@/components';
import SignalFilters from '@/components/SignalFilters';

interface PageProps {
  searchParams: Promise<{ ae_id?: string; category?: string; sort?: string }>;
}

const TIER_ORDER = { urgent: 0, worth_knowing: 1, filtered_out: 2 } as const;

export default async function HomePage({ searchParams }: PageProps) {
  const { ae_id, category, sort = 'urgent' } = await searchParams;

  const [allSignals, hospitals, status] = await Promise.all([
    fetchSignals(undefined, { ae_id }),
    fetchHospitals(),
    fetchStatus(),
  ]);

  const hospitalMap = Object.fromEntries(hospitals.map((h) => [h.id, h.name]));

  // Filter by category
  let signals = category
    ? allSignals.filter((s) => s.signal_type === (category as SignalType))
    : allSignals;

  // Sort
  signals = [...signals].sort((a, b) => {
    if (sort === 'recent') {
      return (
        new Date(b.published_date ?? b.created_at).getTime() -
        new Date(a.published_date ?? a.created_at).getTime()
      );
    }
    if (sort === 'hospital') {
      const nameA = hospitalMap[a.hospital_id] ?? '';
      const nameB = hospitalMap[b.hospital_id] ?? '';
      return nameA.localeCompare(nameB);
    }
    // Default: urgent first, then by date within each tier
    const tierDiff = TIER_ORDER[a.tier] - TIER_ORDER[b.tier];
    if (tierDiff !== 0) return tierDiff;
    return (
      new Date(b.published_date ?? b.created_at).getTime() -
      new Date(a.published_date ?? a.created_at).getTime()
    );
  });

  const urgentCount = allSignals.filter((s) => s.tier === 'urgent').length;
  const worthKnowingCount = allSignals.filter((s) => s.tier === 'worth_knowing').length;

  const aeMap = new Map<string, string>();
  hospitals.forEach((h) =>
    h.ae_users.forEach((u) => {
      if (!u.is_admin) aeMap.set(u.id, u.name);
    })
  );
  const aes = Array.from(aeMap.entries()).map(([id, name]) => ({ id, name }));

  return (
    <div className="px-4 py-5 md:px-8 md:py-7 pb-20 md:pb-7">
      <header className="flex items-end justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-brand">Signal Feed</h1>
          <p className="text-sm text-slate-500 mt-1">
            Live · agents run Mon/Wed/Fri · {allSignals.length} signals
          </p>
        </div>
        <Suspense>
          <TerritoryFilter aes={aes} />
        </Suspense>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Kpi value={urgentCount} label="Urgent this week" tone="urgent" stripeColor="#C44A2C" />
        <Kpi value={worthKnowingCount} label="Updates this week" stripeColor="#2D7B6C" />
        <Kpi value={hospitals.length} label="Accounts monitored" stripeColor="#0F3D3E" />
        <Kpi value={allSignals.length} label="Signals total" stripeColor="#DCEBE7" />
      </div>

      <Suspense>
        <SignalFilters />
      </Suspense>

      <div className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">
        {category ? `${category.replace(/_/g, ' ')} signals` : 'Recent signals'} ·{' '}
        {sort === 'recent' ? 'newest first' : sort === 'hospital' ? 'hospital A–Z' : 'most urgent first'}
      </div>

      {signals.length === 0 ? (
        <div className="bg-white border border-line rounded-xl p-10 text-center space-y-2">
          {category ? (
            <>
              <p className="text-sm font-semibold text-brand">
                No {SIGNAL_TYPE_LABELS[category as SignalType] ?? category.replace(/_/g, ' ')} signals this week.
              </p>
              <p className="text-xs text-slate-400">
                Try a different category, or check back Monday after the next agent run.
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-semibold text-brand">No signals yet.</p>
              <p className="text-xs text-slate-400">
                Agents run Mon / Wed / Fri — next update {nextAgentRun()}.
              </p>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-5">
          {signals.map((signal) => (
            <SignalCard
              key={signal.id}
              signal={signal}
              hospitalName={hospitalMap[signal.hospital_id]}
            />
          ))}
        </div>
      )}

      <footer className="mt-8 pt-5 border-t border-line flex items-center justify-between flex-wrap gap-4">
        <Link href="/hospitals" className="text-xs text-accent hover:underline">
          View all hospitals →
        </Link>
        <div className="flex items-center gap-5 text-xs font-mono text-slate-400 flex-wrap">
          {status.pending_review_count > 0 && (
            <Link href="/review" className="text-urgent font-semibold hover:underline">
              {status.pending_review_count} pending review
            </Link>
          )}
          <span>
            <span className="text-slate-500">last run:</span>{' '}
            {status.last_scraper_run ? formatDate(status.last_scraper_run) : 'never'}
          </span>
          <span>
            <span className="text-slate-500">next run:</span>{' '}
            {status.next_scraper_run ? formatDate(status.next_scraper_run) : 'scheduled'}
          </span>
          <span>
            <span className="text-slate-500">stored:</span> {status.total_signals_stored}
          </span>
          <span className="text-slate-300">v{status.api_version}</span>
        </div>
      </footer>
    </div>
  );
}

function nextAgentRun(): string {
  const now = new Date();
  const day = now.getDay();
  const targets = [1, 3, 5];
  const daysAhead = targets.map((t) => (t - day + 7) % 7 || 7);
  const next = new Date(now);
  next.setDate(now.getDate() + Math.min(...daysAhead));
  return next.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

type DeltaDirection = 'up' | 'down' | 'flat';

const PILL_STYLES: Record<DeltaDirection, { background: string; color: string }> = {
  up:   { background: '#FCE8E1', color: '#C44A2C' },
  down: { background: '#DCEBE7', color: '#2D7B6C' },
  flat: { background: '#F0F5F4', color: '#6b7480' },
};

function Kpi({
  value,
  label,
  tone,
  stripeColor,
  delta,
  deltaDirection,
}: {
  value: string | number;
  label: string;
  tone?: 'urgent';
  stripeColor: string;
  delta?: number | null;
  deltaDirection?: DeltaDirection | null;
}) {
  return (
    <div className="bg-white border border-line rounded-xl p-4 relative overflow-hidden">
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: stripeColor }} />
      <div className={`font-serif text-2xl font-bold ${tone === 'urgent' ? 'text-urgent' : 'text-brand'}`}>
        {value}
      </div>
      <div className="text-xs text-slate-500 mt-1">{label}</div>
      {delta != null && deltaDirection && (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 7px', borderRadius: '10px', fontFamily: 'ui-monospace, monospace', fontSize: '10px', fontWeight: 600, marginTop: '8px', letterSpacing: '0.02em', ...PILL_STYLES[deltaDirection] }}>
          {deltaDirection === 'up' && `↑ ${delta} vs last week`}
          {deltaDirection === 'down' && `↓ ${delta} vs last week`}
          {deltaDirection === 'flat' && 'same as last week'}
        </div>
      )}
    </div>
  );
}

import Link from 'next/link';
import { Suspense } from 'react';
import { fetchSignals, fetchHospitals, fetchStatus } from '@/lib/api';
import { SignalCard, TerritoryFilter } from '@/components';

interface PageProps {
  searchParams: Promise<{ ae_id?: string }>;
}

export default async function HomePage({ searchParams }: PageProps) {
  const { ae_id } = await searchParams;
  const [signals, hospitals, status] = await Promise.all([
    fetchSignals(undefined, { ae_id }),
    fetchHospitals(),
    fetchStatus(),
  ]);

  const hospitalMap = Object.fromEntries(hospitals.map((h) => [h.id, h.name]));
  const urgentCount = signals.filter((s) => s.tier === 'urgent').length;
  const worthKnowingCount = signals.filter((s) => s.tier === 'worth_knowing').length;

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
            Live · agents run Mon/Wed/Fri · {signals.length} signals
          </p>
        </div>
        <Suspense>
          <TerritoryFilter aes={aes} />
        </Suspense>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Kpi
          value={status.urgent_count ?? urgentCount}
          label="Urgent this week"
          tone="urgent"
          delta={status.urgent_delta}
          deltaDirection={status.urgent_delta_direction}
        />
        <Kpi
          value={status.worth_knowing_count ?? worthKnowingCount}
          label="Updates this week"
          delta={status.worth_knowing_delta}
          deltaDirection={status.worth_knowing_delta_direction}
        />
        <Kpi value={hospitals.length} label="Accounts monitored" />
        <Kpi value={signals.length} label="Signals total" />
      </div>

      <div className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">
        Recent signals · newest first
      </div>

      {signals.length === 0 ? (
        <div className="bg-white border border-line rounded-xl p-10 text-center text-sm text-slate-500">
          No signals yet — agents will populate this on the next scheduled run.
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

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function Kpi({
  value,
  label,
  tone,
  delta,
  deltaDirection,
}: {
  value: string | number;
  label: string;
  tone?: 'urgent';
  delta?: number;
  deltaDirection?: 'up' | 'down' | 'flat';
}) {
  const showDelta = delta !== undefined && deltaDirection !== undefined;

  return (
    <div className="bg-white border border-line rounded-xl p-4 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <div
            className={`font-serif text-2xl font-bold ${
              tone === 'urgent' ? 'text-urgent' : 'text-brand'
            }`}
          >
            {value}
          </div>
          {showDelta && (
            <div
              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-0.5 ${
                deltaDirection === 'up'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/50'
                  : deltaDirection === 'down'
                    ? 'bg-rose-50 text-rose-700 border border-rose-200/50'
                    : 'bg-slate-50 text-slate-500 border border-slate-200/50'
              }`}
            >
              <span>{deltaDirection === 'up' ? '↑' : deltaDirection === 'down' ? '↓' : '→'}</span>
              <span>{Math.abs(delta)}</span>
            </div>
          )}
        </div>
        <div className="text-xs text-slate-500 mt-1">{label}</div>
      </div>
    </div>
  );
}

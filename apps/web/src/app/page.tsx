import Link from 'next/link';
import { fetchSignals, fetchHospitals } from '@/lib/api';
import { SignalCard } from '@/components';

export default async function HomePage() {
  const [signals, hospitals] = await Promise.all([fetchSignals(), fetchHospitals()]);

  const hospitalMap = Object.fromEntries(hospitals.map((h) => [h.id, h.name]));
  const urgentCount = signals.filter((s) => s.tier === 'urgent').length;
  const worthKnowingCount = signals.filter((s) => s.tier === 'worth_knowing').length;

  return (
    <div className="px-8 py-7">
      <header className="flex items-end justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-ink">Signal Feed</h1>
          <p className="text-sm text-slate-500 mt-1">
            Live · agents run Mon/Wed/Fri · {signals.length} signals
          </p>
        </div>
        <div className="bg-white border border-line rounded-lg px-3 py-1.5 text-xs font-mono text-slate-600">
          Territory: <strong className="text-ink">Admin (Danielle)</strong> · {hospitals.length}{' '}
          accounts
        </div>
      </header>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <Kpi value={urgentCount} label="Urgent this week" tone="urgent" />
        <Kpi value={worthKnowingCount} label="Updates this week" />
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
        <div className="space-y-3">
          {signals.map((signal) => (
            <SignalCard
              key={signal.id}
              signal={signal}
              hospitalName={hospitalMap[signal.hospital_id]}
            />
          ))}
        </div>
      )}

      <div className="mt-8 text-xs text-slate-500">
        <Link href="/hospitals" className="text-accent hover:underline">
          View all hospitals →
        </Link>
      </div>
    </div>
  );
}

function Kpi({
  value,
  label,
  tone,
}: {
  value: string | number;
  label: string;
  tone?: 'urgent';
}) {
  return (
    <div className="bg-white border border-line rounded-xl p-4">
      <div
        className={`font-serif text-2xl font-bold ${
          tone === 'urgent' ? 'text-urgent' : 'text-navy-900'
        }`}
      >
        {value}
      </div>
      <div className="text-xs text-slate-500 mt-1">{label}</div>
    </div>
  );
}

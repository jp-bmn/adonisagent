import Link from 'next/link';
import { SignalCard, PREVIEW_SIGNALS } from '@/components';

// Hospital name lookup using real backend UUIDs
const HOSPITAL_NAMES: Record<string, string> = {
  'f0f6b915-3e9d-4040-ba4d-c89339a1e134': 'NewYork-Presbyterian',
  'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476': 'UMass Memorial',
  'a4725891-7354-4187-a6c1-93d7ea9a078f': 'Ascension',
  '3aebd89a-1d2c-465c-a22b-08ced9613027': 'UAMS',
  '7b836e62-3ee8-4d10-b30e-028734a5f812': 'CommonSpirit',
};

export default function HomePage() {
  // TODO T-04: replace PREVIEW_SIGNALS with fetchSignals() from @/lib/api
  const signals = PREVIEW_SIGNALS;
  const urgentCount = signals.filter((s) => s.tier === 'urgent').length;
  const standardCount = signals.filter((s) => s.tier === 'worth_knowing').length;

  return (
    <div className="px-8 py-7">
      <header className="flex items-end justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-ink">Signal Feed</h1>
          <p className="text-sm text-slate-500 mt-1">
            Last refreshed — placeholder · agents run Mon/Wed/Fri
          </p>
        </div>
        <div className="bg-white border border-line rounded-lg px-3 py-1.5 text-xs font-mono text-slate-600">
          Territory: <strong className="text-ink">Admin (Danielle)</strong> · 5 accounts
        </div>
      </header>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <Kpi value={urgentCount} label="Urgent this week" tone="urgent" />
        <Kpi value={standardCount} label="Updates this week" />
        <Kpi value={5} label="Accounts monitored" />
        <Kpi value="0" label="Sources scanned" />
      </div>

      <div className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">
        Recent signals · newest first
      </div>

      <div className="space-y-3">
        {signals.map((signal) => (
          <SignalCard
            key={signal.id}
            signal={signal}
            hospitalName={HOSPITAL_NAMES[signal.hospital_id]}
          />
        ))}
      </div>

      <div className="mt-8 text-xs text-slate-500">
        <Link href="/hospitals" className="text-accent hover:underline">
          View all hospitals →
        </Link>
      </div>
    </div>
  );
}

function Kpi({ value, label, tone }: { value: string | number; label: string; tone?: 'urgent' }) {
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

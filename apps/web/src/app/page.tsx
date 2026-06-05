import Link from 'next/link';
import { SEED_HOSPITALS } from '@adonis/shared';

export default function HomePage() {
  // TODO: when DB is wired, replace with: const signals = await listSignals(db, { limit: 20 });
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
          Territory: <strong className="text-ink">Admin (Danielle)</strong> ·{' '}
          {SEED_HOSPITALS.length} accounts
        </div>
      </header>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <Kpi value="0" label="Urgent this week" tone="urgent" />
        <Kpi value="0" label="Updates this week" />
        <Kpi value={SEED_HOSPITALS.length} label="Accounts monitored" />
        <Kpi value="0" label="Sources scanned" />
      </div>

      <div className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-3">
        Recent signals · newest first
      </div>

      <div className="bg-white border border-line rounded-lg p-6 text-center text-slate-500">
        <p className="mb-2 text-sm">No signals yet — the agent worker has not run.</p>
        <p className="text-xs">
          Run{' '}
          <code className="px-1.5 py-0.5 bg-paper rounded text-ink font-mono">
            pnpm --filter @adonis/agents scrape:once
          </code>{' '}
          to pull from sources, or wait for the next scheduled Mon/Wed/Fri run.
        </p>
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

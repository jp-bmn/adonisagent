import { fetchSignals, fetchHospitals } from '@/lib/api';
import { SignalCard } from '@/components';

export default async function AlertsPage() {
  const [signals, hospitals] = await Promise.all([
    fetchSignals(undefined, { tier: 'urgent' }),
    fetchHospitals(),
  ]);

  const hospitalMap = Object.fromEntries(hospitals.map((h) => [h.id, h.name]));

  return (
    <div className="px-8 py-7">
      <header className="mb-6">
        <h1 className="font-serif text-2xl font-semibold text-ink">Alerts</h1>
        <p className="text-sm text-slate-500 mt-1">
          Urgent signals across all accounts · {signals.length} total
        </p>
      </header>

      {signals.length === 0 ? (
        <div className="bg-white border border-line rounded-xl p-10 text-center text-sm text-slate-500">
          No urgent signals yet. Urgent signals appear here as soon as the agent detects them.
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
    </div>
  );
}

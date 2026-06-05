import { notFound } from 'next/navigation';
import Link from 'next/link';
import { fetchHospitals, fetchHospitalSignals } from '@/lib/api';
import { SignalCard } from '@/components';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function HospitalProfilePage({ params }: PageProps) {
  const { id } = await params;

  const [hospitals, signals] = await Promise.all([fetchHospitals(), fetchHospitalSignals(id)]);

  const hospital = hospitals.find((h) => h.id === id);
  if (!hospital) return notFound();

  const aes = hospital.ae_users.filter((u) => !u.is_admin);
  const urgentCount = signals.filter((s) => s.tier === 'urgent').length;

  return (
    <div className="px-8 py-7">
      <Link href="/hospitals" className="text-xs text-accent hover:underline">
        ← All hospitals
      </Link>

      <div className="bg-white border border-line rounded-xl overflow-hidden mt-3">
        {/* Header */}
        <div className="px-6 py-5 border-b border-line bg-gradient-to-b from-white to-paper flex gap-5">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-navy-900 to-navy-700 text-white flex items-center justify-center font-serif font-bold text-2xl flex-none">
            {hospital.name[0]}
          </div>
          <div className="flex-1">
            <h1 className="font-serif text-2xl font-semibold text-ink leading-tight">
              {hospital.name}
            </h1>
            <div className="text-sm text-slate-500 mt-1 flex items-center gap-3 flex-wrap">
              {hospital.division_note && <span>{hospital.division_note}</span>}
              {hospital.website_url && (
                <a
                  href={hospital.website_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-accent hover:underline"
                >
                  {hospital.website_url.replace(/^https?:\/\//, '')}
                </a>
              )}
            </div>
            {aes.length > 0 && (
              <div className="text-xs text-slate-500 mt-2">
                AE:{' '}
                <span className="font-medium text-ink">{aes.map((u) => u.name).join(', ')}</span>
              </div>
            )}
          </div>
          <div className="flex gap-4 flex-none text-right">
            <div>
              <div className="font-serif text-2xl font-bold text-urgent">{urgentCount}</div>
              <div className="text-xs text-slate-500">Urgent</div>
            </div>
            <div>
              <div className="font-serif text-2xl font-bold text-navy-900">{signals.length}</div>
              <div className="text-xs text-slate-500">Total signals</div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="grid grid-cols-2">
          <section className="p-6 border-r border-line">
            <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-4">
              Revenue &amp; finance leadership
            </h2>
            <p className="text-sm text-slate-500">
              No contacts loaded yet. Once the agent worker runs, key revenue and finance leaders
              will appear here with their backgrounds and any recent role changes flagged.
            </p>
          </section>

          <section className="p-6">
            <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-4">
              Signal history · {signals.length} total
            </h2>
            {signals.length === 0 ? (
              <p className="text-sm text-slate-500">
                No signals yet. The agent monitors this hospital on Mon/Wed/Fri.
              </p>
            ) : (
              <div className="space-y-3">
                {signals.map((signal) => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

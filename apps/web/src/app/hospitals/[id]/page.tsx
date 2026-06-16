import { notFound } from 'next/navigation';
import Link from 'next/link';
import { fetchHospitals, fetchHospitalSignals, fetchHospitalContacts } from '@/lib/api';
import { SignalCard, HospitalLogo } from '@/components';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function HospitalProfilePage({ params }: PageProps) {
  const { id } = await params;

  const [hospitals, signals, contacts] = await Promise.all([
    fetchHospitals(),
    fetchHospitalSignals(id),
    fetchHospitalContacts(id).catch(() => []),
  ]);

  const hospital = hospitals.find((h) => h.id === id);
  if (!hospital) return notFound();

  const aes = hospital.ae_users.filter((u) => !u.is_admin);
  const urgentCount = signals.filter((s) => s.tier === 'urgent').length;

  return (
    <div className="px-4 py-5 md:px-8 md:py-7 pb-20 md:pb-7">
      <Link href="/hospitals" className="text-xs text-accent hover:underline">
        ← All hospitals
      </Link>

      <div className="bg-white border border-line rounded-xl overflow-hidden mt-3">
        {/* Header */}
        <div className="px-4 md:px-6 py-5 border-b border-line bg-gradient-to-b from-white to-paper flex flex-wrap gap-4">
          <HospitalLogo name={hospital.name} websiteUrl={hospital.website_url} size="lg" />
          <div className="flex-1 min-w-0">
            <h1 className="font-serif text-xl md:text-2xl font-semibold text-brand leading-tight">
              {hospital.name}
            </h1>
            <div className="text-sm text-slate-500 mt-1 flex items-center gap-3 flex-wrap">
              {hospital.division_note && <span>{hospital.division_note}</span>}
              {hospital.website_url && (
                <a
                  href={hospital.website_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-accent hover:underline truncate"
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
            {/* Stats inline below name on mobile */}
            <div className="flex gap-5 mt-3 md:hidden">
              <div>
                <div className="font-serif text-xl font-bold text-urgent">{urgentCount}</div>
                <div className="text-xs text-slate-500">Urgent</div>
              </div>
              <div>
                <div className="font-serif text-xl font-bold text-brand">{signals.length}</div>
                <div className="text-xs text-slate-500">Total signals</div>
              </div>
            </div>
          </div>
          {/* Stats on right — desktop only */}
          <div className="hidden md:flex gap-4 flex-none text-right self-start">
            <div>
              <div className="font-serif text-2xl font-bold text-urgent">{urgentCount}</div>
              <div className="text-xs text-slate-500">Urgent</div>
            </div>
            <div>
              <div className="font-serif text-2xl font-bold text-brand">{signals.length}</div>
              <div className="text-xs text-slate-500">Total signals</div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="grid grid-cols-1 md:grid-cols-2">
          <section className="p-4 md:p-6 border-b md:border-b-0 md:border-r border-line">
            <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-4">
              Revenue &amp; finance leadership
            </h2>
            {contacts.length === 0 ? (
              <p className="text-sm text-slate-500">
                No contacts loaded yet. The agent will populate key revenue and finance leaders on
                the next scheduled run.
              </p>
            ) : (
              <div className="space-y-4">
                {contacts.map((c) => (
                  <div key={c.id} className="flex flex-col gap-1">
                    <div className="text-sm font-semibold text-ink">
                      {c.full_name || 'Unknown contact'}
                    </div>
                    {c.role && <div className="text-xs text-slate-500">{c.role}</div>}
                    {c.prior_employer && (
                      <div className="text-xs text-slate-400">prev. {c.prior_employer}</div>
                    )}
                    <div className="flex items-center gap-3 flex-wrap">
                      {c.linkedin_url && (
                        <a
                          href={c.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-accent hover:underline"
                        >
                          ↗ LinkedIn
                        </a>
                      )}
                      {c.email && (
                        <a
                          href={`mailto:${c.email}`}
                          className="text-[10px] font-mono text-slate-400 hover:underline"
                        >
                          {c.email}
                        </a>
                      )}
                    </div>

                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="p-4 md:p-6">
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
                  <SignalCard key={signal.id} signal={signal} hospitalName={hospital.name} />
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

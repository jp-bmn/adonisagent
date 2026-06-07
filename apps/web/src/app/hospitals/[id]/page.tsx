import { notFound } from 'next/navigation';
import Link from 'next/link';
import { SEED_HOSPITALS } from '@adonis/shared';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function HospitalProfilePage({ params }: PageProps) {
  const { id } = await params;
  const hospital = SEED_HOSPITALS.find((h) => h.id === id);
  if (!hospital) return notFound();

  // TODO: load contacts and signals from DB
  // const contacts = await listContactsForHospital(db, id);
  // const signals = await listSignals(db, { hospitalIds: [id] });

  return (
    <div className="px-8 py-7">
      <Link href="/hospitals" className="text-xs text-accent hover:underline">
        ← All hospitals
      </Link>

      <div className="bg-white border border-line rounded-xl overflow-hidden mt-3">
        <div className="px-6 py-5 border-b border-line bg-gradient-to-b from-white to-paper flex gap-5">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-navy-900 to-navy-700 text-white flex items-center justify-center font-serif font-bold text-2xl flex-none">
            {hospital.display_name[0]}
          </div>
          <div className="flex-1">
            <h1 className="font-serif text-2xl font-semibold text-ink leading-tight">
              {hospital.display_name}
            </h1>
            <div className="text-sm text-slate-500 mt-1">
              {hospital.city ? `${hospital.city}, ` : ''}
              {hospital.state}
              {hospital.website && (
                <>
                  {' · '}
                  <a
                    href={hospital.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-accent hover:underline"
                  >
                    {hospital.website.replace(/^https?:\/\//, '')}
                  </a>
                </>
              )}
            </div>
            {hospital.notes && (
              <p className="text-sm text-slate-600 mt-3 max-w-2xl">{hospital.notes}</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2">
          <section className="p-6 border-r border-line">
            <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-4">
              Revenue & finance leadership
            </h2>
            <p className="text-sm text-slate-500">
              No contacts loaded yet. Once the agent worker runs, key revenue and finance leaders
              will appear here with their backgrounds and any recent role changes flagged.
            </p>
          </section>

          <section className="p-6">
            <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-4">
              Signal history
            </h2>
            <p className="text-sm text-slate-500">
              No signals yet. The agent monitors this hospital on Mon/Wed/Fri.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}

import Link from 'next/link';
import { fetchHospitals } from '@/lib/api';

export default async function HospitalsPage() {
  const hospitals = await fetchHospitals();

  return (
    <div className="px-8 py-7">
      <header className="mb-6">
        <h1 className="font-serif text-2xl font-semibold text-ink">Hospitals</h1>
        <p className="text-sm text-slate-500 mt-1">{hospitals.length} accounts monitored</p>
      </header>

      <div className="bg-white border border-line rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-paper border-b border-line">
            <tr>
              <th className="text-left text-xs font-mono uppercase tracking-widest text-slate-500 px-5 py-3">
                Hospital
              </th>
              <th className="text-left text-xs font-mono uppercase tracking-widest text-slate-500 px-5 py-3">
                AE Coverage
              </th>
              <th className="text-left text-xs font-mono uppercase tracking-widest text-slate-500 px-5 py-3">
                Notes
              </th>
            </tr>
          </thead>
          <tbody>
            {hospitals.map((h) => (
              <tr key={h.id} className="border-b border-line last:border-b-0 hover:bg-paper">
                <td className="px-5 py-4">
                  <Link
                    href={`/hospitals/${h.id}`}
                    className="font-serif font-semibold text-navy-900 hover:underline"
                  >
                    {h.name}
                  </Link>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600">
                  {h.ae_users.filter((u) => !u.is_admin).map((u) => u.name).join(', ') || '—'}
                </td>
                <td className="px-5 py-4 text-sm text-slate-500">{h.division_note ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

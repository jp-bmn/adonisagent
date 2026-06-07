'use client';

import { useRouter, useSearchParams } from 'next/navigation';

interface AeUser {
  id: string;
  name: string;
}

export default function TerritoryFilter({ aes }: { aes: AeUser[] }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const current = searchParams.get('ae_id') ?? '';

  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const params = new URLSearchParams(searchParams.toString());
    if (e.target.value) params.set('ae_id', e.target.value);
    else params.delete('ae_id');
    router.push(`/?${params}`);
  }

  return (
    <select
      value={current}
      onChange={handleChange}
      className="bg-white border border-line rounded-lg px-3 py-1.5 text-xs font-mono text-slate-600 focus:outline-none focus:ring-1 focus:ring-accent"
    >
      <option value="">All accounts (Danielle)</option>
      {aes.map((ae) => (
        <option key={ae.id} value={ae.id}>
          {ae.name}&apos;s territory
        </option>
      ))}
    </select>
  );
}

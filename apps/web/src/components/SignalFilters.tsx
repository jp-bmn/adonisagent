'use client';

import { useRouter, usePathname, useSearchParams } from 'next/navigation';

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'leadership_change', label: 'Leadership' },
  { value: 'epic_go_live', label: 'Epic go-live' },
  { value: 'vendor_change', label: 'Vendor change' },
  { value: 'vendor_dispute', label: 'Vendor dispute' },
  { value: 'ma_acquisition', label: 'M&A' },
  { value: 'financial_event', label: 'Financial' },
  { value: 'rcm_hiring_spike', label: 'RCM hiring' },
  { value: 'thought_leadership', label: 'Thought leadership' },
];

export default function SignalFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const currentCategory = searchParams.get('category') ?? '';
  const currentSort = searchParams.get('sort') ?? 'urgent';

  function setParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <div className="flex items-center justify-between gap-3 flex-wrap mb-5">
      {/* Category chips */}
      <div className="flex items-center gap-2 flex-wrap">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.value}
            onClick={() => setParam('category', cat.value)}
            className={`text-xs font-mono px-3 py-1.5 rounded-full border transition ${
              currentCategory === cat.value
                ? 'bg-brand text-cream border-brand'
                : 'bg-white border-line text-slate-600 hover:border-brand hover:text-brand'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Sort toggle */}
      <div className="flex items-center gap-1 bg-white border border-line rounded-lg p-0.5 flex-none">
        <button
          onClick={() => setParam('sort', 'urgent')}
          className={`text-xs font-mono px-3 py-1.5 rounded-md transition ${
            currentSort === 'urgent' ? 'bg-brand text-cream' : 'text-slate-500 hover:text-ink'
          }`}
        >
          Most urgent
        </button>
        <button
          onClick={() => setParam('sort', 'recent')}
          className={`text-xs font-mono px-3 py-1.5 rounded-md transition ${
            currentSort === 'recent' ? 'bg-brand text-cream' : 'text-slate-500 hover:text-ink'
          }`}
        >
          Most recent
        </button>
      </div>
    </div>
  );
}

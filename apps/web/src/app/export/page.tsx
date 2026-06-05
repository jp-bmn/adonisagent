'use client';

import { useState } from 'react';
import { exportCsv } from '@/lib/api';

export default function ExportPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDownload() {
    setLoading(true);
    setError(null);
    try {
      const blob = await exportCsv();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `adonis-signals-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Export failed — endpoint may not be live yet (Joel Task 13).');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="px-8 py-7">
      <header className="mb-6">
        <h1 className="font-serif text-2xl font-semibold text-brand">Export</h1>
        <p className="text-sm text-slate-500 mt-1">
          Download all signals as a CSV for offline review or CRM import.
        </p>
      </header>

      <div className="bg-white border border-line rounded-xl p-8 max-w-md">
        <h2 className="font-serif text-lg font-semibold text-brand mb-2">Signals CSV</h2>
        <p className="text-sm text-slate-500 mb-6">
          Exports all approved signals with hospital name, signal type, tier, summary, source, and
          date.
        </p>
        <button
          onClick={handleDownload}
          disabled={loading}
          className="px-5 py-2.5 bg-navy-900 text-white text-sm font-mono rounded-lg hover:bg-navy-700 disabled:opacity-50 transition"
        >
          {loading ? 'Downloading…' : '↧ Download CSV'}
        </button>
        {error && <p className="text-xs text-urgent mt-3">{error}</p>}
      </div>
    </div>
  );
}

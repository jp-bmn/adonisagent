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
      a.download = `adonis-contacts-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Export failed — please try again or contact Joel.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="px-4 py-5 md:px-8 md:py-7 pb-20 md:pb-7">
      <header className="mb-6">
        <h1 className="font-serif text-2xl font-semibold text-brand">Export</h1>
        <p className="text-sm text-slate-500 mt-1">
          Download active hospital contacts as a HubSpot-compatible CSV for offline review or CRM import.
        </p>
      </header>

      <div className="bg-white border border-line rounded-xl p-8 max-w-md">
        <h2 className="font-serif text-lg font-semibold text-brand mb-2">Contacts CSV</h2>
        <p className="text-sm text-slate-500 mb-6">
          Exports active hospital contacts with first/last name, job title, company name, website, verified LinkedIn URL, and recent signal notes.
        </p>
        <button
          onClick={handleDownload}
          disabled={loading}
          className="px-5 py-2.5 text-sm font-mono rounded-lg disabled:opacity-50 transition hover:opacity-90 active:scale-95"
          style={{ background: '#0F3D3E', color: '#EFEFC8' }}
        >
          {loading ? 'Downloading…' : '↧ Download CSV'}
        </button>
        {error && <p className="text-xs text-urgent mt-3">{error}</p>}
      </div>
    </div>
  );
}

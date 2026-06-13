'use client';

import { useState } from 'react';
import { ApiSignal, reviewSignal } from '@/lib/api';

interface ReviewQueueProps {
  initialSignals: ApiSignal[];
}

export default function ReviewQueue({ initialSignals }: ReviewQueueProps) {
  const [signals, setSignals] = useState(initialSignals);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  async function handleReview(id: string, status: 'approved' | 'dismissed') {
    setLoadingId(id);
    try {
      await reviewSignal(id, status);
      setSignals((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      console.error('Failed to review signal', err);
    } finally {
      setLoadingId(null);
    }
  }

  if (signals.length === 0) {
    return (
      <div className="bg-white border border-line rounded-xl p-10 text-center text-sm text-slate-500">
        No signals pending review. You are all caught up!
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {signals.map((signal) => (
        <div key={signal.id} className="bg-white border border-line rounded-xl p-5 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                {Math.round(signal.confidence_score * 100)}% Match
              </span>
              <span className="text-xs font-mono text-slate-400">
                {signal.signal_type}
              </span>
            </div>
            <h3 className="font-semibold text-brand text-sm">{signal.title || 'Untitled Signal'}</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">{signal.summary}</p>
          </div>
          
          <div className="flex items-center gap-2 w-full md:w-auto mt-3 md:mt-0">
            <button
              disabled={loadingId === signal.id}
              onClick={() => handleReview(signal.id, 'dismissed')}
              className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg border border-line text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            >
              Dismiss
            </button>
            <button
              disabled={loadingId === signal.id}
              onClick={() => handleReview(signal.id, 'approved')}
              className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg bg-accent text-white hover:bg-accent/90 disabled:opacity-50"
            >
              Approve
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

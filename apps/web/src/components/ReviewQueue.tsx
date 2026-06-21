'use client';

import { useState } from 'react';
import { ApiSignal, reviewSignal, SIGNAL_TYPE_LABELS, SignalType } from '@/lib/api';

function stripHtml(text: string): string {
  return text.replace(/<[^>]*>/g, '').trim();
}

interface CoverageResult {
  title: string;
  url: string;
  snippet: string;
  source: string;
}

interface ReviewQueueProps {
  initialSignals: ApiSignal[];
}

export default function ReviewQueue({ initialSignals }: ReviewQueueProps) {
  const [signals, setSignals] = useState(initialSignals);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [searching, setSearching] = useState<string | null>(null);
  const [coverage, setCoverage] = useState<Record<string, CoverageResult[]>>({});

  async function handleReview(id: string, status: 'approved' | 'dismissed') {
    setLoadingId(id);
    try {
      await reviewSignal(id, status);
      setSignals((prev) => prev.filter((s) => s.id !== id));
      setCoverage((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } catch (err) {
      console.error('Failed to review signal', err);
    } finally {
      setLoadingId(null);
    }
  }

  async function findCoverage(signal: ApiSignal) {
    setSearching(signal.id);
    try {
      const res = await fetch('/api/signals/coverage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: stripHtml(signal.title ?? ''),
          hospital_name: signal.hospital_name ?? '',
        }),
      });
      const results: CoverageResult[] = await res.json();
      setCoverage((prev) => ({ ...prev, [signal.id]: results }));
    } finally {
      setSearching(null);
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
        <div key={signal.id} className="bg-white border border-line rounded-xl p-5 space-y-3">
          {/* Header row */}
          <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-start">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  {Math.round(signal.confidence_score * 100)}% Match
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {SIGNAL_TYPE_LABELS[signal.signal_type as SignalType] ?? signal.signal_type}
                </span>
                {signal.hospital_name && (
                  <span className="text-xs font-mono text-slate-400 ml-auto">{signal.hospital_name}</span>
                )}
              </div>
              <h3 className="font-semibold text-brand text-sm">
                {signal.title ? stripHtml(signal.title) : 'Untitled Signal'}
              </h3>
              <p className="text-xs text-slate-500 mt-1 max-w-2xl">{signal.summary}</p>
              {signal.source_url && (
                <a
                  href={signal.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-accent hover:underline mt-1.5 block truncate max-w-sm"
                >
                  {signal.source_url}
                </a>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 w-full md:w-auto flex-shrink-0">
              <button
                disabled={loadingId === signal.id || searching === signal.id}
                onClick={() => handleReview(signal.id, 'dismissed')}
                className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg border border-line text-slate-600 hover:bg-slate-50 disabled:opacity-50"
              >
                Dismiss
              </button>
              <button
                disabled={loadingId === signal.id || searching === signal.id}
                onClick={() => findCoverage(signal)}
                className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg border border-line text-slate-600 hover:bg-slate-50 disabled:opacity-50"
              >
                {searching === signal.id ? 'Searching...' : 'More coverage'}
              </button>
              <button
                disabled={loadingId === signal.id || searching === signal.id}
                onClick={() => handleReview(signal.id, 'approved')}
                className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg bg-accent text-white hover:bg-accent/90 disabled:opacity-50"
              >
                Approve
              </button>
            </div>
          </div>

          {/* Coverage panel */}
          {coverage[signal.id] != null && (
            <div className="space-y-2 pt-1 border-t border-line">
              <p className="text-[10px] font-mono uppercase tracking-widest text-slate-400 pt-2">
                More coverage
              </p>
              {coverage[signal.id]!.length === 0 ? (
                <p className="text-xs text-slate-400">No additional coverage found.</p>
              ) : (
                coverage[signal.id]!.map((item, i) => (
                  <a
                    key={i}
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block p-3 rounded-lg border border-line hover:bg-paper transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[10px] font-mono text-slate-400">{item.source}</span>
                    </div>
                    <p className="text-xs font-semibold text-ink">{item.title}</p>
                    {item.snippet && (
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{item.snippet}</p>
                    )}
                  </a>
                ))
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

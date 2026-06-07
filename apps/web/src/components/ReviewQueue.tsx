'use client';

import { useState } from 'react';
import type { ApiSignal } from '@/lib/api';
import { reviewSignal, SIGNAL_TYPE_LABELS } from '@/lib/api';

export default function ReviewQueue({ initialSignals }: { initialSignals: ApiSignal[] }) {
  const [signals, setSignals] = useState(initialSignals);
  const [pending, setPending] = useState<Set<string>>(new Set());

  async function handleReview(id: string, status: 'approved' | 'dismissed') {
    setPending((p) => new Set(p).add(id));
    try {
      await reviewSignal(id, status);
      setSignals((prev) => prev.filter((s) => s.id !== id));
    } finally {
      setPending((p) => {
        const next = new Set(p);
        next.delete(id);
        return next;
      });
    }
  }

  if (signals.length === 0) {
    return (
      <div className="bg-white border border-line rounded-xl p-10 text-center text-sm text-slate-500">
        Queue is clear — no signals awaiting review.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {signals.map((signal) => {
        const label = SIGNAL_TYPE_LABELS[signal.signal_type] ?? signal.signal_type;
        const isBusy = pending.has(signal.id);
        return (
          <div key={signal.id} className="bg-white border border-line rounded-xl p-5 space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-500">{label}</span>
                  <span className="text-xs font-mono text-slate-400">·</span>
                  <span className="text-xs font-mono text-slate-400">
                    confidence {Math.round(signal.confidence_score)}%
                  </span>
                </div>
                <p className="font-serif text-base font-semibold text-ink leading-snug">
                  {signal.title ?? label}
                </p>
                {signal.summary && (
                  <p className="text-sm text-slate-600 leading-relaxed">{signal.summary}</p>
                )}
                <a
                  href={signal.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-accent hover:underline truncate block max-w-[60%]"
                >
                  {signal.source_name ?? signal.source_url}
                </a>
              </div>
              <div className="flex gap-2 flex-none">
                <button
                  disabled={isBusy}
                  onClick={() => handleReview(signal.id, 'approved')}
                  className="px-3 py-1.5 text-xs font-mono rounded-lg bg-standard/10 text-standard hover:bg-standard/20 disabled:opacity-40 transition"
                >
                  Approve
                </button>
                <button
                  disabled={isBusy}
                  onClick={() => handleReview(signal.id, 'dismissed')}
                  className="px-3 py-1.5 text-xs font-mono rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 disabled:opacity-40 transition"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

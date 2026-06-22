'use client';

import { useState } from 'react';
import { ApiSignal, reviewSignal, SIGNAL_TYPE_LABELS, SignalType } from '@/lib/api';

function stripHtml(text: string): string {
  return text.replace(/<[^>]*>/g, '').trim();
}

function isGarbage(signal: ApiSignal): boolean {
  return signal.signal_type === 'filtered_out' || signal.tier === 'filtered_out';
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

function SignalCard({
  signal,
  garbage,
  loadingId,
  searching,
  coverage,
  onReview,
  onFindCoverage,
  onRescue,
}: {
  signal: ApiSignal;
  garbage: boolean;
  loadingId: string | null;
  searching: string | null;
  coverage: Record<string, CoverageResult[]>;
  onReview: (id: string, status: 'approved' | 'dismissed') => void;
  onFindCoverage: (signal: ApiSignal) => void;
  onRescue?: (id: string) => void;
}) {
  return (
    <div
      className="rounded-xl p-5 space-y-3"
      style={{
        background: garbage ? '#FAFAFA' : '#FFFFFF',
        border: garbage ? '1px solid #E2E8F0' : '1.5px solid #16A34A33',
        opacity: garbage ? 0.75 : 1,
      }}
    >
      {/* Header row */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-start">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span
              className="text-xs font-mono px-2 py-0.5 rounded-full"
              style={{
                background: garbage ? '#F1F5F9' : '#DCFCE7',
                color: garbage ? '#94A3B8' : '#15803D',
              }}
            >
              {Math.round(signal.confidence_score * 100)}% Match
            </span>
            <span className="text-xs font-mono text-slate-400">
              {SIGNAL_TYPE_LABELS[signal.signal_type as SignalType] ?? signal.signal_type}
            </span>
            {signal.hospital_name && (
              <span className="text-xs font-mono text-slate-400 ml-auto">
                {signal.hospital_name}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-sm" style={{ color: garbage ? '#94A3B8' : '#0F172A' }}>
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
            onClick={() => onReview(signal.id, 'dismissed')}
            className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg border border-line text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            Dismiss
          </button>
          {garbage && onRescue && (
            <button
              onClick={() => onRescue(signal.id)}
              className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg border border-green-300 text-green-700 hover:bg-green-50 transition"
            >
              Move to relevant
            </button>
          )}
          {!garbage && (
            <button
              disabled={loadingId === signal.id || searching === signal.id}
              onClick={() => onFindCoverage(signal)}
              className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg border border-line text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            >
              {searching === signal.id ? 'Searching...' : 'More coverage'}
            </button>
          )}
          {!garbage && (
            <button
              disabled={loadingId === signal.id || searching === signal.id}
              onClick={() => onReview(signal.id, 'approved')}
              className="flex-1 md:flex-none px-4 py-2 text-xs font-semibold rounded-lg bg-accent text-white hover:bg-accent/90 disabled:opacity-50"
            >
              Approve
            </button>
          )}
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
                <span className="text-[10px] font-mono text-slate-400 block mb-0.5">
                  {item.source}
                </span>
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
  );
}

export default function ReviewQueue({ initialSignals }: ReviewQueueProps) {
  const [signals, setSignals] = useState(initialSignals);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [searching, setSearching] = useState<string | null>(null);
  const [coverage, setCoverage] = useState<Record<string, CoverageResult[]>>({});

  const real = signals.filter((s) => !isGarbage(s));
  const garbage = signals.filter((s) => isGarbage(s));

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

  function rescueSignal(id: string) {
    setSignals((prev) =>
      prev.map((s) =>
        s.id === id
          ? { ...s, signal_type: 'leadership_change' as SignalType, tier: 'worth_knowing' as const }
          : s
      )
    );
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

  const cardProps = {
    loadingId,
    searching,
    coverage,
    onReview: handleReview,
    onFindCoverage: findCoverage,
    onRescue: rescueSignal,
  };

  return (
    <div className="space-y-8">
      {/* Real signals */}
      {real.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-widest text-green-700">
              Relevant
            </span>
            <span className="text-xs font-mono text-slate-400">{real.length} signals</span>
          </div>
          {real.map((signal) => (
            <SignalCard key={signal.id} signal={signal} garbage={false} {...cardProps} />
          ))}
        </div>
      )}

      {/* Separator */}
      {real.length > 0 && garbage.length > 0 && (
        <div className="flex items-center gap-3">
          <div className="flex-1 border-t border-dashed border-slate-200" />
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
            Irrelevant — dismiss all
          </span>
          <div className="flex-1 border-t border-dashed border-slate-200" />
        </div>
      )}

      {/* Garbage signals */}
      {garbage.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold uppercase tracking-widest text-slate-400">
                Noise
              </span>
              <span className="text-xs font-mono text-slate-400">{garbage.length} signals</span>
            </div>
            <button
              onClick={() => garbage.forEach((s) => handleReview(s.id, 'dismissed'))}
              className="text-xs font-semibold text-urgent hover:opacity-80 transition"
            >
              Dismiss all
            </button>
          </div>
          {garbage.map((signal) => (
            <SignalCard key={signal.id} signal={signal} garbage={true} {...cardProps} />
          ))}
        </div>
      )}
    </div>
  );
}

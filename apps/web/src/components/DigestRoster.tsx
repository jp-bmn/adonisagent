'use client';

import { useEffect, useState } from 'react';

interface DigestView {
  ae_id: string;
  viewed_at: string;
  digest_id: string | null;
}

interface AeUser {
  id: string;
  name: string;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function DigestRoster({ aes }: { aes: AeUser[] }) {
  const [views, setViews] = useState<DigestView[]>([]);

  useEffect(() => {
    fetch('/api/digest-view')
      .then((r) => r.json())
      .then((data) => setViews(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, []);

  const viewMap = Object.fromEntries(views.map((v) => [v.ae_id, v]));

  return (
    <div className="bg-white border border-line rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-line bg-paper flex items-center justify-between">
        <span className="text-xs font-mono uppercase tracking-widest text-slate-500">
          Digest · Last Opened
        </span>
        <span className="text-[10px] font-mono text-slate-400">{aes.length} AEs</span>
      </div>
      <div className="divide-y divide-line">
        {aes.map((ae) => {
          const view = viewMap[ae.id];
          return (
            <div key={ae.id} className="flex items-center justify-between px-4 py-2.5">
              <span className="text-sm text-ink">{ae.name}</span>
              {view ? (
                <div className="flex items-center gap-2">
                  <span
                    className="w-1.5 h-1.5 rounded-full flex-none"
                    style={{ background: '#16A34A' }}
                  />
                  <span className="text-xs font-mono text-green-700">
                    {timeAgo(view.viewed_at)}
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-300 flex-none" />
                  <span className="text-xs font-mono text-slate-400">not opened</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

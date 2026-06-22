'use client';

import { useEffect, useState } from 'react';

interface RoleCoverage {
  role: string;
  status: 'filled' | 'pending' | 'missing';
  name: string | null;
  linkedin_url: string | null;
}

interface HospitalCoverage {
  id: string;
  name: string;
  roles: RoleCoverage[];
}

const STATUS_STYLE = {
  filled: { dot: 'bg-green-500', text: 'text-green-700', label: 'bg-green-50 border-green-200' },
  pending: {
    dot: 'bg-yellow-400',
    text: 'text-yellow-700',
    label: 'bg-yellow-50 border-yellow-200',
  },
  missing: { dot: 'bg-red-400', text: 'text-red-600', label: 'bg-red-50 border-red-200' },
};

export default function ContactCoverage() {
  const [coverage, setCoverage] = useState<HospitalCoverage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/contacts/coverage')
      .then((r) => r.json())
      .then((data) => {
        setCoverage(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-xs text-slate-400">Loading coverage...</p>;

  return (
    <div className="space-y-4">
      {coverage.map((hospital) => {
        const filled = hospital.roles.filter((r) => r.status === 'filled').length;
        const pending = hospital.roles.filter((r) => r.status === 'pending').length;
        const missing = hospital.roles.filter((r) => r.status === 'missing').length;

        return (
          <div key={hospital.id} className="border border-line rounded-xl overflow-hidden">
            {/* Hospital header */}
            <div className="flex items-center justify-between px-4 py-3 bg-paper border-b border-line">
              <span className="text-sm font-semibold text-ink">{hospital.name}</span>
              <div className="flex items-center gap-3 text-[10px] font-mono">
                <span className="text-green-700">{filled} filled</span>
                {pending > 0 && <span className="text-yellow-700">{pending} pending</span>}
                {missing > 0 && <span className="text-red-600">{missing} missing</span>}
              </div>
            </div>

            {/* Role rows */}
            <div className="divide-y divide-line">
              {hospital.roles.map((r) => {
                const style = STATUS_STYLE[r.status];
                return (
                  <div key={r.role} className="flex items-center gap-3 px-4 py-2.5">
                    <span className={`w-1.5 h-1.5 rounded-full flex-none ${style.dot}`} />
                    <span className="text-xs font-mono text-slate-500 w-28 flex-none">
                      {r.role}
                    </span>
                    {r.name ? (
                      <div className="flex items-center gap-2 min-w-0">
                        <span
                          className={`text-xs font-semibold ${r.status === 'missing' ? 'text-slate-400' : 'text-ink'}`}
                        >
                          {r.name}
                        </span>
                        {r.status === 'pending' && (
                          <span
                            className={`text-[9px] font-mono px-1.5 py-0.5 rounded-full border ${style.label} ${style.text}`}
                          >
                            pending review
                          </span>
                        )}
                        {r.linkedin_url && (
                          <a
                            href={r.linkedin_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[10px] text-accent hover:underline truncate"
                          >
                            LinkedIn
                          </a>
                        )}
                      </div>
                    ) : (
                      <span className={`text-xs ${style.text} italic`}>Not found</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

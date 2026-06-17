'use client';

import { useEffect, useState, useCallback } from 'react';
import { useUser } from '@/components/UserProvider';

const BASE_URL = 'https://adonisagents-production.up.railway.app/api/v1';
const HEADERS = (userId: string) => ({ 'X-User-Id': userId });

interface ApiStatus {
  last_scraper_run: string | null;
  next_scraper_run: string | null;
  total_signals_stored: number;
  pending_review_count: number;
  urgent_count: number;
  urgent_delta: number;
  urgent_delta_direction: 'up' | 'down' | 'flat';
  worth_knowing_count: number;
  worth_knowing_delta: number;
  worth_knowing_delta_direction: 'up' | 'down' | 'flat';
}

interface Hospital {
  id: string;
  name: string;
}

interface Signal {
  id: string;
  hospital_id: string;
  signal_type: string;
  tier: string;
  title: string | null;
  source_url: string;
}

interface Contact {
  id: string;
  full_name: string;
  linkedin_url: string | null;
  role: string | null;
}

interface GithubIssue {
  number: number;
  title: string;
  assignees: { login: string }[];
  html_url: string;
}

interface AuditEntry {
  time: Date;
  type: 'error' | 'success' | 'warning' | 'info';
  message: string;
}

function fmt(d: Date) {
  return `${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} ${d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
}

export default function DevDashboardPage() {
  const { userId } = useUser();
  const [dark, setDark] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const [apiHealth, setApiHealth] = useState<'loading' | 'ok' | 'down'>('loading');
  const [apiDownSince, setApiDownSince] = useState<Date | null>(null);
  const [statusData, setStatusData] = useState<ApiStatus | null>(null);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [signalsByHospital, setSignalsByHospital] = useState<Record<string, Signal[]>>({});
  const [contactsByHospital, setContactsByHospital] = useState<Record<string, Contact[]>>({});
  const [githubIssues, setGithubIssues] = useState<GithubIssue[]>([]);
  const [allSignals, setAllSignals] = useState<Signal[]>([]);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [prevApiHealth, setPrevApiHealth] = useState<'loading' | 'ok' | 'down'>('loading');

  const addAudit = useCallback((entry: AuditEntry) => {
    setAuditLog((prev) => [entry, ...prev].slice(0, 100));
  }, []);

  const fetchData = useCallback(async () => {
    const uid = userId || 'df7c14fd-cde3-4025-be00-ca42f4d31741';
    const h = HEADERS(uid);

    // API health
    try {
      const res = await fetch(`${BASE_URL}/status`, { headers: h, cache: 'no-store' });
      if (!res.ok) throw new Error('not ok');
      const data: ApiStatus = await res.json();
      setStatusData(data);
      setApiHealth('ok');
      setApiDownSince(null);
    } catch {
      setApiHealth('down');
      setApiDownSince((prev) => prev ?? new Date());
    }

    // Hospitals + per-hospital signals + contacts
    try {
      const res = await fetch(`${BASE_URL}/hospitals`, { headers: h, cache: 'no-store' });
      if (!res.ok) throw new Error('not ok');
      const data: Hospital[] = await res.json();
      setHospitals(data);

      const sigMap: Record<string, Signal[]> = {};
      const conMap: Record<string, Contact[]> = {};

      await Promise.all(
        data.map(async (hosp) => {
          try {
            const [sr, cr] = await Promise.all([
              fetch(`${BASE_URL}/hospitals/${hosp.id}/signals`, { headers: h, cache: 'no-store' }),
              fetch(`${BASE_URL}/hospitals/${hosp.id}/contacts`, { headers: h, cache: 'no-store' }),
            ]);
            if (sr.ok) sigMap[hosp.id] = await sr.json();
            if (cr.ok) conMap[hosp.id] = await cr.json();
          } catch {}
        })
      );

      setSignalsByHospital(sigMap);
      setContactsByHospital(conMap);
    } catch {}

    // All signals for quality checks
    try {
      const res = await fetch(`${BASE_URL}/signals?limit=200`, { headers: h, cache: 'no-store' });
      if (res.ok) setAllSignals(await res.json());
    } catch {}

    // GitHub issues
    try {
      const res = await fetch(
        'https://api.github.com/repos/jp-bmn/adonisagent/issues?state=open&per_page=30'
      );
      if (res.ok) setGithubIssues(await res.json());
    } catch {}

    setLastRefresh(new Date());
  }, [userId]);

  // Audit: detect API state transitions
  useEffect(() => {
    if (prevApiHealth === 'loading' && apiHealth === 'down') {
      addAudit({ time: new Date(), type: 'error', message: 'API offline — returning 502' });
    } else if (prevApiHealth === 'down' && apiHealth === 'ok') {
      addAudit({ time: new Date(), type: 'success', message: 'API came back online' });
    } else if (prevApiHealth === 'loading' && apiHealth === 'ok') {
      addAudit({ time: new Date(), type: 'info', message: 'API online — dashboard loaded' });
    }
    setPrevApiHealth(apiHealth);
  }, [apiHealth, prevApiHealth, addAudit]);

  useEffect(() => {
    const saved = localStorage.getItem('adonis-dev-dark');
    if (saved === 'true') setDark(true);
    addAudit({ time: new Date(), type: 'info', message: 'Dev dashboard session started' });
  }, [addAudit]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const toggleDark = () => {
    setDark((d) => {
      localStorage.setItem('adonis-dev-dark', String(!d));
      return !d;
    });
  };

  // Signal quality checks
  const htmlSignals = allSignals.filter((s) => s.title && /<[^>]+>/.test(s.title));
  const testSignals = allSignals.filter((s) => s.title && /ignore|test signal/i.test(s.title));
  const allContacts = Object.values(contactsByHospital).flat();
  const nullLinkedin = allContacts.filter((c) => !c.linkedin_url);
  const postUrlLinkedin = allContacts.filter(
    (c) => c.linkedin_url && c.linkedin_url.includes('/posts/')
  );

  // Theme classes
  const bg = dark ? 'bg-gray-950' : 'bg-paper';
  const card = dark ? 'bg-gray-900 border-gray-800' : 'bg-white border-line';
  const text = dark ? 'text-gray-100' : 'text-ink';
  const sub = dark ? 'text-gray-400' : 'text-slate-500';
  const border = dark ? 'border-gray-800' : 'border-line';

  return (
    <div className={`${bg} ${text} min-h-screen`}>
      {/* Header */}
      <div
        className={`px-6 py-4 border-b ${border} flex flex-wrap items-center justify-between gap-3`}
      >
        <div>
          <h1 className="font-serif text-xl font-semibold">Dev Dashboard</h1>
          <p className={`text-xs ${sub} mt-0.5`}>Refreshed {fmt(lastRefresh)} · Admin only</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* API status pill */}
          <span
            className={`inline-flex items-center gap-1.5 text-xs font-mono px-3 py-1 rounded-full font-semibold ${
              apiHealth === 'ok'
                ? 'bg-green-100 text-green-700'
                : apiHealth === 'down'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-500'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                apiHealth === 'ok'
                  ? 'bg-green-500'
                  : apiHealth === 'down'
                    ? 'bg-red-500 animate-pulse'
                    : 'bg-gray-400'
              }`}
            />
            {apiHealth === 'ok'
              ? 'API Online'
              : apiHealth === 'down'
                ? `API Down${apiDownSince ? ` since ${apiDownSince.toLocaleTimeString()}` : ''}`
                : 'Checking…'}
          </span>

          {/* Dark mode toggle */}
          <div className="flex items-center gap-2">
            <span className={`text-xs ${sub}`}>☀️</span>
            <button
              onClick={toggleDark}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${dark ? 'bg-accent' : 'bg-gray-300'}`}
              aria-label="Toggle dark mode"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${dark ? 'translate-x-6' : 'translate-x-1'}`}
              />
            </button>
            <span className={`text-xs ${sub}`}>🌙</span>
          </div>

          <button
            onClick={fetchData}
            className={`text-xs px-3 py-1.5 rounded-lg border ${border} ${sub} hover:text-ink transition`}
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      <div className="p-6 space-y-5">
        {/* Row 1 — 3 stat tiles */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className={`${card} border rounded-xl p-5`}>
            <div className={`text-xs font-mono uppercase tracking-widest ${sub} mb-2`}>
              API Health
            </div>
            <div
              className={`font-serif text-2xl font-bold ${
                apiHealth === 'ok' ? 'text-green-600' : apiHealth === 'down' ? 'text-urgent' : sub
              }`}
            >
              {apiHealth === 'ok' ? 'Online' : apiHealth === 'down' ? 'Down' : '…'}
            </div>
            <div className={`text-xs ${sub} mt-1`}>
              {apiHealth === 'down' && apiDownSince
                ? `Since ${apiDownSince.toLocaleTimeString()}`
                : apiHealth === 'ok'
                  ? 'All endpoints responding'
                  : 'Checking…'}
            </div>
          </div>

          <div className={`${card} border rounded-xl p-5`}>
            <div className={`text-xs font-mono uppercase tracking-widest ${sub} mb-2`}>
              Total Signals
            </div>
            <div className="font-serif text-2xl font-bold text-navy-900">
              {statusData?.total_signals_stored ?? '—'}
            </div>
            <div className={`text-xs ${sub} mt-1`}>
              {statusData?.last_scraper_run
                ? `Last run: ${new Date(statusData.last_scraper_run).toLocaleDateString()}`
                : 'Last run: unknown'}
            </div>
          </div>

          <div className={`${card} border rounded-xl p-5`}>
            <div className={`text-xs font-mono uppercase tracking-widest ${sub} mb-2`}>
              Pending Review
            </div>
            <div
              className={`font-serif text-2xl font-bold ${
                (statusData?.pending_review_count ?? 0) > 0 ? 'text-urgent' : 'text-green-600'
              }`}
            >
              {statusData?.pending_review_count ?? '—'}
            </div>
            <div className={`text-xs ${sub} mt-1`}>
              {(statusData?.pending_review_count ?? 0) > 0 ? 'Waiting for Danielle' : 'Queue clear'}
            </div>
          </div>
        </div>

        {/* Row 2 — Hospital Coverage + Contact Health */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className={`${card} border rounded-xl p-5`}>
            <div className={`text-xs font-mono uppercase tracking-widest ${sub} mb-4`}>
              Hospital Coverage
            </div>
            {apiHealth === 'down' ? (
              <p className={`text-sm ${sub}`}>API offline — cannot load</p>
            ) : hospitals.length === 0 ? (
              <p className={`text-sm ${sub}`}>Loading…</p>
            ) : (
              <div className="space-y-2.5">
                {hospitals.map((hosp) => {
                  const count = signalsByHospital[hosp.id]?.length ?? 0;
                  const icon = count >= 5 ? '✅' : count >= 3 ? '⚠️' : '❌';
                  const color =
                    count >= 5 ? 'text-green-600' : count >= 3 ? 'text-yellow-600' : 'text-urgent';
                  return (
                    <div key={hosp.id} className="flex items-center justify-between">
                      <span className={`text-sm ${text}`}>{hosp.name}</span>
                      <span className={`text-sm font-mono font-semibold ${color}`}>
                        {icon} {count} signals
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className={`${card} border rounded-xl p-5`}>
            <div className={`text-xs font-mono uppercase tracking-widest ${sub} mb-4`}>
              Contact Health
            </div>
            {apiHealth === 'down' ? (
              <p className={`text-sm ${sub}`}>API offline — cannot load</p>
            ) : hospitals.length === 0 ? (
              <p className={`text-sm ${sub}`}>Loading…</p>
            ) : (
              <div className="space-y-2.5">
                {hospitals.map((hosp) => {
                  const contacts = contactsByHospital[hosp.id] ?? [];
                  const total = contacts.length;
                  const broken = contacts.filter(
                    (c) => !c.linkedin_url || c.linkedin_url.includes('/posts/')
                  ).length;
                  const icon = total === 0 ? '❌' : broken > 0 ? '⚠️' : '✅';
                  const color =
                    total === 0 ? 'text-urgent' : broken > 0 ? 'text-yellow-600' : 'text-green-600';
                  return (
                    <div key={hosp.id} className="flex items-center justify-between">
                      <span className={`text-sm ${text}`}>{hosp.name}</span>
                      <span className={`text-sm font-mono font-semibold ${color}`}>
                        {icon} {total} contacts{broken > 0 ? ` · ${broken} broken` : ''}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Row 3 — Signal Quality + GitHub Issues */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className={`${card} border rounded-xl p-5`}>
            <div className={`text-xs font-mono uppercase tracking-widest ${sub} mb-4`}>
              Signal Quality
            </div>
            {apiHealth === 'down' ? (
              <p className={`text-sm ${sub}`}>API offline — cannot load</p>
            ) : allSignals.length === 0 ? (
              <p className={`text-sm ${sub}`}>Loading…</p>
            ) : (
              <div className="space-y-2.5">
                {[
                  {
                    label: 'HTML in titles',
                    count: htmlSignals.length,
                    level: htmlSignals.length > 0 ? 'error' : 'ok',
                  },
                  {
                    label: 'Test signals in prod',
                    count: testSignals.length,
                    level: testSignals.length > 0 ? 'error' : 'ok',
                  },
                  {
                    label: 'Null LinkedIn URLs',
                    count: nullLinkedin.length,
                    level: nullLinkedin.length > 0 ? 'warn' : 'ok',
                  },
                  {
                    label: 'LinkedIn post URLs',
                    count: postUrlLinkedin.length,
                    level: postUrlLinkedin.length > 0 ? 'error' : 'ok',
                  },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between">
                    <span className={`text-sm ${text}`}>{row.label}</span>
                    <span
                      className={`text-sm font-mono font-semibold ${
                        row.level === 'error'
                          ? 'text-urgent'
                          : row.level === 'warn'
                            ? 'text-yellow-600'
                            : 'text-green-600'
                      }`}
                    >
                      {row.level === 'error' ? '❌' : row.level === 'warn' ? '⚠️' : '✅'}{' '}
                      {row.count}
                    </span>
                  </div>
                ))}
                <div className={`pt-1 border-t ${border} flex items-center justify-between`}>
                  <span className={`text-xs ${sub}`}>Signals checked</span>
                  <span className={`text-xs font-mono ${sub}`}>{allSignals.length}</span>
                </div>
              </div>
            )}
          </div>

          <div className={`${card} border rounded-xl p-5`}>
            <div className={`text-xs font-mono uppercase tracking-widest ${sub} mb-4`}>
              Open GitHub Issues
            </div>
            {githubIssues.length === 0 ? (
              <p className={`text-sm ${sub}`}>Loading…</p>
            ) : (
              <div className="space-y-4">
                {(
                  [
                    { login: 'jp-bmn', name: 'Joel' },
                    { login: 'newbloomwon', name: 'Michael' },
                    { login: 'm1lestones', name: 'Juan' },
                  ] as const
                ).map(({ login, name }) => {
                  const assigned = githubIssues.filter((i) =>
                    i.assignees.some((a) => a.login === login)
                  );
                  if (assigned.length === 0) return null;
                  return (
                    <div key={login}>
                      <div className={`text-xs font-semibold ${sub} mb-1.5`}>
                        {name} ({assigned.length})
                      </div>
                      <div className="space-y-1">
                        {assigned.map((issue) => (
                          <a
                            key={issue.number}
                            href={issue.html_url}
                            target="_blank"
                            rel="noreferrer"
                            className={`block text-xs ${text} hover:text-accent truncate`}
                          >
                            #{issue.number} {issue.title}
                          </a>
                        ))}
                      </div>
                    </div>
                  );
                })}
                {githubIssues.every(
                  (i) =>
                    !i.assignees.some((a) =>
                      ['jp-bmn', 'newbloomwon', 'm1lestones'].includes(a.login)
                    )
                ) && <p className={`text-sm ${sub}`}>No assigned open issues</p>}
              </div>
            )}
          </div>
        </div>

        {/* Row 4 — Audit Log */}
        <div className={`${card} border rounded-xl p-5`}>
          <div className={`text-xs font-mono uppercase tracking-widest ${sub} mb-4`}>
            Audit Log · This Session
          </div>
          {auditLog.length === 0 ? (
            <p className={`text-sm ${sub}`}>No events yet</p>
          ) : (
            <div className="space-y-2">
              {auditLog.map((entry, i) => (
                <div key={i} className="flex items-start gap-4">
                  <span className={`text-xs font-mono ${sub} whitespace-nowrap pt-0.5 flex-none`}>
                    {fmt(entry.time)}
                  </span>
                  <span
                    className={`text-xs ${
                      entry.type === 'error'
                        ? 'text-urgent'
                        : entry.type === 'success'
                          ? 'text-green-600'
                          : entry.type === 'warning'
                            ? 'text-yellow-600'
                            : text
                    }`}
                  >
                    {entry.type === 'error'
                      ? '❌'
                      : entry.type === 'success'
                        ? '✅'
                        : entry.type === 'warning'
                          ? '⚠️'
                          : 'ℹ️'}{' '}
                    {entry.message}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

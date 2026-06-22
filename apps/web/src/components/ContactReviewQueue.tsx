'use client';

import { useState, useEffect } from 'react';
import type { PendingContact } from '@/lib/api';

interface Candidate {
  full_name: string;
  linkedin_url: string | null;
  prior_employer: string | null;
  confidence: number;
  evidence: string;
}

const ROLE_STYLE: Record<string, { background: string; color: string }> = {
  ceo: { background: '#FBEDEB', color: '#C44A2C' },
  cfo: { background: '#EBF0FB', color: '#1F4FA8' },
  cro: { background: '#E9F4ED', color: '#1F7A3E' },
};

function roleStyle(role: string | null) {
  if (!role) return { background: '#F0EBF8', color: '#6B3FA0' };
  const key = Object.keys(ROLE_STYLE).find((k) => role.toLowerCase().includes(k));
  return key ? ROLE_STYLE[key] : { background: '#F0EBF8', color: '#6B3FA0' };
}

export default function ContactReviewQueue() {
  const [contacts, setContacts] = useState<PendingContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState<string | null>(null);
  const [searching, setSearching] = useState<string | null>(null);
  const [alternatives, setAlternatives] = useState<Record<string, Candidate[]>>({});
  const [linkedinInputs, setLinkedinInputs] = useState<Record<string, string>>({});

  useEffect(() => {
    fetch('/api/contacts')
      .then((r) => r.json())
      .then((data) => {
        setContacts(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  async function handleAction(id: string, action: 'approve' | 'reject') {
    setActing(id);
    const manualUrl = linkedinInputs[id]?.trim() || null;
    try {
      await fetch(`/api/contacts/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          ...(action === 'approve' && manualUrl
            ? { overrides: { linkedin_url: manualUrl, linkedin_verified: true } }
            : {}),
        }),
      });
      setContacts((prev) => prev.filter((c) => c.id !== id));
      setAlternatives((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } finally {
      setActing(null);
    }
  }

  async function findAlternatives(contact: PendingContact) {
    setSearching(contact.id);
    try {
      const res = await fetch('/api/contacts/alternatives', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hospital_name: contact.hospital_name,
          role: contact.role,
        }),
      });
      const candidates: Candidate[] = await res.json();
      setAlternatives((prev) => ({ ...prev, [contact.id]: candidates }));
    } finally {
      setSearching(null);
    }
  }

  async function approveCandidate(contactId: string, candidate: Candidate) {
    setActing(contactId);
    try {
      await fetch(`/api/contacts/${contactId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'approve',
          overrides: {
            full_name: candidate.full_name,
            linkedin_url: candidate.linkedin_url,
            prior_employer: candidate.prior_employer,
          },
        }),
      });
      setContacts((prev) => prev.filter((c) => c.id !== contactId));
      setAlternatives((prev) => {
        const next = { ...prev };
        delete next[contactId];
        return next;
      });
    } finally {
      setActing(null);
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Loading pending contacts...</p>;
  if (contacts.length === 0)
    return <p className="text-sm text-slate-500">No contacts pending review.</p>;

  return (
    <div className="space-y-3">
      {contacts.map((c) => (
        <div key={c.id} className="bg-white border border-line rounded-xl p-4 space-y-3">
          {/* Header */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-ink">{c.full_name}</span>
            {c.role && (
              <span
                className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full uppercase tracking-wide"
                style={roleStyle(c.role)}
              >
                {c.role}
              </span>
            )}
            <span className="text-xs font-mono text-slate-400 ml-auto">{c.hospital_name}</span>
          </div>

          {/* Details */}
          {c.prior_employer && <p className="text-xs text-slate-400">prev. {c.prior_employer}</p>}
          {c.linkedin_url && (
            <a
              href={c.linkedin_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-accent hover:underline block"
            >
              {c.linkedin_url}
            </a>
          )}

          {/* Agent reasoning */}
          {c.review_note && (
            <div
              className="text-xs text-slate-600 leading-relaxed"
              style={{ borderLeft: '3px solid #0F3D3E', paddingLeft: '10px', fontStyle: 'italic' }}
            >
              {c.review_note}
            </div>
          )}

          {/* Alternatives */}
          {alternatives[c.id] != null && (
            <div className="space-y-2 pt-1">
              <p className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
                Alternative candidates
              </p>
              {alternatives[c.id]!.length === 0 ? (
                <p className="text-xs text-slate-400">No other candidates found.</p>
              ) : (
                alternatives[c.id]!.map((candidate, i) => (
                  <div
                    key={i}
                    className="flex items-start justify-between gap-3 p-3 rounded-lg border border-line hover:bg-paper transition-colors"
                  >
                    <div className="space-y-0.5 min-w-0">
                      <p className="text-sm font-semibold text-ink">{candidate.full_name}</p>
                      {candidate.prior_employer && (
                        <p className="text-xs text-slate-400">prev. {candidate.prior_employer}</p>
                      )}
                      {candidate.linkedin_url && (
                        <a
                          href={candidate.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-accent hover:underline block truncate"
                        >
                          {candidate.linkedin_url}
                        </a>
                      )}
                      <p className="text-xs text-slate-500 italic">{candidate.evidence}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1.5 flex-none">
                      <span className="text-[10px] font-mono text-slate-400">
                        {(candidate.confidence * 100).toFixed(0)}%
                      </span>
                      <button
                        onClick={() => approveCandidate(c.id, candidate)}
                        disabled={acting === c.id}
                        className="px-2.5 py-1 rounded-lg text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
                        style={{ background: '#0F3D3E' }}
                      >
                        Use this
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Manual LinkedIn input */}
          {!c.linkedin_url && (
            <div className="flex items-center gap-2">
              <input
                type="url"
                placeholder="Paste LinkedIn URL (optional)"
                value={linkedinInputs[c.id] ?? ''}
                onChange={(e) => setLinkedinInputs((prev) => ({ ...prev, [c.id]: e.target.value }))}
                className="flex-1 text-xs border border-line rounded-lg px-3 py-1.5 text-ink placeholder:text-slate-400 focus:outline-none focus:border-slate-400"
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-1">
            <button
              onClick={() => handleAction(c.id, 'approve')}
              disabled={acting === c.id || searching === c.id}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
              style={{ background: '#0F3D3E' }}
            >
              Approve
            </button>
            <button
              onClick={() => findAlternatives(c)}
              disabled={acting === c.id || searching === c.id}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 border border-line transition hover:bg-paper disabled:opacity-50"
            >
              {searching === c.id ? 'Searching...' : 'Find alternatives'}
            </button>
            <button
              onClick={() => handleAction(c.id, 'reject')}
              disabled={acting === c.id || searching === c.id}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-urgent transition hover:opacity-80 disabled:opacity-50"
            >
              Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

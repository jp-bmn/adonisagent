'use client';

import { useState, useRef, useEffect } from 'react';
import { fetchSignals } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  text: string;
}

const STORAGE_KEY = 'adonis-copilot-history';
const PILL_KEY = 'adonis-copilot-pill-shown';
const OPENED_KEY = 'adonis-copilot-opened';
const MAX_STORED = 200;
const MAX_CONTEXT = 40;

const STUB_REPLY =
  "I can answer questions about your accounts and recent signals. Try asking: 'What happened with NYP this week?' or 'Summarize urgent signals.'";

function loadMessages(): Message[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Message[]) : [];
  } catch {
    return [];
  }
}

function saveMessages(msgs: Message[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-MAX_STORED)));
  } catch {
    // storage full or unavailable — fail silently
  }
}

export default function CoPilot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPill, setShowPill] = useState(false);
  const [pillSlideIn, setPillSlideIn] = useState(false);
  const [pulsing, setPulsing] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const pillDismissTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setMessages(loadMessages());
  }, []);

  useEffect(() => {
    if (messages.length > 0) saveMessages(messages);
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Discoverability pill — show once per session
  useEffect(() => {
    if (sessionStorage.getItem(PILL_KEY)) return;
    const showTimer = setTimeout(() => {
      setShowPill(true);
      setTimeout(() => setPillSlideIn(true), 50);
      pillDismissTimer.current = setTimeout(() => {
        dismissPill();
        setPulsing(true);
      }, 6000);
    }, 800);
    return () => clearTimeout(showTimer);
  }, []);

  // Unread dot — urgent signals from the last 24h
  useEffect(() => {
    if (sessionStorage.getItem(OPENED_KEY)) return;
    fetchSignals(undefined, { tier: 'urgent' })
      .then((signals) => {
        const cutoff = Date.now() - 24 * 60 * 60 * 1000;
        const recent = signals.filter((s) => {
          const d = s.published_date ?? s.created_at;
          return new Date(d).getTime() > cutoff;
        });
        setHasUnread(recent.length > 0);
      })
      .catch(() => {});
  }, []);

  function dismissPill() {
    setPillSlideIn(false);
    setTimeout(() => setShowPill(false), 300);
    sessionStorage.setItem(PILL_KEY, '1');
    if (pillDismissTimer.current) clearTimeout(pillDismissTimer.current);
  }

  function handleBubbleClick() {
    if (showPill) dismissPill();
    setPulsing(false);
    setHasUnread(false);
    sessionStorage.setItem(OPENED_KEY, '1');
    setOpen((o) => !o);
  }

  function clearHistory() {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  }

  async function handleSend() {
    const text = input.trim();
    if (!text) return;
    setInput('');
    const updated = [...messages, { role: 'user' as const, text }];
    setMessages(updated);
    setLoading(true);
    // TODO T-13: replace stub with real API call.
    // Send only the last MAX_CONTEXT messages so API calls stay fast and cheap.
    //
    // const res = await fetch('/api/copilot', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     message: text,
    //     history: updated.slice(-MAX_CONTEXT),
    //   }),
    // });
    // const { reply } = await res.json();
    await new Promise((r) => setTimeout(r, 800));
    setMessages((prev) => [...prev, { role: 'assistant' as const, text: STUB_REPLY }]);
    setLoading(false);
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <>
      {/* Keyframes for pulse ring */}
      <style>{`
        @keyframes copilot-ring {
          0% { box-shadow: 0 0 0 0 rgba(239,239,200,0.5); }
          70% { box-shadow: 0 0 0 14px rgba(239,239,200,0); }
          100% { box-shadow: 0 0 0 0 rgba(239,239,200,0); }
        }
        .copilot-pulse { animation: copilot-ring 1.2s ease-out; }
      `}</style>

      <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3">
        {/* Discoverability pill */}
        {showPill && (
          <div
            style={{
              transition: 'opacity 300ms, transform 300ms',
              opacity: pillSlideIn ? 1 : 0,
              transform: pillSlideIn ? 'translateX(0)' : 'translateX(12px)',
              background: 'white',
              color: '#0F3D3E',
              fontSize: '13px',
              padding: '8px 14px',
              borderRadius: '20px',
              boxShadow: '0 4px 14px rgba(15,61,62,0.18)',
              whiteSpace: 'nowrap',
              fontWeight: 500,
            }}
          >
            Ask about any signal
          </div>
        )}

        {/* Bubble */}
        <div className="relative flex-none">
          {/* Pulse ring */}
          {pulsing && !open && (
            <span
              key={Date.now()}
              className="absolute inset-0 rounded-full copilot-pulse pointer-events-none"
            />
          )}

          {/* Unread dot */}
          {hasUnread && !open && (
            <span className="absolute top-0 right-0 w-2 h-2 rounded-full bg-red-500 ring-2 ring-white z-10" />
          )}

          <button
            onClick={handleBubbleClick}
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: '#0F3D3E',
              color: '#EFEFC8',
              boxShadow: '0 4px 14px rgba(15,61,62,0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '22px',
              border: 'none',
              cursor: 'pointer',
              transition: 'background 150ms',
            }}
            title="Adonis Intel co-pilot"
          >
            {open ? (
              <span style={{ fontSize: 24, lineHeight: 1 }}>×</span>
            ) : (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Chat panel — anchored above the bubble */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-80 bg-white border border-line rounded-xl shadow-xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-navy-900 px-4 py-3 flex items-center justify-between">
            <div>
              <div className="text-white text-sm font-semibold">Adonis Intel</div>
              <div className="text-slate-400 text-[10px] font-mono">AI co-pilot · beta</div>
            </div>
            <div className="flex items-center gap-3">
              {messages.length > 0 && (
                <button
                  onClick={clearHistory}
                  className="text-slate-400 hover:text-white text-[10px] font-mono transition"
                  title="Clear conversation"
                >
                  clear
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="text-slate-400 hover:text-white transition text-lg leading-none"
              >
                ×
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-72 min-h-[8rem]">
            {messages.length === 0 && (
              <p className="text-xs text-slate-400 text-center">
                Ask about your accounts, signals, or territory.
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] text-xs px-3 py-2 rounded-xl leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-accent text-white rounded-br-none'
                      : 'bg-paper text-slate-700 rounded-bl-none'
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-paper text-slate-400 text-xs px-3 py-2 rounded-xl rounded-bl-none">
                  Thinking…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="border-t border-line p-3 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about your accounts…"
              className="flex-1 text-xs border border-line rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="text-xs px-3 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 disabled:opacity-40 transition"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}

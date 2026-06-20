'use client';

import { useState, useRef, useEffect } from 'react';
import { fetchSignals } from '@/lib/api';
import { useUser } from '@/components/UserProvider';

interface Message {
  role: 'user' | 'assistant';
  text: string;
}

function IrisMessage({ text }: { text: string }) {
  const lines = text.split('\n');
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i] ?? '';

    // Blank line — spacing between blocks
    if (line.trim() === '') {
      i++;
      continue;
    }

    // Bullet list block
    if (/^[-•*]\s/.test(line.trim())) {
      const items: string[] = [];
      while (i < lines.length && /^[-•*]\s/.test((lines[i] ?? '').trim())) {
        items.push((lines[i] ?? '').trim().replace(/^[-•*]\s/, ''));
        i++;
      }
      nodes.push(
        <ul key={i} className="list-disc list-outside pl-4 space-y-0.5 my-1">
          {items.map((item, j) => (
            <li key={j}>{renderInline(item)}</li>
          ))}
        </ul>
      );
      continue;
    }

    // Numbered list block
    if (/^\d+\.\s/.test(line.trim())) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test((lines[i] ?? '').trim())) {
        items.push((lines[i] ?? '').trim().replace(/^\d+\.\s/, ''));
        i++;
      }
      nodes.push(
        <ol key={i} className="list-decimal list-outside pl-4 space-y-0.5 my-1">
          {items.map((item, j) => (
            <li key={j}>{renderInline(item)}</li>
          ))}
        </ol>
      );
      continue;
    }

    // Regular paragraph
    nodes.push(
      <p key={i} className="my-0.5">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return <div className="space-y-0.5">{nodes}</div>;
}

function renderInline(text: string): React.ReactNode {
  // Split on **bold** and [text](url) patterns
  const parts = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-slate-800">
          {part.slice(2, -2)}
        </strong>
      );
    }
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      return (
        <a
          key={i}
          href={linkMatch[2]}
          target="_blank"
          rel="noreferrer"
          className="text-accent underline underline-offset-2 hover:opacity-80"
        >
          {linkMatch[1]}
        </a>
      );
    }
    return part;
  });
}

const STORAGE_KEY = 'adonis-iris-history';
const PILL_KEY = 'adonis-iris-pill-shown';
const OPENED_KEY = 'adonis-iris-opened';
const MAX_STORED = 200;
const MAX_CONTEXT = 40;
const BUBBLE_SIZE = typeof window !== 'undefined' && window.innerWidth < 640 ? 44 : 56;
const PANEL_WIDTH = 480;
const PANEL_HEIGHT = 560; // approximate — used for initial placement only

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

function defaultPos() {
  const isMobile = window.innerWidth < 768;
  return {
    x: window.innerWidth - BUBBLE_SIZE - (isMobile ? 16 : 24),
    y: window.innerHeight - BUBBLE_SIZE - (isMobile ? 88 : 24),
  };
}

export default function CoPilot() {
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPill, setShowPill] = useState(false);
  const [pillSlideIn, setPillSlideIn] = useState(false);
  const [pulsing, setPulsing] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
  // null = not yet mounted (SSR safe)
  const { userId, isAdmin } = useUser();
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const pillDismissTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const drag = useRef({
    active: false,
    moved: false,
    startX: 0,
    startY: 0,
    startPosX: 0,
    startPosY: 0,
  });

  // Set initial position after mount and attach global drag listeners
  useEffect(() => {
    setPos(defaultPos());

    function onMove(e: PointerEvent) {
      if (!drag.current.active) return;
      const dx = e.clientX - drag.current.startX;
      const dy = e.clientY - drag.current.startY;
      if (Math.abs(dx) > 5 || Math.abs(dy) > 5) drag.current.moved = true;
      const newX = Math.max(
        0,
        Math.min(window.innerWidth - BUBBLE_SIZE, drag.current.startPosX + dx)
      );
      const newY = Math.max(
        0,
        Math.min(window.innerHeight - BUBBLE_SIZE, drag.current.startPosY + dy)
      );
      setPos({ x: newX, y: newY });
    }
    function onUp() {
      drag.current.active = false;
    }
    function onResize() {
      setPos((prev) => {
        if (!prev) return defaultPos();
        return {
          x: Math.max(0, Math.min(window.innerWidth - BUBBLE_SIZE, prev.x)),
          y: Math.max(0, Math.min(window.innerHeight - BUBBLE_SIZE, prev.y)),
        };
      });
    }
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('resize', onResize);
    };
  }, []);

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

  function handlePointerDown(e: React.PointerEvent<HTMLDivElement>) {
    drag.current.active = true;
    drag.current.moved = false;
    drag.current.startX = e.clientX;
    drag.current.startY = e.clientY;
    drag.current.startPosX = pos?.x ?? 0;
    drag.current.startPosY = pos?.y ?? 0;
  }

  function handleBubbleClick() {
    // Suppress click if the pointer was dragged
    if (drag.current.moved) return;
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

  async function handleSend(overrideText?: string) {
    const text = (overrideText ?? input).trim();
    if (!text) return;
    setInput('');
    const updated = [...messages, { role: 'user' as const, text }];
    setMessages(updated);
    setLoading(true);
    try {
      const res = await fetch('/api/copilot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: updated.slice(-MAX_CONTEXT),
          userId,
          isAdmin,
        }),
      });
      const data = await res.json();
      const reply = data.reply ?? data.error ?? STUB_REPLY;
      setMessages((prev) => [...prev, { role: 'assistant' as const, text: reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant' as const, text: `Error: ${String(err)}` },
      ]);
    }
    setLoading(false);
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(undefined);
    }
  }

  // Panel position: appear above/left of bubble, clamped to viewport
  function panelStyle(): React.CSSProperties {
    if (!pos) return { display: 'none' };
    const mobile = window.innerWidth < 640;
    if (mobile && expanded) {
      return {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 50,
        width: 'auto',
        borderRadius: 0,
      };
    }
    if (mobile) {
      return {
        position: 'fixed',
        bottom: 80,
        left: 8,
        right: 8,
        zIndex: 50,
        width: 'auto',
      };
    }
    const gap = 8;
    let top = pos.y - PANEL_HEIGHT - gap;
    if (top < 8) top = pos.y + BUBBLE_SIZE + gap;
    let left = pos.x + BUBBLE_SIZE - PANEL_WIDTH;
    left = Math.max(8, Math.min(window.innerWidth - PANEL_WIDTH - 8, left));
    return { position: 'fixed', top, left, zIndex: 50, width: PANEL_WIDTH };
  }

  if (!pos) return null;

  return (
    <>
      {/* Keyframes for pulse ring */}
      <style>{`
        @keyframes copilot-ring {
          0% { box-shadow: 0 0 0 0 rgba(15,61,62,0.35); }
          70% { box-shadow: 0 0 0 14px rgba(15,61,62,0); }
          100% { box-shadow: 0 0 0 0 rgba(15,61,62,0); }
        }
        .copilot-pulse { animation: copilot-ring 1.2s ease-out; }
        .copilot-bubble-wrap { touch-action: none; }
      `}</style>

      {/* Bubble wrapper — draggable, sized to the bubble only so pos.x/pos.y track the bubble edge */}
      <div
        className="copilot-bubble-wrap"
        style={{ position: 'fixed', left: pos.x, top: pos.y, zIndex: 50 }}
        onPointerDown={handlePointerDown}
      >
        {/* Discoverability pill — absolutely positioned to the left of the bubble */}
        {showPill && (
          <div
            style={{
              position: 'absolute',
              right: 'calc(100% + 12px)',
              top: '50%',
              transform: pillSlideIn
                ? 'translateY(-50%) translateX(0)'
                : 'translateY(-50%) translateX(12px)',
              transition: 'opacity 300ms, transform 300ms',
              opacity: pillSlideIn ? 1 : 0,
              background: 'white',
              color: '#0F3D3E',
              fontSize: '13px',
              padding: '8px 14px',
              borderRadius: '20px',
              boxShadow: '0 4px 14px rgba(15,61,62,0.18)',
              whiteSpace: 'nowrap',
              fontWeight: 500,
              pointerEvents: 'none',
            }}
          >
            Ask Iris
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
            <span
              className="absolute top-0 right-0 w-2 h-2 rounded-full bg-urgent z-10"
              style={{ outline: '2px solid #EFEFC8' }}
            />
          )}

          <button
            onClick={handleBubbleClick}
            style={{
              width: BUBBLE_SIZE,
              height: BUBBLE_SIZE,
              borderRadius: '50%',
              background: '#EFEFC8',
              color: '#0F3D3E',
              boxShadow: '0 4px 14px rgba(15, 61, 62, 0.18)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '22px',
              border: 'none',
              cursor: 'grab',
              transition: 'background 150ms',
            }}
            title="Iris — signal co-pilot (drag to move)"
          >
            {open ? (
              <span style={{ fontSize: 24, lineHeight: 1 }}>×</span>
            ) : (
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Chat panel — anchored relative to bubble position */}
      {open && (
        <div
          className="bg-white border border-line rounded-xl shadow-xl flex flex-col overflow-hidden"
          style={panelStyle()}
        >
          {/* Header */}
          <div
            className="px-4 py-3 flex items-center justify-between"
            style={{
              background:
                'radial-gradient(circle at 110% 120%, rgba(63, 215, 190, 0.55) 0%, transparent 55%), linear-gradient(135deg, #0A2A2B 0%, #0F3D3E 50%, #1A5E5C 100%)',
            }}
          >
            <div>
              <div className="text-white text-sm font-semibold">Iris</div>
              <div className="text-slate-400 text-[10px] font-mono">for Adonis · beta</div>
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
                onClick={() => setExpanded((e) => !e)}
                className="text-slate-400 hover:text-white transition leading-none sm:hidden"
                title={expanded ? 'Collapse' : 'Expand'}
              >
                {expanded ? (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="4 14 10 14 10 20" />
                    <polyline points="20 10 14 10 14 4" />
                    <line x1="10" y1="14" x2="3" y2="21" />
                    <line x1="21" y1="3" x2="14" y2="10" />
                  </svg>
                ) : (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="15 3 21 3 21 9" />
                    <polyline points="9 21 3 21 3 15" />
                    <line x1="21" y1="3" x2="14" y2="10" />
                    <line x1="3" y1="21" x2="10" y2="14" />
                  </svg>
                )}
              </button>
              <button
                onClick={() => setOpen(false)}
                className="text-slate-400 hover:text-white transition text-lg leading-none"
              >
                ×
              </button>
            </div>
          </div>

          {/* Messages */}
          <div
            className={`flex-1 overflow-y-auto p-4 space-y-3 ${expanded ? 'max-h-none' : 'max-h-[28rem] min-h-[12rem]'}`}
          >
            {messages.length === 0 && (
              <div className="space-y-2">
                <button
                  onClick={() =>
                    handleSend(
                      'Give me a morning briefing — urgent signals, top outreach opportunities, and key contacts to reach this week.'
                    )
                  }
                  className="w-full text-left px-3 py-2.5 rounded-xl text-xs font-semibold transition hover:opacity-90"
                  style={{ background: '#0F3D3E', color: '#EFEFC8' }}
                >
                  ⚡ Brief me on my territory
                </button>
                {[
                  'Who should I call this week?',
                  'Draft an outreach email for Ascension',
                  "What's urgent across my accounts?",
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs text-slate-600 border border-line hover:bg-paper transition"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}
            {messages.map((m, i) => {
              const isEmail = m.role === 'assistant' && /^Subject:/m.test(m.text);
              return (
                <div
                  key={i}
                  className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {isEmail ? (
                    <div className="w-full space-y-1.5">
                      <div className="bg-paper border border-line rounded-xl px-3 py-2.5 text-xs text-slate-700 leading-relaxed">
                        <IrisMessage text={m.text} />
                      </div>
                      <button
                        onClick={() => navigator.clipboard.writeText(m.text)}
                        className="text-[10px] font-mono text-accent hover:underline"
                      >
                        📋 Copy to clipboard
                      </button>
                    </div>
                  ) : (
                    <div
                      className={`max-w-[85%] text-xs px-3 py-2 rounded-xl leading-relaxed ${
                        m.role === 'user'
                          ? 'bg-accent text-white rounded-br-none'
                          : 'bg-paper text-slate-700 rounded-bl-none'
                      }`}
                    >
                      {m.role === 'assistant' ? <IrisMessage text={m.text} /> : m.text}
                    </div>
                  )}
                </div>
              );
            })}
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
              onClick={() => handleSend(undefined)}
              disabled={!input.trim() || loading}
              className="px-3 py-2 rounded-lg transition hover:opacity-90 active:scale-95"
              style={{
                background: '#0F3D3E',
                color: '#EFEFC8',
                fontFamily: 'ui-monospace, monospace',
                fontSize: '13px',
                opacity: !input.trim() || loading ? 0.4 : 1,
              }}
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}

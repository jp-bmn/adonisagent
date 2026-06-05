'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  text: string;
}

const STORAGE_KEY = 'adonis-copilot-history';

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
    localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs));
  } catch {
    // storage full or unavailable — fail silently
  }
}

export default function CoPilot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load persisted history on mount
  useEffect(() => {
    setMessages(loadMessages());
  }, []);

  // Persist whenever messages change
  useEffect(() => {
    if (messages.length > 0) saveMessages(messages);
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
    // Stub response — Joel wires POST /api/v1/copilot in T-13.
    // When live, send `updated` as the conversation history for context.
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
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
      {open && (
        <div className="w-80 bg-white border border-line rounded-xl shadow-xl flex flex-col overflow-hidden">
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

          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-72 min-h-[8rem]">
            {messages.length === 0 && (
              <p className="text-xs text-slate-400 text-center">
                Ask about your accounts, signals, or territory.
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
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

      <button
        onClick={() => setOpen((o) => !o)}
        className="w-12 h-12 rounded-full bg-navy-900 text-white shadow-xl flex items-center justify-center hover:bg-navy-700 transition text-lg"
        title="Adonis Intel co-pilot"
      >
        {open ? '×' : '💬'}
      </button>
    </div>
  );
}

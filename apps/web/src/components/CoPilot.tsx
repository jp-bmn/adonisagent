'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  text: string;
}

type ClaudeModel = 'claude-haiku-4-5-20251001' | 'claude-sonnet-4-6' | 'claude-opus-4-7';

const MODELS: { id: ClaudeModel; label: string; note: string }[] = [
  { id: 'claude-haiku-4-5-20251001', label: 'Haiku', note: 'Fast · low cost' },
  { id: 'claude-sonnet-4-6', label: 'Sonnet', note: 'Balanced' },
  { id: 'claude-opus-4-7', label: 'Opus', note: 'Most capable' },
];

const STORAGE_KEY = 'adonis-copilot-history';
const MODEL_KEY = 'adonis-copilot-model';
const MAX_STORED = 200; // messages kept in localStorage (full scrollable history)
const MAX_CONTEXT = 40; // messages sent to Claude per request (working memory)

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

function loadModel(): ClaudeModel {
  try {
    const saved = localStorage.getItem(MODEL_KEY) as ClaudeModel | null;
    return MODELS.find((m) => m.id === saved)?.id ?? 'claude-sonnet-4-6';
  } catch {
    return 'claude-sonnet-4-6';
  }
}

export default function CoPilot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [model, setModel] = useState<ClaudeModel>('claude-sonnet-4-6');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showModelPicker, setShowModelPicker] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(loadMessages());
    setModel(loadModel());
  }, []);

  useEffect(() => {
    if (messages.length > 0) saveMessages(messages);
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function handleModelChange(m: ClaudeModel) {
    setModel(m);
    setShowModelPicker(false);
    try {
      localStorage.setItem(MODEL_KEY, m);
    } catch {
      // ignore
    }
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
    // The user sees the full history in the UI; Claude reasons on recent context only.
    //
    // const res = await fetch('/api/copilot', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     message: text,
    //     model,
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

  const currentModel = MODELS.find((m) => m.id === model)!;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
      {open && (
        <div className="w-80 bg-white border border-line rounded-xl shadow-xl flex flex-col overflow-hidden">
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

          {/* Model picker */}
          <div className="bg-navy-900 border-t border-white/10 px-4 pb-2 relative">
            <button
              onClick={() => setShowModelPicker((v) => !v)}
              className="text-[10px] font-mono text-slate-400 hover:text-white transition flex items-center gap-1"
            >
              <span className="text-slate-500">model:</span> {currentModel.label} ·{' '}
              {currentModel.note} ▾
            </button>
            {showModelPicker && (
              <div className="absolute left-4 top-6 bg-white border border-line rounded-lg shadow-lg z-10 overflow-hidden">
                {MODELS.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => handleModelChange(m.id)}
                    className={`w-full text-left px-4 py-2.5 text-xs flex items-center justify-between gap-6 hover:bg-paper transition ${
                      m.id === model ? 'font-semibold text-ink' : 'text-slate-600'
                    }`}
                  >
                    <span>{m.label}</span>
                    <span className="text-slate-400 font-normal">{m.note}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Messages */}
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

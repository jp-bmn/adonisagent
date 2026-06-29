'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });

    if (res.ok) {
      router.push('/');
      router.refresh();
    } else {
      setError('Incorrect password.');
      setLoading(false);
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{
        background:
          'radial-gradient(circle at 110% 100%, rgba(63, 215, 190, 0.55) 0%, transparent 55%), linear-gradient(135deg, #0A2A2B 0%, #0F3D3E 50%, #1A5E5C 100%)',
      }}
    >
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="font-serif text-3xl font-bold" style={{ color: '#EFEFC8' }}>
            Account Intel
          </h1>
          <p className="text-sm mt-1" style={{ color: 'rgba(239,239,200,0.5)' }}>
            for Adonis · Healthcare Revenue-Cycle Software
          </p>
        </div>
        <div className="bg-white/10 border border-white/20 rounded-xl p-8 backdrop-blur-sm">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                className="block text-xs font-semibold uppercase tracking-widest mb-1"
                style={{ color: 'rgba(239,239,200,0.6)' }}
              >
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm bg-white/10 border border-white/20 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Enter password"
                autoFocus
              />
            </div>
            {error && <p className="text-xs text-red-300">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full text-sm font-semibold py-2 rounded-lg hover:opacity-90 disabled:opacity-50"
              style={{ background: '#EFEFC8', color: '#0F3D3E' }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

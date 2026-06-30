import { login } from './actions';

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ message: string }>;
}) {
  const { message } = await searchParams;

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
          <form action={login} className="space-y-4">
            <div>
              <label
                className="block text-xs font-semibold uppercase tracking-widest mb-1"
                style={{ color: 'rgba(239,239,200,0.6)' }}
              >
                Email
              </label>
              <input
                type="email"
                name="email"
                required
                className="w-full rounded-lg px-3 py-2 text-sm bg-white/10 border border-white/20 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Enter email"
                autoFocus
              />
            </div>
            <div>
              <label
                className="block text-xs font-semibold uppercase tracking-widest mb-1"
                style={{ color: 'rgba(239,239,200,0.6)' }}
              >
                Password
              </label>
              <input
                type="password"
                name="password"
                required
                className="w-full rounded-lg px-3 py-2 text-sm bg-white/10 border border-white/20 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Enter password"
              />
            </div>
            {message && <p className="text-xs text-red-300">{message}</p>}
            <button
              type="submit"
              className="w-full text-sm font-semibold py-2 rounded-lg hover:opacity-90 disabled:opacity-50"
              style={{ background: '#EFEFC8', color: '#0F3D3E' }}
            >
              Sign in
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}


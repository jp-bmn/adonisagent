import './globals.css';
import Link from 'next/link';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Adonis Account Intelligence',
  description: 'Sales intelligence for the Adonis hospital prospecting team',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <div className="min-h-screen flex">
          <Sidebar />
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}

function Sidebar() {
  return (
    <aside className="w-56 bg-navy-900 text-slate-200 py-6 flex-none">
      <div className="px-5 pb-5 mb-3 border-b border-white/10 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-navy-700 flex items-center justify-center font-bold text-white">
          A
        </div>
        <div>
          <div className="text-white font-bold text-sm">Account Intel</div>
          <div className="text-[10px] font-mono text-slate-500 tracking-widest">ADONIS</div>
        </div>
      </div>
      <Nav />
    </aside>
  );
}

function Nav() {
  const items = [
    { href: '/', label: 'Signal feed', glyph: '▦' },
    { href: '/hospitals', label: 'Hospitals', glyph: '▢' },
    { href: '/alerts', label: 'Alerts', glyph: '◷' },
    { href: '/export', label: 'Export (CSV)', glyph: '↧' },
  ];
  return (
    <nav className="space-y-0.5">
      {items.map((i) => (
        <Link
          key={i.href}
          href={i.href}
          className="flex items-center gap-3 px-5 py-2.5 text-sm hover:bg-white/5 hover:text-white transition"
        >
          <span className="w-4 text-center opacity-80">{i.glyph}</span>
          {i.label}
        </Link>
      ))}
    </nav>
  );
}

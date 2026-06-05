import './globals.css';
import type { Metadata } from 'next';
import Nav from '@/components/Nav';
import CoPilot from '@/components/CoPilot';

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
        <CoPilot />
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

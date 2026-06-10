import './globals.css';
import { Suspense } from 'react';
import type { Metadata } from 'next';
import Nav from '@/components/Nav';
import CoPilot from '@/components/CoPilot';
import MobileNav from '@/components/MobileNav';
import DigestTracker from '@/components/DigestTracker';
import UserProvider from '@/components/UserProvider';

export const metadata: Metadata = {
  title: 'Adonis Account Intelligence',
  description: 'Sales intelligence for the Adonis hospital prospecting team',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {/* Mobile top bar */}
        <UserProvider>
          <MobileNav />
          <div className="min-h-screen flex">
            <Sidebar />
            <main className="flex-1 min-w-0">{children}</main>
          </div>
          <CoPilot />
          <Suspense>
            <DigestTracker />
          </Suspense>
        </UserProvider>
      </body>
    </html>
  );
}

function Sidebar() {
  return (
    <aside
      className="hidden md:flex md:flex-col w-56 text-slate-200 py-6 flex-none"
      style={{
        background:
          'radial-gradient(circle at 110% 120%, rgba(63, 215, 190, 0.55) 0%, transparent 55%), linear-gradient(135deg, #0A2A2B 0%, #0F3D3E 50%, #1A5E5C 100%)',
      }}
    >
      <div className="px-5 pb-5 mb-3 border-b border-white/10 flex items-center gap-3">
        {/* Adonis leaf mark — three leaf paths from adonis-logo.svg, leaf area only */}
        <svg
          viewBox="0 9 30 17"
          className="w-9 h-9 flex-none"
          fill="none"
          style={{ color: '#EFEFC8' }}
          aria-hidden="true"
        >
          <path
            d="M18.4987 15.9623C18.4987 12.1171 15.0001 9 15.0001 9C15.0001 9 11.5015 12.1171 11.5015 15.9623C11.5015 19.8075 15.0001 22.9247 15.0001 22.9247C15.0001 22.9247 18.4987 19.8075 18.4987 15.9623Z"
            fill="currentColor"
          />
          <path
            d="M7.92124 18.0659C11.3299 19.9884 12.3438 24.507 12.3438 24.507C12.3438 24.507 7.83132 25.9084 4.42265 23.9858C1.01398 22.0632 0 17.5446 0 17.5446C0 17.5446 4.51257 16.1433 7.92124 18.0659Z"
            fill="currentColor"
          />
          <path
            d="M22.0788 18.0658C18.6701 19.9884 17.6562 24.507 17.6562 24.507C17.6562 24.507 22.1687 25.9084 25.5774 23.9858C28.986 22.0632 30 17.5446 30 17.5446C30 17.5446 25.4874 16.1433 22.0788 18.0658Z"
            fill="currentColor"
          />
        </svg>
        <div>
          <div className="font-serif font-bold text-sm leading-tight" style={{ color: '#EFEFC8' }}>
            Account Intel
          </div>
          <div
            className="text-[9px] font-mono tracking-widest uppercase"
            style={{ color: 'rgba(239,239,200,0.5)' }}
          >
            for Adonis
          </div>
        </div>
      </div>
      <Nav />
    </aside>
  );
}

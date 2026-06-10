'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const items = [
  { href: '/', label: 'Feed', glyph: '▦' },
  { href: '/hospitals', label: 'Hospitals', glyph: '▢' },
  { href: '/review', label: 'Review', glyph: '◈' },
  { href: '/alerts', label: 'Alerts', glyph: '◷' },
  { href: '/export', label: 'Export', glyph: '↧' },
];

export default function MobileNav() {
  const pathname = usePathname();

  return (
    <>
      {/* Top bar — logo only */}
      <header
        className="md:hidden px-4 py-3 flex items-center gap-3 sticky top-0 z-40"
        style={{
          background:
            'radial-gradient(circle at 100% 150%, rgba(63, 215, 190, 0.4) 0%, transparent 70%), linear-gradient(90deg, #0A2A2B 0%, #0F3D3E 60%, #155959 100%)',
        }}
      >
        <svg
          viewBox="0 9 30 17"
          className="w-7 h-7 flex-none"
          fill="none"
          style={{ color: '#EFEFC8' }}
          aria-hidden="true"
        >
          <path d="M18.4987 15.9623C18.4987 12.1171 15.0001 9 15.0001 9C15.0001 9 11.5015 12.1171 11.5015 15.9623C11.5015 19.8075 15.0001 22.9247 15.0001 22.9247C15.0001 22.9247 18.4987 19.8075 18.4987 15.9623Z" fill="currentColor" />
          <path d="M7.92124 18.0659C11.3299 19.9884 12.3438 24.507 12.3438 24.507C12.3438 24.507 7.83132 25.9084 4.42265 23.9858C1.01398 22.0632 0 17.5446 0 17.5446C0 17.5446 4.51257 16.1433 7.92124 18.0659Z" fill="currentColor" />
          <path d="M22.0788 18.0658C18.6701 19.9884 17.6562 24.507 17.6562 24.507C17.6562 24.507 22.1687 25.9084 25.5774 23.9858C28.986 22.0632 30 17.5446 30 17.5446C30 17.5446 25.4874 16.1433 22.0788 18.0658Z" fill="currentColor" />
        </svg>
        <span className="font-serif font-bold text-sm" style={{ color: '#EFEFC8' }}>
          Account Intel
        </span>
      </header>

      {/* Bottom tab bar */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 border-t border-white/10 z-40 flex"
        style={{
          background:
            'radial-gradient(circle at 0% -50%, rgba(63, 215, 190, 0.35) 0%, transparent 60%), linear-gradient(90deg, #155959 0%, #0F3D3E 50%, #0A2A2B 100%)',
        }}
      >
        {items.map((item) => {
          const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-[10px] font-mono transition ${
                isActive ? 'text-cream font-semibold' : 'text-slate-400'
              }`}
            >
              <span className="text-base leading-none">{item.glyph}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

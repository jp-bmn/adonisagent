'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const items = [
  { href: '/', label: 'Signal feed', glyph: '▦' },
  { href: '/hospitals', label: 'Hospitals', glyph: '▢' },
  { href: '/review', label: 'Review queue', glyph: '◈' },
  { href: '/alerts', label: 'Alerts', glyph: '◷' },
  { href: '/export', label: 'Export (CSV)', glyph: '↧' },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav className="space-y-0.5">
      {items.map((item) => {
        const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-5 py-2.5 text-sm transition ${
              isActive
                ? 'bg-white/10 text-white'
                : 'text-slate-200 hover:bg-white/5 hover:text-white'
            }`}
          >
            <span className="w-4 text-center opacity-80">{item.glyph}</span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

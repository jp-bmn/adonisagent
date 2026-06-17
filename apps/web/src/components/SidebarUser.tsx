'use client';

import { useRouter } from 'next/navigation';
import { useUser } from '@/components/UserProvider';

export default function SidebarUser() {
  const { userName, isAdmin } = useUser();
  const router = useRouter();

  if (!userName) return null;

  const initials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="flex items-center gap-2.5 py-3">
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center flex-none text-[10px] font-bold cursor-default select-none"
        style={{ background: '#EFEFC8', color: '#0F3D3E' }}
        onDoubleClick={() => router.push('/dev')}
        title=""
      >
        {initials}
      </div>
      <div className="min-w-0">
        <div className="text-xs font-semibold text-white truncate">{userName}</div>
        <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wide">
          {isAdmin ? 'Admin' : 'Account Executive'}
        </div>
      </div>
    </div>
  );
}

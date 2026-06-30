'use client';

import { usePathname } from 'next/navigation';
import { Suspense } from 'react';
import CoPilot from '@/components/CoPilot';
import MobileNav from '@/components/MobileNav';
import DigestTracker from '@/components/DigestTracker';
import UserProvider from '@/components/UserProvider';

export default function ShellGuard({
  children,
  sidebar,
}: {
  children: React.ReactNode;
  sidebar: React.ReactNode;
}) {
  const pathname = usePathname();

  if (pathname === '/login') {
    return <>{children}</>;
  }

  return (
    <UserProvider>
      <MobileNav />
      <div className="min-h-screen flex">
        {sidebar}
        <main className="flex-1 min-w-0">{children}</main>
      </div>
      <CoPilot />
      <Suspense>
        <DigestTracker />
      </Suspense>
    </UserProvider>
  );
}

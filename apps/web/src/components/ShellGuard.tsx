'use client';

import { usePathname } from 'next/navigation';

export default function ShellGuard({
  children,
  shell,
}: {
  children: React.ReactNode;
  shell: React.ReactNode;
}) {
  const pathname = usePathname();

  if (pathname === '/login') {
    return <>{children}</>;
  }

  return <>{shell}</>;
}

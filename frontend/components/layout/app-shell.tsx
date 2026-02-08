'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { PropsWithChildren } from 'react';

import { cn } from '@/components/ui/cn';

const NAV_LINKS = [
  { href: '/', label: 'Overview' },
  { href: '/services', label: 'Services' },
  { href: '/incidents', label: 'Incidents' },
];

export default function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-sm uppercase tracking-widest text-slate-500">SignalSentry</p>
            <h1 className="text-xl font-semibold text-white">AI System Reliability Dashboard</h1>
          </div>
          <span className="text-xs text-slate-400">Realtime SRE telemetry</span>
        </div>
      </header>
      <div className="mx-auto flex max-w-6xl gap-6 px-6 py-8">
        <aside className="w-48 border-r border-slate-800 pr-4">
          <nav className="flex flex-col gap-2 text-sm">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'rounded-md px-3 py-2 text-slate-300 transition hover:bg-slate-800 hover:text-white',
                  pathname === link.href && 'bg-slate-800 text-white'
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="flex-1 pb-16">{children}</main>
      </div>
    </div>
  );
}

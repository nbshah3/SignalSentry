'use client';

import { useMemo, useState } from 'react';
import useSWR from 'swr';

import { apiGet } from '@/lib/api';
import type { LogEntry, ServiceLogsResponse } from '@/types/api';

const LEVELS = ['ALL', 'ERROR', 'WARN', 'INFO'];

const buildPath = (service: string, level?: string, query?: string) => {
  const params = new URLSearchParams();
  if (level && level !== 'ALL') params.set('level', level);
  if (query) params.set('query', query);
  const suffix = params.toString() ? `?${params.toString()}` : '';
  return `/services/${encodeURIComponent(service)}/logs${suffix}`;
};

export function LogViewer({ service, initialLogs }: { service: string; initialLogs: LogEntry[] }) {
  const [level, setLevel] = useState<string>('ALL');
  const [query, setQuery] = useState<string>('');

  const { data } = useSWR<ServiceLogsResponse>(
    ['logs', service, level, query],
    async () => apiGet<ServiceLogsResponse>(buildPath(service, level, query)),
    {
      fallbackData: { service, items: initialLogs },
      revalidateOnFocus: false,
    }
  );

  const logs = useMemo(() => data?.items ?? [], [data]);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="flex flex-col gap-4 border-b border-slate-800 px-6 py-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Recent logs</h3>
          <p className="text-sm text-slate-400">Filter by level or keyword to inspect the latest context.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {LEVELS.map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevel(lvl)}
              className={`rounded-full px-3 py-1 text-xs uppercase tracking-widest ${
                lvl === level ? 'bg-slate-100 text-slate-900' : 'bg-slate-800 text-slate-400'
              }`}
            >
              {lvl}
            </button>
          ))}
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="keyword"
            className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-sm text-white focus:border-slate-400"
          />
        </div>
      </div>
      <div className="max-h-96 overflow-y-auto text-sm">
        <table className="min-w-full divide-y divide-slate-800">
          <thead className="bg-slate-900/60 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Time</th>
              <th className="px-4 py-2">Level</th>
              <th className="px-4 py-2">Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="whitespace-nowrap px-4 py-2 text-slate-400">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-semibold ${levelColor(log.level)}`}
                  >
                    {log.level}
                  </span>
                </td>
                <td className="px-4 py-2 text-slate-200">
                  <p>{log.message}</p>
                  {log.request_id && <p className="text-xs text-slate-500">req: {log.request_id}</p>}
                </td>
              </tr>
            ))}
            {!logs.length && (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-center text-slate-500">
                  No logs match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function levelColor(level: string) {
  switch (level) {
    case 'ERROR':
      return 'bg-rose-500/20 text-rose-200';
    case 'WARN':
      return 'bg-amber-500/20 text-amber-200';
    default:
      return 'bg-slate-800 text-slate-200';
  }
}

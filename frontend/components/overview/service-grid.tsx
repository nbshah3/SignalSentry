'use client';

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { ServiceSummary } from '@/types/api';

const formatNumber = (value?: number | null, suffix = '') =>
  value === undefined || value === null ? '—' : `${value.toFixed(0)}${suffix}`;

const formatPercent = (value?: number | null) =>
  value === undefined || value === null ? '—' : `${(value * 100).toFixed(1)}%`;

export function ServiceGrid({ services }: { services: ServiceSummary[] }) {
  if (!services.length) {
    return null;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {services.map((service) => (
        <article key={service.service} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm uppercase tracking-widest text-slate-500">{service.service}</p>
              <p className="text-xl font-semibold text-white">{formatNumber(service.latency_p95_ms, ' ms')}</p>
              <p className="text-sm text-slate-400">latency · error rate {formatPercent(service.error_rate)}</p>
            </div>
            <div className="text-right text-sm text-slate-400">
              <p>CPU {formatNumber(service.cpu_pct, '%')}</p>
              <p>Memory {formatNumber(service.memory_rss_mb, ' MB')}</p>
            </div>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {Object.entries(service.sparklines).map(([metric, points]) => (
              <div key={metric} className="flex flex-col">
                <span className="text-xs uppercase tracking-widest text-slate-500">{metric}</span>
                <div className="h-24">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={points} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
                      <XAxis dataKey="timestamp" hide />
                      <YAxis hide domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                        labelFormatter={(label) => new Date(label).toLocaleTimeString()}
                      />
                      <Line type="monotone" dataKey="value" stroke="#38bdf8" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

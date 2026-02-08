'use client';

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import type { MetricSeriesResponse } from '@/types/api';

export function ServiceMetrics({ series }: { series: Record<string, MetricSeriesResponse> }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {Object.entries(series).map(([metric, payload]) => (
        <article key={metric} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="mb-2 flex items-center justify-between text-sm text-slate-400">
            <span className="uppercase tracking-widest">{metric}</span>
            <span>{payload.points.at(-1)?.value?.toFixed(2) ?? '—'}</span>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={payload.points} margin={{ top: 10, left: 0, right: 0, bottom: 0 }}>
                <XAxis dataKey="timestamp" hide />
                <YAxis hide domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1f2937' }}
                  labelFormatter={(label) => new Date(label).toLocaleTimeString()}
                />
                <Line type="monotone" dataKey="value" dot={false} stroke="#34d399" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </article>
      ))}
    </div>
  );
}

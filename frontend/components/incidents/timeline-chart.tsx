'use client';

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import type { IncidentTimelineResponse } from '@/types/api';

export function TimelineChart({ timeline }: { timeline: IncidentTimelineResponse }) {
  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <h3 className="text-lg font-semibold text-white">Timeline · {timeline.metric}</h3>
      <p className="text-sm text-slate-400">Baseline {timeline.baseline?.toFixed(2) ?? '—'} vs observed {timeline.observed?.toFixed(2) ?? '—'}</p>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timeline.points} margin={{ top: 10, left: 0, right: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="timeline" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} minTickGap={32} stroke="#475569" />
            <YAxis stroke="#475569" domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1f2937' }}
              labelFormatter={(label) => new Date(label).toLocaleTimeString()}
            />
            <Area type="monotone" dataKey="value" stroke="#38bdf8" fill="url(#timeline)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

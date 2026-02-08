import type { Incident, ServiceSummary } from '@/types/api';

const formatPercent = (value?: number | null) =>
  value === undefined || value === null ? '—' : `${(value * 100).toFixed(1)}%`;

export function KpiCards({ incidents, services }: { incidents: Incident[]; services: ServiceSummary[] }) {
  const topLatency = services
    .map((service) => ({ service: service.service, value: service.latency_p95_ms ?? 0 }))
    .sort((a, b) => b.value - a.value)[0];

  const topError = services
    .map((service) => ({ service: service.service, value: service.error_rate ?? 0 }))
    .sort((a, b) => b.value - a.value)[0];

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <p className="text-sm uppercase tracking-widest text-slate-500">Active incidents</p>
        <p className="mt-3 text-4xl font-semibold text-white">{incidents.length}</p>
        <p className="mt-1 text-sm text-slate-400">across {services.length} services</p>
      </article>
      <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <p className="text-sm uppercase tracking-widest text-slate-500">Highest latency</p>
        <p className="mt-3 text-2xl font-semibold text-white">
          {topLatency?.value ? `${topLatency.value.toFixed(0)} ms` : '—'}
        </p>
        <p className="mt-1 text-sm text-slate-400">{topLatency?.service || 'No data'}</p>
      </article>
      <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <p className="text-sm uppercase tracking-widest text-slate-500">Highest error rate</p>
        <p className="mt-3 text-2xl font-semibold text-white">{formatPercent(topError?.value)}</p>
        <p className="mt-1 text-sm text-slate-400">{topError?.service || 'No data'}</p>
      </article>
    </div>
  );
}

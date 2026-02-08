import { notFound } from 'next/navigation';

import { LogViewer } from '@/components/services/log-viewer';
import { ServiceMetrics } from '@/components/services/service-metrics';
import { fetchServiceLogs, fetchServiceMetricSeries, fetchServiceSummary } from '@/lib/data';
import type { MetricSeriesResponse } from '@/types/api';

const METRICS = ['latency_p95_ms', 'error_rate', 'cpu_pct', 'memory_rss_mb'];

export default async function ServiceDetailPage({ params }: { params: { service: string } }) {
  const serviceId = decodeURIComponent(params.service);
  const summary = await fetchServiceSummary();
  const selected = summary.find((svc) => svc.service === serviceId);
  if (!selected) {
    notFound();
  }

  const metricSeries = await Promise.all(
    METRICS.map(async (metric) => {
      try {
        const series = await fetchServiceMetricSeries(serviceId, metric);
        return [metric, series] as [string, MetricSeriesResponse];
      } catch (error) {
        return [metric, { service: serviceId, metric, points: [] }] as [string, MetricSeriesResponse];
      }
    })
  );
  const initialLogs = await fetchServiceLogs(serviceId);

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-sm uppercase tracking-widest text-slate-500">Service</p>
        <h1 className="text-3xl font-semibold text-white">{serviceId}</h1>
        <p className="mt-2 text-slate-300">
          Latency {(selected.latency_p95_ms ?? 0).toFixed(0)} ms · Error rate {(selected.error_rate ?? 0).toFixed(3)} · CPU{' '}
          {(selected.cpu_pct ?? 0).toFixed(1)}%
        </p>
      </div>
      <ServiceMetrics series={Object.fromEntries(metricSeries)} />
      <LogViewer service={serviceId} initialLogs={initialLogs.items} />
    </section>
  );
}

import Link from 'next/link';

import { fetchServiceSummary } from '@/lib/data';

export default async function ServicesPage() {
  const services = await fetchServiceSummary();

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-white">Services</h2>
      <p className="text-sm text-slate-400">Select a service to view detailed metrics and logs.</p>
      <div className="grid gap-4 lg:grid-cols-2">
        {services.map((service) => (
          <Link
            key={service.service}
            href={`/services/${service.service}`}
            className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-600"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-widest text-slate-500">{service.service}</p>
                <p className="text-xl font-semibold text-white">
                  {service.latency_p95_ms ? `${service.latency_p95_ms.toFixed(0)} ms latency` : 'No latency data'}
                </p>
              </div>
              <div className="text-right text-sm text-slate-400">
                <p>Error rate {(service.error_rate ?? 0).toFixed(2)}</p>
                <p>CPU {(service.cpu_pct ?? 0).toFixed(1)}%</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}

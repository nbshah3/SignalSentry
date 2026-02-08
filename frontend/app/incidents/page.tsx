import Link from 'next/link';

import { fetchActiveIncidents, fetchRecentIncidents } from '@/lib/data';

export default async function IncidentsPage() {
  const [active, recent] = await Promise.all([fetchActiveIncidents(), fetchRecentIncidents()]);

  const Section = ({ title, items }: { title: string; items: typeof active }) => (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      <ul className="divide-y divide-slate-800">
        {items.map((incident) => (
          <li key={incident.id} className="px-6 py-4">
            <Link href={`/incidents/${incident.id}`} className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-widest text-slate-500">{incident.service}</p>
                <p className="text-lg font-semibold text-white">{incident.metric}</p>
                <p className="text-sm text-slate-400">{incident.summary || 'Anomaly detected'}</p>
              </div>
              <div className="text-right text-xs text-slate-500">
                <p>Severity {incident.severity}</p>
                <p>{new Date(incident.detected_at).toLocaleString()}</p>
              </div>
            </Link>
          </li>
        ))}
        {!items.length && (
          <li className="px-6 py-8 text-center text-sm text-slate-500">No incidents yet.</li>
        )}
      </ul>
    </div>
  );

  return (
    <section className="space-y-6">
      <Section title="Active" items={active} />
      <Section title="Recent" items={recent} />
    </section>
  );
}

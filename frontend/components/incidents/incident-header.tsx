import Link from 'next/link';

import type { Incident } from '@/types/api';

export function IncidentHeader({ incident }: { incident: Incident }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <p className="text-sm uppercase tracking-widest text-slate-500">Incident #{incident.id}</p>
          <h1 className="text-3xl font-semibold text-white">
            {incident.service} · {incident.metric}
          </h1>
          <p className="mt-2 text-slate-300">Severity {incident.severity} · {incident.summary || 'Anomaly detected'}</p>
        </div>
        <div className="text-sm text-slate-400">
          <p>
            Window {new Date(incident.window_start).toLocaleTimeString()} –{' '}
            {new Date(incident.window_end).toLocaleTimeString()}
          </p>
          <p>Detected {new Date(incident.detected_at).toLocaleString()}</p>
          <Link href={`/services/${incident.service}`} className="text-sky-400 hover:underline">
            View service
          </Link>
        </div>
      </div>
    </div>
  );
}

import type { Incident } from '@/types/api';

export function IncidentList({ incidents }: { incidents: Incident[] }) {
  if (!incidents.length) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 text-slate-400">
        No active incidents — detectors are quiet.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-4">
        <h3 className="text-lg font-semibold text-white">Active incidents</h3>
        <p className="text-sm text-slate-400">Realtime anomalies detected by the backend</p>
      </div>
      <ul className="divide-y divide-slate-800">
        {incidents.map((incident) => (
          <li key={incident.id} className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-widest text-slate-500">{incident.service}</p>
                <p className="text-lg font-semibold text-white">
                  {incident.metric} · severity {incident.severity}
                </p>
                <p className="text-sm text-slate-400">{incident.summary || 'Anomaly detected'}</p>
              </div>
              <div className="text-right text-xs text-slate-500">
                <p>Detected {new Date(incident.detected_at).toLocaleTimeString()}</p>
                <p>
                  Window {new Date(incident.window_start).toLocaleTimeString()} –{' '}
                  {new Date(incident.window_end).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

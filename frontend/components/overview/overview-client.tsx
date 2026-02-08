'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { apiGet, apiPost } from '@/lib/api';
import type { Incident, IncidentListResponse, ServiceSummary, ServiceSummaryResponse } from '@/types/api';

import { IncidentList } from './incident-list';
import { KpiCards } from './kpi-cards';
import { ServiceGrid } from './service-grid';

const STREAM_URL = (process.env.NEXT_PUBLIC_STREAM_URL || 'http://localhost:8000/stream/events').replace(/\/$/, '');

export function OverviewClient({
  initialIncidents,
  initialServices,
}: {
  initialIncidents: Incident[];
  initialServices: ServiceSummary[];
}) {
  const [incidents, setIncidents] = useState<Incident[]>(initialIncidents);
  const [services, setServices] = useState<ServiceSummary[]>(initialServices);
  const [isSimulating, setIsSimulating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const lastRefresh = useRef<number>(Date.now());

  const refreshServices = useCallback(async () => {
    const now = Date.now();
    if (now - lastRefresh.current < 8000) return;
    lastRefresh.current = now;
    const data = await apiGet<ServiceSummaryResponse>('/services/summary');
    setServices(data.services);
  }, []);

  const upsertIncident = useCallback((next: Incident) => {
    setIncidents((prev) => {
      const filtered = prev.filter((item) => item.id !== next.id);
      return [next, ...filtered].slice(0, 10);
    });
  }, []);

  useEffect(() => {
    const source = new EventSource(STREAM_URL);
    source.onmessage = async (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'incident_alert' && payload.incident_id) {
          const incident = await apiGet<Incident>(`/incidents/${payload.incident_id}`);
          upsertIncident(incident);
        }
        if (payload.type === 'metric_update') {
          refreshServices();
        }
      } catch (error) {
        console.error('event stream error', error);
      }
    };
    return () => source.close();
  }, [refreshServices, upsertIncident]);

  const runSimulation = useCallback(async () => {
    try {
      setIsSimulating(true);
      const result = await apiPost<{ incidents: number }>('/incidents/simulate');
      setMessage(`Simulated ${result.incidents} incidents`);
      // refresh lists after backend work completes
      const data = await apiGet<IncidentListResponse>('/incidents/active');
      setIncidents(data.items);
      refreshServices();
    } catch (error) {
      setMessage('Simulation failed');
    } finally {
      setIsSimulating(false);
      setTimeout(() => setMessage(null), 6000);
    }
  }, [refreshServices]);

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Realtime monitoring</h2>
          <p className="text-sm text-slate-400">SSE stream keeps this view synchronized with the backend.</p>
          {message && <p className="text-sm text-slate-300">{message}</p>}
        </div>
        <button
          onClick={runSimulation}
          disabled={isSimulating}
          className="rounded-full bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-sky-400 disabled:opacity-50"
        >
          {isSimulating ? 'Simulating…' : 'Simulate incident'}
        </button>
      </div>
      <KpiCards incidents={incidents} services={services} />
      <ServiceGrid services={services.slice(0, 4)} />
      <IncidentList incidents={incidents} />
    </section>
  );
}

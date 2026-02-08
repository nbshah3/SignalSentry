import { apiGet, apiPost } from '@/lib/api';
import type {
  Incident,
  IncidentListResponse,
  IncidentRefreshResponse,
  IncidentTimelineResponse,
  MetricSeriesResponse,
  RootCauseResponse,
  ServiceLogsResponse,
  ServiceSummary,
  ServiceSummaryResponse,
} from '@/types/api';

const SHOULD_AUTO_SEED =
  process.env.NODE_ENV !== 'production' || process.env.NEXT_PUBLIC_AUTO_SEED === 'true';

export async function ensureDemoData(): Promise<boolean> {
  if (!SHOULD_AUTO_SEED) {
    return false;
  }
  try {
    const result = await apiPost<{ seeded?: boolean; reason?: string }>(`/admin/seed`);
    const refresh = await apiPost<IncidentRefreshResponse>(`/incidents/refresh`);
    return Boolean(result.seeded || refresh.incidents_created);
  } catch (error) {
    console.warn('auto-seed failed', error);
    return false;
  }
}

export async function fetchActiveIncidents(): Promise<Incident[]> {
  const data = await apiGet<IncidentListResponse>('/incidents/active');
  return data.items;
}

export async function fetchRecentIncidents(): Promise<Incident[]> {
  const data = await apiGet<IncidentListResponse>('/incidents/recent');
  return data.items;
}

export async function fetchIncident(incidentId: string): Promise<Incident> {
  return apiGet<Incident>(`/incidents/${incidentId}`);
}

export async function fetchIncidentTimeline(incidentId: string): Promise<IncidentTimelineResponse> {
  return apiGet<IncidentTimelineResponse>(`/incidents/${incidentId}/timeline`);
}

export async function fetchIncidentAnalysis(incidentId: string): Promise<RootCauseResponse> {
  return apiGet<RootCauseResponse>(`/incidents/${incidentId}/analysis`);
}

export async function fetchServiceSummary(): Promise<ServiceSummary[]> {
  const data = await apiGet<ServiceSummaryResponse>('/services/summary');
  return data.services;
}

export async function fetchServiceMetricSeries(service: string, metric: string): Promise<MetricSeriesResponse> {
  return apiGet<MetricSeriesResponse>(`/services/${encodeURIComponent(service)}/metrics?metric=${metric}`);
}

export async function fetchServiceLogs(service: string, params?: { level?: string; query?: string }): Promise<ServiceLogsResponse> {
  const search = new URLSearchParams();
  if (params?.level) search.set('level', params.level);
  if (params?.query) search.set('query', params.query);
  const suffix = search.toString() ? `?${search.toString()}` : '';
  return apiGet<ServiceLogsResponse>(`/services/${encodeURIComponent(service)}/logs${suffix}`);
}

import { apiGet } from '@/lib/api';
import type {
  Incident,
  IncidentListResponse,
  MetricSeriesResponse,
  ServiceLogsResponse,
  ServiceSummary,
  ServiceSummaryResponse,
} from '@/types/api';

export async function fetchActiveIncidents(): Promise<Incident[]> {
  const data = await apiGet<IncidentListResponse>('/incidents/active');
  return data.items;
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

import { apiGet } from '@/lib/api';
import type { Incident, IncidentListResponse, ServiceSummary, ServiceSummaryResponse } from '@/types/api';

export async function fetchActiveIncidents(): Promise<Incident[]> {
  const data = await apiGet<IncidentListResponse>('/incidents/active');
  return data.items;
}

export async function fetchServiceSummary(): Promise<ServiceSummary[]> {
  const data = await apiGet<ServiceSummaryResponse>('/services/summary');
  return data.services;
}

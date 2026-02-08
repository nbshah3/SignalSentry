export type Incident = {
  id: number;
  incident_key: string;
  service: string;
  metric: string;
  severity: number;
  summary?: string | null;
  detected_at: string;
  window_start: string;
  window_end: string;
  status: string;
};

export type IncidentListResponse = {
  items: Incident[];
};

export type SparklinePoint = {
  timestamp: string;
  value: number;
};

export type ServiceSummary = {
  service: string;
  latency_p95_ms?: number | null;
  error_rate?: number | null;
  cpu_pct?: number | null;
  memory_rss_mb?: number | null;
  sparklines: Record<string, SparklinePoint[]>;
};

export type ServiceSummaryResponse = {
  services: ServiceSummary[];
};

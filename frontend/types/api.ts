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

export type MetricSeriesResponse = {
  service: string;
  metric: string;
  points: SparklinePoint[];
};

export type LogEntry = {
  id: number;
  service: string;
  timestamp: string;
  level: string;
  message: string;
  request_id?: string | null;
  latency_ms?: number | null;
  context?: Record<string, unknown> | null;
};

export type ServiceLogsResponse = {
  service: string;
  items: LogEntry[];
};

export type RootCauseResponse = {
  incident_id: number;
  service: string;
  metric: string;
  hypotheses: Array<{
    title: string;
    confidence: number;
    evidence: Array<{ type: string; detail: string }>;
  }>;
};

export type IncidentTimelineResponse = {
  incident_id: number;
  metric: string;
  points: SparklinePoint[];
  baseline?: number | null;
  observed?: number | null;
};

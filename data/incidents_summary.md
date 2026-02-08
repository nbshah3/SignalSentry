# Sample Incident Scenarios

| Key | Service | Metric | Window (UTC) | Description |
| --- | ------- | ------ | ------------ | ----------- |
| api_latency_spike | api-gateway | latency_p95_ms | 2024-03-01T01:00Z – 2024-03-01T01:15Z | Gradual DB saturation driving elevated latency and timeout logs. |
| auth_error_surge | auth-service | error_rate | 2024-03-01T00:30Z – 2024-03-01T00:42Z | Upstream identity provider instability causing bursts of 5xx responses. |
| worker_memory_leak | analytics-worker | memory_rss_mb | 2024-03-01T00:40Z onward | Memory leak culminating in OOM warnings. |

These scenarios power the anomaly detection + root-cause demo flows.

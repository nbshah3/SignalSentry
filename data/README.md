# Data Directory

This folder contains deterministic sample datasets that showcase three incident scenarios:

1. **Latency spike** on `api-gateway` between minutes 60–75.
2. **Error-rate spike** on `auth-service` between minutes 30–42.
3. **Memory leak** on `analytics-worker` after minute 40.

## Files

- `sample_metrics.jsonl` — Minute-level metrics (`latency_p95_ms`, `error_rate`, `cpu_pct`, `memory_rss_mb`). Each line matches the `/ingest/metrics` JSON schema.
- `sample_logs.jsonl` — Focused log snippets with keywords useful for the root-cause engine.
- `generate_sample_data.py` — Deterministic script (seeded with 42) used to regenerate the JSONL fixtures.

## Usage

To re-generate the datasets:

```bash
python3 data/generate_sample_data.py
```

To ingest metrics:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/metrics \
  -H "Content-Type: application/json" \
  -d "$(python -c 'import json; print(json.dumps({"metrics": [json.loads(line) for line in open("data/sample_metrics.jsonl")]}) )' )"
```

Use a similar pattern for logs and the `/ingest/logs` endpoint.

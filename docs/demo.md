# SignalSentry Demo Script

This guide walks through a 5-minute demo that highlights log/metric ingestion, anomaly detection, realtime updates, root-cause hints, and postmortem export.

## 1. Prep the environment

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload

# In a second terminal for the frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Visit `http://localhost:3000` to keep the dashboard open.

## 2. Ingest sample metrics + logs

The repo ships with deterministic fixtures. Use the helper snippets below from the repo root.

```bash
# Metrics
python - <<'PY'
import json
from pathlib import Path
import requests

metrics = [json.loads(line) for line in Path('data/sample_metrics.jsonl').read_text().splitlines()]
payload = json.dumps({'metrics': metrics[:200]})
requests.post('http://localhost:8000/api/v1/ingest/metrics', data=payload, headers={'Content-Type': 'application/json'})
PY

# Logs
python - <<'PY'
import json
from pathlib import Path
import requests

logs = [json.loads(line) for line in Path('data/sample_logs.jsonl').read_text().splitlines()]
payload = json.dumps({'logs': logs})
requests.post('http://localhost:8000/api/v1/ingest/logs', data=payload, headers={'Content-Type': 'application/json'})
PY
```

You should now see incidents appear on the overview page.

## 3. Trigger realtime updates

- Click **Simulate incident** on the overview page. This replays seeded data and sends SSE updates without a page refresh.
- Watch active incidents and service cards update instantly.

## 4. Drill into services and incidents

1. Navigate to `/services` → choose `api-gateway` to showcase metric sparklines + log viewer filters.
2. Go to `/incidents` → select an incident to view the timeline, hypotheses, and evidence list.
3. Mention that the root-cause hints pull from metric correlations (`latency` vs `error_rate`, etc.) and log keywords (`timeout`, `OOM`).

## 5. Export a postmortem

Use `curl` (or API docs) to export a JSON + PDF snapshot:

```bash
curl -X POST http://localhost:8000/api/v1/incidents/1/postmortem
```

Grab the download links from the response (served from `/api/v1/postmortems/<file>`).

## 6. Wrap-up talking points

- Architecture: FastAPI + SQLite + SSE + Next.js + Recharts.
- Deterministic sample data & simulator for repeatable demos.
- Tests/lint/CI + Cloud Run / Vercel ready deployment steps in the README.

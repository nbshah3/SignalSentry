# SignalSentry: AI System Reliability & Monitoring Dashboard

SignalSentry is a portfolio-ready, cloud-friendly reliability platform that ingests logs + metrics, detects anomalies, correlates root causes, and visualizes everything through a realtime dashboard.

## Architecture

```
                           ┌─────────────────────────────┐
                           │        Next.js + SWR        │
                           │  Tailwind + Recharts UI     │
                           └──────────────┬──────────────┘
                                          │ SSE / REST
                                          │
                    ┌─────────────────────▼────────────────────┐
                    │              FastAPI API                 │
                    │  • Ingestion endpoints                   │
                    │  • Anomaly + root-cause engines         │
                    │  • SSE event bus / simulator            │
                    └──────────────┬──────────────┬────────────┘
                                   │              │
                             SQLite / Postgres    │
                                   │              │
                              Seed data +      Postmortem
                             incident store      exports
```

## Highlights

- Dual ingestion (JSON + file upload) for logs and metrics.
- Deterministic anomaly detectors (z-score + EWMA) with severity scoring and incident windows.
- Root-cause hints powered by metric correlations + log keyword heuristics.
- Realtime SSE stream, plus a deterministic simulator for demos.
- Postmortem export endpoint (JSON + PDF via ReportLab) with download links.
- Next.js dashboard with service detail, incident detail, log viewer filters, and streaming updates.
- Tests (pytest), lint/format (ruff + black + ESLint), and GitHub Actions CI.

## Repository Layout

```
SignalSentry/
├── backend/      # FastAPI app, detectors, SSE, simulator, tests
├── frontend/     # Next.js + Tailwind dashboard
├── data/         # Seeded sample metrics/logs
├── docs/         # Demo script, screenshots, deployment notes
├── infra/        # Docker compose + runtime references
└── exports/      # Postmortem artifacts (gitignored)
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) Docker + Docker Compose

### Environment files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Update `NEXT_PUBLIC_API_BASE_URL` / `NEXT_PUBLIC_STREAM_URL` if the backend runs on a different host.

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --port 3000
```

Visit `http://localhost:3000` for the dashboard. Alternatively run everything via Docker Compose:

```bash
docker compose up --build
```

## Sample Data & Incident Simulation

- `data/sample_metrics.jsonl` and `data/sample_logs.jsonl` contain deterministic scenarios:
  - `api-gateway` latency spike
  - `auth-service` error-rate surge
  - `analytics-worker` memory leak
- Regenerate fixtures anytime via `python3 data/generate_sample_data.py`.
- Ingest fixtures with the snippets in `docs/demo.md`.
- Use the **Simulate incident** button (overview page) to replay seeded metrics/logs and watch SSE updates without refreshing.

## How Anomaly Detection Works

1. **Metric windows** – the detector pulls recent series per service/metric.
2. **Baselines** – rolling mean + EWMA establish expected behavior.
3. **Scoring** – z-score, percent delta, and EWMA deviation combine into a 0–100 severity score.
4. **Incidents** – spikes above the threshold persist as incidents with windows + baseline/observed values.
5. **Root-cause hints** – the hint engine correlates the primary metric against other tracked metrics and scans logs for keywords (`timeout`, `db saturation`, `memory leak`, etc.) to output ranked hypotheses with evidence + confidence.

## Testing & Quality Gates

```bash
# Backend
cd backend
ruff check app
black --check app
pytest

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Deployment

### Backend → Cloud Run

1. Build & push the image:
   ```bash
   cd backend
   gcloud builds submit --tag gcr.io/<PROJECT>/signalsentry-backend
   ```
2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy signalsentry-api \
     --image gcr.io/<PROJECT>/signalsentry-backend \
     --region=<REGION> \
     --allow-unauthenticated \
     --set-env-vars="DATABASE_URL=sqlite:///./signalsentry.db,POSTMORTEM_EXPORT_DIR=/tmp/exports"
   ```
3. Attach a managed volume or Cloud SQL if you need persistent storage.

### Frontend → Vercel (or Cloud Run)

1. Push the repo and import it into Vercel.
2. Configure env vars:
   - `NEXT_PUBLIC_API_BASE_URL=https://<cloud-run-url>`
   - `NEXT_PUBLIC_STREAM_URL=https://<cloud-run-url>/stream/events`
3. Vercel runs `npm run build` automatically. For Cloud Run, build the Dockerfile in `frontend/` and deploy similar to the backend.

## Docs & Screenshots

- Demo walkthrough: [`docs/demo.md`](docs/demo.md)
- Placeholder screenshots (add your captures here):
  - `docs/images/overview.png`
  - `docs/images/service-detail.png`
  - `docs/images/incident-detail.png`

## What to Verify Before Pushing to GitHub

- `backend`: `ruff check`, `black --check`, and `pytest` all succeed.
- `frontend`: `npm run lint`, `npm run typecheck`, `npm run build` succeed.
- `docker compose up` starts both services and the dashboard shows seeded incidents.
- CI workflow (`.github/workflows/ci.yml`) passes locally or in a dry run.

# SignalSentry: AI System Reliability & Monitoring Dashboard

SignalSentry is a lightweight SRE-style reliability platform focused on ingesting service logs and metrics, detecting anomalies, providing root-cause hints, and surfacing everything in a clean dashboard optimized for cloud-native teams.

## Repository Layout

```
SignalSentry/
├── backend/    # FastAPI service, anomaly detection, SSE stream
├── frontend/   # Next.js dashboard
├── infra/      # Docker, deployment descriptors
├── data/       # Seeded sample logs + metrics
├── docs/       # Architecture notes, demo script, deployment guide
└── exports/    # Generated postmortems and downloadable artifacts
```

## Architecture Overview (placeholder)

```
[client] -> Next.js dashboard -> FastAPI API -> SQLite/Postgres
                                 |                ^
                                 +--> detectors ---+
```

A more detailed diagram plus deployment notes will be added alongside the first backend/infra commits.

## Roadmap

The implementation follows the staged commit plan provided in the project brief to keep progress organized and reviewable.

## Local Development (preview)

- Requirements, environment variables, and one-command startup scripts will be documented once the backend and frontend scaffolds are in place.
- Docker Compose based workflows will land in the next commits.

Stay tuned for the full build-out!

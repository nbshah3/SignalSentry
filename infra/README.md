# Infra Overview

- `docker-compose.yml`: Spins up FastAPI backend and Next.js frontend for local dev.
- `backend/Dockerfile`: Python runtime with FastAPI + detector stack.
- `frontend/Dockerfile`: Next.js build + production runner.
- Environment templates live in `backend/.env.example`, `frontend/.env.local.example`, and the repo-level `.env.example`.

Future commits will introduce Terraform/GCP deployment helpers alongside Cloud Run build steps.

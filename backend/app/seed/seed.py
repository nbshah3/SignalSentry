from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from sqlalchemy import delete, func, select
from sqlmodel import Session

from app.models import Incident, LogEntry, MetricPoint
from app.schemas import LogCreate, MetricPointCreate
from app.services.incident_detector import IncidentDetector

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
METRICS_FILE = DATA_DIR / "demo_metrics.json"
LOGS_FILE = DATA_DIR / "demo_logs.json"

SERVICES = ["auth-service", "payments", "search", "recommendation-engine"]


def seed_sample_data(session: Session, *, force: bool = False) -> Dict[str, object]:
    metric_count = session.exec(select(func.count(MetricPoint.id))).one()
    log_count = session.exec(select(func.count(LogEntry.id))).one()

    if not force and (metric_count or log_count):
        return {"seeded": False, "reason": "dataset already present"}

    if force:
        session.exec(delete(Incident))
        session.exec(delete(MetricPoint))
        session.exec(delete(LogEntry))
        session.commit()

    raw_metrics = _load_json(METRICS_FILE)
    raw_logs = _load_json(LOGS_FILE)

    # --- Make demo data "recent" ---
    # Find the latest timestamp in the demo payloads and shift everything so the latest point is ~now.
    latest_demo_ts = _latest_timestamp(raw_metrics, raw_logs)
    now = datetime.now(timezone.utc)
    shift = now - latest_demo_ts

    metrics = [_build_metric(entry, shift=shift) for entry in raw_metrics]
    logs = [_build_log(entry, shift=shift) for entry in raw_logs]

    session.add_all(metrics)
    session.add_all(logs)
    session.commit()

    # Optionally run detection once so incidents exist immediately if detector flags anything
    detector = IncidentDetector(session)
    incidents = detector.evaluate_all_services()

    return {
        "seeded": True,
        "metrics": len(metrics),
        "logs": len(logs),
        "incidents": len(incidents),
    }


def _build_metric(entry: Dict[str, object], *, shift: timedelta) -> MetricPoint:
    timestamp = _parse_timestamp(entry["timestamp"]) + shift
    payload = MetricPointCreate(
        service=entry["service"],
        metric=entry["metric"],
        timestamp=timestamp,
        value=float(entry["value"]),
    )
    return MetricPoint.model_validate(payload)


def _build_log(entry: Dict[str, object], *, shift: timedelta) -> LogEntry:
    payload = LogCreate(
        service=entry["service"],
        timestamp=_parse_timestamp(entry["timestamp"]) + shift,
        level=entry.get("level", "INFO"),
        request_id=entry.get("request_id"),
        message=entry.get("message", ""),
        latency_ms=entry.get("latency_ms"),
        context=entry.get("context"),
    )
    return LogEntry(
        service=payload.service,
        timestamp=payload.timestamp,
        level=payload.level,
        request_id=payload.request_id,
        message=payload.message,
        latency_ms=payload.latency_ms,
        context=json.dumps(payload.context) if payload.context else None,
    )


def _load_json(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_timestamp(value: str) -> datetime:
    # normalize Zulu time to offset format
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    # ensure timezone-aware (UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _latest_timestamp(
    metrics: List[Dict[str, object]], logs: List[Dict[str, object]]
) -> datetime:
    latest = datetime(1970, 1, 1, tzinfo=timezone.utc)
    for entry in metrics:
        ts = _parse_timestamp(entry["timestamp"])
        if ts > latest:
            latest = ts
    for entry in logs:
        ts = _parse_timestamp(entry["timestamp"])
        if ts > latest:
            latest = ts
    return latest

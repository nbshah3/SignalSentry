from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from sqlalchemy import delete, func, select
from sqlmodel import Session

from app.models import Incident, LogEntry, MetricPoint
from app.schemas import LogCreate, MetricPointCreate
from app.services.incident_detector import IncidentDetector

BASE_PATH = Path(__file__).resolve()
DATA_FILENAMES = {
    "metrics": "demo_metrics.json",
    "logs": "demo_logs.json",
}

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

    metrics_payload, logs_payload = _load_payloads()
    metrics = [_build_metric(entry) for entry in metrics_payload]
    logs = [_build_log(entry) for entry in logs_payload]
    session.add_all(metrics)
    session.add_all(logs)
    session.commit()

    detector = IncidentDetector(session)
    incidents = detector.evaluate_all_services()

    return {
        "seeded": True,
        "metrics": len(metrics),
        "logs": len(logs),
        "incidents": len(incidents),
    }


def _build_metric(entry: Dict[str, object]) -> MetricPoint:
    timestamp = _parse_timestamp(entry["timestamp"])
    payload = MetricPointCreate(
        service=entry["service"],
        metric=entry["metric"],
        timestamp=timestamp,
        value=float(entry["value"]),
    )
    return MetricPoint.model_validate(payload)


def _build_log(entry: Dict[str, object]) -> LogEntry:
    payload = LogCreate(
        service=entry["service"],
        timestamp=_parse_timestamp(entry["timestamp"]),
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


def _load_payloads() -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    metrics = _load_from_disk(DATA_FILENAMES["metrics"])
    logs = _load_from_disk(DATA_FILENAMES["logs"])
    if metrics is not None and logs is not None:
        return metrics, logs
    return _generate_demo_payloads()


def _load_from_disk(filename: str) -> List[Dict[str, object]] | None:
    for candidate in _candidate_dirs():
        path = candidate / filename
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _candidate_dirs() -> Iterable[Path]:
    seen = set()
    parents = [BASE_PATH.parent]
    for idx in range(min(4, len(BASE_PATH.parents))):
        parents.append(BASE_PATH.parents[idx])
    for ancestor in parents:
        candidate = ancestor / "data"
        if candidate not in seen:
            seen.add(candidate)
            yield candidate
    yield Path("/app/data")


def _generate_demo_payloads() -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    rng = random.Random(1337)
    base_time = datetime.utcnow() - timedelta(minutes=30)
    services = {
        "auth-service": {"latency_ms": 110.0, "error_rate": 0.01},
        "payments": {"latency_ms": 95.0, "error_rate": 0.012},
        "search": {"latency_ms": 80.0, "error_rate": 0.008},
        "recommendation-engine": {"latency_ms": 130.0, "error_rate": 0.009},
    }
    metrics: List[Dict[str, object]] = []
    logs: List[Dict[str, object]] = []
    for idx in range(30):
        timestamp = (base_time + timedelta(minutes=idx)).isoformat() + "Z"
        for service, baselines in services.items():
            latency = baselines["latency_ms"] + rng.uniform(-5, 5)
            error = baselines["error_rate"] + rng.uniform(-0.002, 0.002)
            if service == "payments" and idx >= 25:
                latency += 140
                error += 0.04
            metrics.append(
                {
                    "service": service,
                    "metric": "latency_ms",
                    "timestamp": timestamp,
                    "value": round(latency, 3),
                }
            )
            metrics.append(
                {
                    "service": service,
                    "metric": "error_rate",
                    "timestamp": timestamp,
                    "value": round(max(error, 0), 4),
                }
            )
    for service in services:
        for i in range(5):
            ts = (base_time + timedelta(minutes=i * 3)).isoformat() + "Z"
            logs.append(
                {
                    "service": service,
                    "timestamp": ts,
                    "level": "ERROR" if service == "payments" and i >= 3 else "INFO",
                    "request_id": f"demo-{service}-{i}",
                    "message": (
                        f"{service} anomaly detected"
                        if service == "payments" and i >= 3
                        else f"{service} heartbeat"
                    ),
                    "latency_ms": 320 if service == "payments" and i >= 3 else None,
                    "context": {"service": service, "idx": i},
                }
            )
    return metrics, logs


def _parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)

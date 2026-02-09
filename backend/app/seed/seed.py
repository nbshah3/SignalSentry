from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
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
METRIC_NAME_MAP = {
    "latency_ms": "latency_p95_ms",
    "latency": "latency_p95_ms",
    "cpu_usage": "cpu_pct",
    "cpu": "cpu_pct",
    "memory_usage": "memory_rss_mb",
    "memory": "memory_rss_mb",
}
DEFAULT_METRICS = ("latency_p95_ms", "error_rate", "cpu_pct", "memory_rss_mb")


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

    raw_metrics, raw_logs = _load_payloads()
    latest_demo_ts = _latest_timestamp(raw_metrics, raw_logs)
    now = datetime.now(timezone.utc)
    shift = now - latest_demo_ts if latest_demo_ts else timedelta(0)

    metrics = [_build_metric(entry, shift=shift) for entry in raw_metrics]
    logs = [_build_log(entry, shift=shift) for entry in raw_logs]

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


def _build_metric(entry: Dict[str, object], *, shift: timedelta) -> MetricPoint:
    timestamp = _parse_timestamp(entry["timestamp"]) + shift
    metric_name = METRIC_NAME_MAP.get(
        entry.get("metric", ""), entry.get("metric", "latency_p95_ms")
    )
    payload = MetricPointCreate(
        service=entry["service"],
        metric=metric_name,
        timestamp=timestamp,
        value=float(entry["value"]),
    )
    return MetricPoint.model_validate(payload)


def _build_log(entry: Dict[str, object], *, shift: timedelta) -> LogEntry:
    latency = entry.get("latency_ms")
    if latency is None:
        latency = entry.get("latency_p95_ms")
    payload = LogCreate(
        service=entry["service"],
        timestamp=_parse_timestamp(entry["timestamp"]) + shift,
        level=entry.get("level", "INFO"),
        request_id=entry.get("request_id"),
        message=entry.get("message", ""),
        latency_ms=latency,
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
    for directory in _candidate_dirs():
        path = directory / filename
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _candidate_dirs() -> Iterable[Path]:
    seen: set[Path] = set()
    candidates = []
    for parent_index in (3, 2):
        try:
            parent = BASE_PATH.parents[parent_index]
        except IndexError:
            continue
        candidate = parent / "data"
        if candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)
    seed_dir = BASE_PATH.parent / "data"
    if seed_dir not in seen:
        seen.add(seed_dir)
        candidates.append(seed_dir)
    candidates.append(Path("/app/data"))
    return candidates


def _generate_demo_payloads() -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    rng = random.Random(1337)
    base_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    baselines: Dict[str, Dict[str, float]] = {
        "auth-service": {
            "latency_p95_ms": 140.0,
            "error_rate": 0.012,
            "cpu_pct": 48.0,
            "memory_rss_mb": 620.0,
        },
        "payments": {
            "latency_p95_ms": 110.0,
            "error_rate": 0.01,
            "cpu_pct": 55.0,
            "memory_rss_mb": 660.0,
        },
        "search": {
            "latency_p95_ms": 90.0,
            "error_rate": 0.007,
            "cpu_pct": 60.0,
            "memory_rss_mb": 640.0,
        },
        "recommendation-engine": {
            "latency_p95_ms": 150.0,
            "error_rate": 0.009,
            "cpu_pct": 58.0,
            "memory_rss_mb": 700.0,
        },
    }

    metrics: List[Dict[str, object]] = []
    logs: List[Dict[str, object]] = []

    for idx in range(60):
        timestamp = (base_time + timedelta(minutes=idx)).isoformat().replace("+00:00", "Z")
        for service, values in baselines.items():
            for metric in DEFAULT_METRICS:
                baseline = values.get(metric, 0.0)
                noise = baseline * rng.uniform(-0.05, 0.05)
                value = baseline + noise
                if (
                    service == "payments"
                    and metric in {"latency_p95_ms", "error_rate"}
                    and idx >= 45
                ):
                    if metric == "latency_p95_ms":
                        value += 180
                    else:
                        value += 0.05
                metrics.append(
                    {
                        "service": service,
                        "metric": metric,
                        "timestamp": timestamp,
                        "value": round(value, 4),
                    }
                )

    for service in baselines:
        for i in range(8):
            ts = (base_time + timedelta(minutes=i * 5)).isoformat().replace("+00:00", "Z")
            is_error = service == "payments" and i >= 4
            logs.append(
                {
                    "service": service,
                    "timestamp": ts,
                    "level": "ERROR" if is_error else "INFO",
                    "request_id": f"demo-{service}-{i}",
                    "message": (
                        "payments latency spike detected" if is_error else f"{service} heartbeat"
                    ),
                    "latency_ms": 330 + i * 10 if is_error else None,
                    "context": {"service": service, "index": i},
                }
            )
    return metrics, logs


def _parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _latest_timestamp(
    metrics: List[Dict[str, object]], logs: List[Dict[str, object]]
) -> datetime | None:
    latest: datetime | None = None
    for entry in metrics + logs:
        ts = _parse_timestamp(entry["timestamp"])
        if latest is None or ts > latest:
            latest = ts
    return latest

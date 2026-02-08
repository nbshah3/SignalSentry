from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from sqlalchemy import delete, func, select
from sqlmodel import Session

from app.models import LogEntry, MetricPoint

SEED = 1337
TOTAL_MINUTES = 360
SERVICES = {
    "auth": {
        "latency_p95_ms": 140.0,
        "error_rate": 0.02,
        "cpu_pct": 48.0,
        "memory_rss_mb": 620.0,
    },
    "payments": {
        "latency_p95_ms": 120.0,
        "error_rate": 0.015,
        "cpu_pct": 54.0,
        "memory_rss_mb": 580.0,
    },
    "search": {
        "latency_p95_ms": 95.0,
        "error_rate": 0.01,
        "cpu_pct": 62.0,
        "memory_rss_mb": 660.0,
    },
}


@dataclass
class IncidentWindow:
    service: str
    metric: str
    start_minute: int
    end_minute: int
    delta: float = 0.0
    trend_per_minute: float = 0.0
    logs: Tuple[str, ...] = ()

    def apply(self, minute: int, value: float) -> float:
        if minute < self.start_minute or minute > self.end_minute:
            return value
        updated = value + self.delta
        if self.trend_per_minute:
            updated += (minute - self.start_minute) * self.trend_per_minute
        return updated


INCIDENTS: Tuple[IncidentWindow, ...] = (
    IncidentWindow(
        service="search",
        metric="latency_p95_ms",
        start_minute=160,
        end_minute=210,
        delta=190.0,
        logs=(
            "timeout contacting shard alpha",
            "db saturation detected on replica",
            "upstream request_id req-981 timed out",
        ),
    ),
    IncidentWindow(
        service="payments",
        metric="error_rate",
        start_minute=120,
        end_minute=170,
        delta=0.18,
        logs=(
            "connection reset from card network",
            "5xx surge from fraud-service",
            "payment gateway timeout",
        ),
    ),
    IncidentWindow(
        service="auth",
        metric="memory_rss_mb",
        start_minute=200,
        end_minute=TOTAL_MINUTES - 1,
        trend_per_minute=2.2,
        logs=(
            "memory leak suspected in token generator",
            "OOM killer likely if usage continues",
            "cache flush unable to reclaim memory",
        ),
    ),
)


def seed_sample_data(session: Session, *, force: bool = False) -> Dict[str, object]:
    metric_count = session.exec(select(func.count(MetricPoint.id))).one()
    log_count = session.exec(select(func.count(LogEntry.id))).one()
    if not force and (metric_count or log_count):
        return {"seeded": False, "reason": "dataset already present"}

    if force:
        session.exec(delete(MetricPoint))
        session.exec(delete(LogEntry))
        session.commit()

    metrics = _build_metrics()
    logs = _build_logs()
    session.add_all(metrics)
    session.add_all(logs)
    session.commit()
    return {"seeded": True, "metrics": len(metrics), "logs": len(logs)}


def _build_metrics() -> List[MetricPoint]:
    rng = random.Random(SEED)
    base_time = datetime.utcnow() - timedelta(minutes=TOTAL_MINUTES)
    metrics: List[MetricPoint] = []
    for offset in range(TOTAL_MINUTES):
        timestamp = base_time + timedelta(minutes=offset)
        for service, config in SERVICES.items():
            for metric, baseline in config.items():
                value = _metric_with_noise(rng, baseline)
                for window in INCIDENTS:
                    if window.service == service and window.metric == metric:
                        value = window.apply(offset, value)
                if metric == "error_rate":
                    value = max(value, 0.0)
                metrics.append(
                    MetricPoint(
                        service=service,
                        metric=metric,
                        timestamp=timestamp,
                        value=round(value, 4),
                    )
                )
    return metrics


def _metric_with_noise(rng: random.Random, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    noise = rng.uniform(-0.05, 0.05) * baseline
    return baseline + noise


def _build_logs() -> List[LogEntry]:
    base_time = datetime.utcnow() - timedelta(minutes=TOTAL_MINUTES)
    logs: List[LogEntry] = []
    for window in INCIDENTS:
        for idx, message in enumerate(window.logs):
            timestamp = base_time + timedelta(minutes=window.start_minute + idx * 3)
            logs.append(
                LogEntry(
                    service=window.service,
                    level="ERROR",
                    timestamp=timestamp,
                    request_id=f"{window.service}-{window.metric}-{idx}",
                    message=message,
                    latency_ms=320.0 if "timeout" in message else None,
                    context=None,
                )
            )
    return logs

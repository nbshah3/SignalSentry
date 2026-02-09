"""Generate deterministic sample logs and metrics for SignalSentry demos."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

random.seed(42)
BASE_PATH = Path(__file__).resolve().parent
START = datetime(2024, 3, 1, 0, 0, 0)
TOTAL_POINTS = 120  # two hours of minute-level data


@dataclass
class IncidentWindow:
    service: str
    metric: str
    start_idx: int
    end_idx: int
    magnitude: float


LATENCY_SPIKE = IncidentWindow("api-gateway", "latency_p95_ms", 60, 75, 120.0)
ERROR_SPIKE = IncidentWindow("auth-service", "error_rate", 30, 42, 0.18)
MEMORY_LEAK = IncidentWindow("analytics-worker", "memory_rss_mb", 40, 119, 2.5)


SERVICES = {
    "api-gateway": {
        "latency_p95_ms": 140.0,
        "error_rate": 0.01,
        "cpu_pct": 42.0,
    },
    "auth-service": {
        "latency_p95_ms": 95.0,
        "error_rate": 0.02,
        "cpu_pct": 38.0,
    },
    "analytics-worker": {
        "memory_rss_mb": 620.0,
        "cpu_pct": 55.0,
        "latency_p95_ms": 180.0,
    },
}


INCIDENT_WINDOWS = [LATENCY_SPIKE, ERROR_SPIKE, MEMORY_LEAK]


def create_metric_points() -> List[Dict[str, object]]:
    points: List[Dict[str, object]] = []
    for idx in range(TOTAL_POINTS):
        ts = (START + timedelta(minutes=idx)).isoformat() + "Z"
        noise = random.normalvariate
        for service, base_metrics in SERVICES.items():
            for metric, base_value in base_metrics.items():
                value = base_value + noise(0, base_value * 0.02)

                for incident in INCIDENT_WINDOWS:
                    if (
                        incident.service == service
                        and incident.metric == metric
                        and incident.start_idx <= idx <= incident.end_idx
                    ):
                        if metric == "memory_rss_mb":
                            # slow leak trend rather than sudden spike
                            value += (idx - incident.start_idx) * incident.magnitude
                        else:
                            value += incident.magnitude

                value = round(max(value, 0), 3)
                points.append(
                    {
                        "service": service,
                        "metric": metric,
                        "timestamp": ts,
                        "value": value,
                    }
                )

    return points


def create_log_events() -> List[Dict[str, object]]:
    logs: List[Dict[str, object]] = []
    log_templates = [
        {
            "timestamp": (START + timedelta(minutes=62)).isoformat() + "Z",
            "service": "api-gateway",
            "level": "ERROR",
            "latency_ms": 320,
            "message": "Checkout timeout while waiting on db-primary",
            "context": {
                "request_id": "req-501",
                "path": "/checkout",
                "keyword": "timeout",
            },
        },
        {
            "timestamp": (START + timedelta(minutes=65)).isoformat() + "Z",
            "service": "api-gateway",
            "level": "ERROR",
            "latency_ms": 410,
            "message": "DB saturation suspected: connection pool exhausted",
            "context": {
                "request_id": "req-777",
                "path": "/orders",
                "keyword": "DB saturation",
            },
        },
        {
            "timestamp": (START + timedelta(minutes=34)).isoformat() + "Z",
            "service": "auth-service",
            "level": "ERROR",
            "message": "Increased 5xx rate from identity provider",
            "context": {"request_id": "req-320", "upstream": "idp", "keyword": "5xx"},
        },
        {
            "timestamp": (START + timedelta(minutes=36)).isoformat() + "Z",
            "service": "auth-service",
            "level": "ERROR",
            "message": "token issuance failed: connection reset by peer",
            "context": {"request_id": "req-458", "keyword": "connection reset"},
        },
        {
            "timestamp": (START + timedelta(minutes=90)).isoformat() + "Z",
            "service": "analytics-worker",
            "level": "WARN",
            "message": "memory usage exceeded 90% of container limit",
            "context": {"keyword": "memory leak", "rss_mb": 1024},
        },
        {
            "timestamp": (START + timedelta(minutes=100)).isoformat() + "Z",
            "service": "analytics-worker",
            "level": "ERROR",
            "message": "process unstable: OOM killer likely",
            "context": {"keyword": "OOM", "rss_mb": 1180},
        },
    ]
    logs.extend(log_templates)
    return logs


def write_jsonl(path: Path, records: List[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def main() -> None:
    metrics = create_metric_points()
    logs = create_log_events()

    write_jsonl(BASE_PATH / "sample_metrics.jsonl", metrics)
    write_jsonl(BASE_PATH / "sample_logs.jsonl", logs)


if __name__ == "__main__":
    main()

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple

from sqlmodel import Session

from app.crud import logs as log_crud
from app.crud import metrics as metric_crud
from app.models import LogEntry, MetricPoint
from app.schemas import LogCreate, MetricPointCreate
from app.seed import SERVICES

__all__ = ["IncidentSimulator", "SimulationPlan"]

SIM_SEED = 2024


@dataclass
class SimulationPlan:
    key: str
    service: str
    metric: str
    delta: float = 0.0
    trend_per_minute: float = 0.0
    logs: Tuple[str, ...] = ()


PLANS: Tuple[SimulationPlan, ...] = (
    SimulationPlan(
        key="search-latency",
        service="search",
        metric="latency_p95_ms",
        delta=180.0,
        logs=(
            "search timeout escalating",
            "upstream shard saturation",
            "queue depth exceeded",
        ),
    ),
    SimulationPlan(
        key="payments-error-rate",
        service="payments",
        metric="error_rate",
        delta=0.22,
        logs=(
            "card network 5xx burst",
            "connection reset by peer",
            "timeout hitting risk-engine",
        ),
    ),
    SimulationPlan(
        key="auth-memory",
        service="auth",
        metric="memory_rss_mb",
        trend_per_minute=2.5,
        logs=(
            "memory leak suspected",
            "OOM killer likely",
            "container swap usage climbing",
        ),
    ),
)


class IncidentSimulator:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.rng = random.Random(SIM_SEED)

    def run(self, minutes: int = 45) -> Tuple[List[MetricPoint], List[LogEntry], SimulationPlan]:
        plan = self.rng.choice(PLANS)
        metrics_payload = self._build_metrics(plan, minutes)
        logs_payload = self._build_logs(plan)
        metrics = metric_crud.bulk_create_metrics(self.session, metrics_payload)
        logs = log_crud.bulk_create_logs(self.session, logs_payload)
        return list(metrics), list(logs), plan

    def _build_metrics(self, plan: SimulationPlan, minutes: int) -> List[MetricPointCreate]:
        baseline = SERVICES.get(plan.service, {}).get(plan.metric, 100.0)
        latest = metric_crud.get_latest_metric(self.session, plan.service, plan.metric)
        start_time = latest.timestamp if latest else datetime.utcnow()
        payload: List[MetricPointCreate] = []
        for idx in range(minutes):
            timestamp = start_time + timedelta(minutes=idx + 1)
            value = self._with_noise(baseline)
            if idx >= minutes // 3:
                value += plan.delta
            if plan.trend_per_minute:
                value += idx * plan.trend_per_minute
            if plan.metric == "error_rate":
                value = max(value, 0.0)
            payload.append(
                MetricPointCreate(
                    service=plan.service,
                    metric=plan.metric,
                    timestamp=timestamp,
                    value=round(value, 4),
                )
            )
        return payload

    def _build_logs(self, plan: SimulationPlan) -> List[LogCreate]:
        base_timestamp = datetime.utcnow()
        logs: List[LogCreate] = []
        for idx, message in enumerate(plan.logs):
            logs.append(
                LogCreate(
                    timestamp=base_timestamp + timedelta(minutes=idx * 2),
                    service=plan.service,
                    level="ERROR",
                    request_id=f"simulate-{plan.key}-{idx}",
                    message=message,
                    latency_ms=350 if "timeout" in message else None,
                    context={"plan": plan.key},
                )
            )
        return logs

    def _with_noise(self, baseline: float) -> float:
        if baseline == 0:
            return 0.0
        noise = self.rng.uniform(-0.04, 0.04) * baseline
        return baseline + noise

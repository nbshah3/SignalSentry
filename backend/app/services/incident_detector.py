from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from sqlmodel import Session

from app.crud import incidents as incident_crud
from app.crud import metrics as metric_crud
from app.models import Incident
from app.services.anomaly import detect_for_series

TrackedMetric = Tuple[str, str]
DEFAULT_METRICS: Sequence[str] = (
    "latency_p95_ms",
    "error_rate",
    "cpu_pct",
    "memory_rss_mb",
)


class IncidentDetector:
    def __init__(self, session: Session) -> None:
        self.session = session

    def evaluate_metric(self, service: str, metric: str) -> Incident | None:
        series = metric_crud.get_metric_series(
            self.session, service=service, metric=metric, limit=240
        )
        if not series:
            return None

        payload = [(point.timestamp, point.value) for point in series]
        assessment = detect_for_series(payload, metric=metric)
        if not assessment:
            return None

        incident = incident_crud.upsert_incident(
            session=self.session,
            incident_key=f"{service}:{metric}",
            service=service,
            metric=metric,
            assessment=assessment,
        )
        return incident

    def evaluate_metrics(self, metrics: Iterable[TrackedMetric]) -> List[Incident]:
        incidents: List[Incident] = []
        for service, metric in metrics:
            incident = self.evaluate_metric(service, metric)
            if incident:
                incidents.append(incident)
        return incidents

    def evaluate_all_services(self) -> List[Incident]:
        return self.evaluate_metrics(self.candidate_pairs())

    def candidate_pairs(self) -> List[TrackedMetric]:
        tracked = incident_crud.list_tracked_metrics(self.session)
        if tracked:
            return tracked

        pairs: List[TrackedMetric] = []

        services = metric_crud.list_services(self.session)
        for service in services:
            for metric in metric_crud.list_service_metrics(self.session, service):
                if metric in DEFAULT_METRICS:
                    pairs.append((service, metric))

        return pairs

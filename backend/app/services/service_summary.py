from __future__ import annotations

from typing import Dict, List

from sqlmodel import Session

from app.crud import metrics as metric_crud
from app.schemas.services import ServiceSummary

SUMMARY_METRICS = ["latency_p95_ms", "error_rate", "cpu_pct", "memory_rss_mb"]
SPARKLINE_METRICS = ["latency_p95_ms", "error_rate"]


class ServiceSummaryBuilder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def build(self) -> List[ServiceSummary]:
        services = metric_crud.list_services(self.session)
        summaries: List[ServiceSummary] = []
        for service in services:
            latest_values = self._latest_metrics(service)
            sparklines = self._sparkline_payload(service)
            summaries.append(
                ServiceSummary(
                    service=service,
                    latency_p95_ms=latest_values.get("latency_p95_ms"),
                    error_rate=latest_values.get("error_rate"),
                    cpu_pct=latest_values.get("cpu_pct"),
                    memory_rss_mb=latest_values.get("memory_rss_mb"),
                    sparklines=sparklines,
                )
            )
        return summaries

    def _latest_metrics(self, service: str) -> Dict[str, float]:
        values: Dict[str, float] = {}
        for metric in SUMMARY_METRICS:
            latest = metric_crud.get_latest_metric(self.session, service, metric)
            if latest:
                values[metric] = latest.value
        return values

    def _sparkline_payload(self, service: str) -> Dict[str, List[Dict[str, float]]]:
        payload: Dict[str, List[Dict[str, float]]] = {}
        for metric in SPARKLINE_METRICS:
            series = metric_crud.get_metric_series(self.session, service, metric, limit=30)
            if not series:
                continue
            payload[metric] = [
                {"timestamp": point.timestamp.isoformat(), "value": point.value}
                for point in series
            ]
        return payload

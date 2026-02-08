from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

from sqlmodel import Session

from app.crud import logs as log_crud
from app.crud import metrics as metric_crud
from app.models import LogEntry, MetricPoint
from app.schemas import LogCreate, MetricPointCreate


class IncidentSimulator:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.base_dir = Path(__file__).resolve().parents[3]
        self.metrics_path = self.base_dir / "data" / "sample_metrics.jsonl"
        self.logs_path = self.base_dir / "data" / "sample_logs.jsonl"

    def run(self, minutes: int = 60) -> Tuple[List[MetricPoint], List[LogEntry]]:
        metrics_payload = self._load_metrics(minutes)
        logs_payload = self._load_logs()
        metrics = metric_crud.bulk_create_metrics(self.session, metrics_payload)
        logs = log_crud.bulk_create_logs(self.session, logs_payload)
        return list(metrics), list(logs)

    def _load_metrics(self, minutes: int) -> List[MetricPointCreate]:
        if not self.metrics_path.exists():
            return []
        payload: List[MetricPointCreate] = []
        now = datetime.utcnow()
        with self.metrics_path.open() as handle:
            for idx, line in enumerate(handle):
                if idx >= minutes * 4:
                    break
                record = json.loads(line)
                timestamp = now - timedelta(minutes=minutes - (idx % minutes))
                payload.append(
                    MetricPointCreate(
                        service=record["service"],
                        metric=record["metric"],
                        timestamp=timestamp,
                        value=record["value"],
                    )
                )
        return payload

    def _load_logs(self) -> List[LogCreate]:
        if not self.logs_path.exists():
            return []
        payload: List[LogCreate] = []
        with self.logs_path.open() as handle:
            for line in handle:
                record = json.loads(line)
                payload.append(
                    LogCreate(
                        timestamp=datetime.utcnow(),
                        service=record["service"],
                        level=record.get("level", "INFO"),
                        request_id=record.get("context", {}).get("request_id"),
                        message=record["message"],
                        latency_ms=record.get("latency_ms"),
                        context=record.get("context"),
                    )
                )
        return payload

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional

from sqlmodel import Session, select

from app.models import MetricPoint
from app.schemas import MetricPointCreate


def create_metric(session: Session, metric_in: MetricPointCreate) -> MetricPoint:
    metric = MetricPoint(
        service=metric_in.service,
        metric=metric_in.metric,
        timestamp=metric_in.timestamp,
        value=metric_in.value,
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def bulk_create_metrics(
    session: Session, metric_points: Iterable[MetricPointCreate]
) -> List[MetricPoint]:
    entries = [
        MetricPoint(
            service=item.service,
            metric=item.metric,
            timestamp=item.timestamp,
            value=item.value,
        )
        for item in metric_points
    ]

    if not entries:
        return []

    session.add_all(entries)
    session.commit()

    for entry in entries:
        session.refresh(entry)

    return entries


def get_metric_series(
    session: Session, service: str, metric: str, limit: int = 200
) -> List[MetricPoint]:
    statement = (
        select(MetricPoint)
        .where(MetricPoint.service == service, MetricPoint.metric == metric)
        .order_by(MetricPoint.timestamp.desc())
        .limit(limit)
    )
    results = session.exec(statement).all()
    return list(reversed(results))


def get_latest_metric(session: Session, service: str, metric: str) -> Optional[MetricPoint]:
    statement = (
        select(MetricPoint)
        .where(MetricPoint.service == service, MetricPoint.metric == metric)
        .order_by(MetricPoint.timestamp.desc())
        .limit(1)
    )
    return session.exec(statement).first()


def get_metrics_window(
    session: Session,
    service: str,
    metric: str,
    window_start: datetime,
    window_end: datetime,
    limit: int = 240,
    padding_minutes: int = 10,
) -> List[MetricPoint]:
    lower = window_start - timedelta(minutes=padding_minutes)
    upper = window_end + timedelta(minutes=padding_minutes)

    statement = (
        select(MetricPoint)
        .where(
            MetricPoint.service == service,
            MetricPoint.metric == metric,
            MetricPoint.timestamp >= lower,
            MetricPoint.timestamp <= upper,
        )
        .order_by(MetricPoint.timestamp)
        .limit(limit)
    )
    return session.exec(statement).all()


# ✅ Used by /api/v1/services/... to populate dropdowns / pages
def list_services(session: Session) -> List[str]:
    statement = select(MetricPoint.service).distinct()
    rows = session.exec(statement).all()

    # sqlmodel may return tuples depending on driver; normalize
    out: List[str] = []
    for row in rows:
        out.append(row[0] if isinstance(row, tuple) else row)
    return out


# ✅ Used by services endpoints and simulator logic
def list_service_metrics(session: Session, service: str) -> List[str]:
    statement = select(MetricPoint.metric).where(MetricPoint.service == service).distinct()
    rows = session.exec(statement).all()

    out: List[str] = []
    for row in rows:
        out.append(row[0] if isinstance(row, tuple) else row)
    return out


# Backward-compat alias (if older code calls this name)
def get_metrics_for_service(session: Session, service: str) -> List[str]:
    return list_service_metrics(session, service)

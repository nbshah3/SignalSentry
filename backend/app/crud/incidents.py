from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Sequence, Tuple

from sqlmodel import Session, select

from app.models import Incident, MetricPoint
from app.services.anomaly import AnomalyAssessment

TrackedMetric = Tuple[str, str]


def upsert_incident(
    session: Session,
    incident_key: str,
    service: str,
    metric: str,
    assessment: AnomalyAssessment,
) -> Incident:
    statement = select(Incident).where(Incident.incident_key == incident_key, Incident.status == "open")
    incident = session.exec(statement).first()

    if incident:
        incident.severity = assessment.severity
        incident.window_start = assessment.window_start
        incident.window_end = assessment.window_end
        incident.baseline = assessment.baseline
        incident.observed = assessment.observed
        incident.summary = assessment.summary
        incident.detector = assessment.detector
        incident.updated_at = datetime.utcnow()
    else:
        incident = Incident(
            incident_key=incident_key,
            service=service,
            metric=metric,
            severity=assessment.severity,
            window_start=assessment.window_start,
            window_end=assessment.window_end,
            baseline=assessment.baseline,
            observed=assessment.observed,
            detector=assessment.detector,
            summary=assessment.summary,
        )
        session.add(incident)

    session.commit()
    session.refresh(incident)
    return incident


def list_tracked_metrics(session: Session) -> List[TrackedMetric]:
    statement = select(Incident.service, Incident.metric).distinct()
    rows = session.exec(statement).all()
    return [(row[0], row[1]) for row in rows]


def list_recent_incidents(session: Session, limit: int = 20) -> List[Incident]:
    statement = select(Incident).order_by(Incident.detected_at.desc()).limit(limit)
    return session.exec(statement).all()


def list_active_incidents(session: Session, limit: int = 20) -> List[Incident]:
    statement = (
        select(Incident)
        .where(Incident.status == "open")
        .order_by(Incident.severity.desc(), Incident.detected_at.desc())
        .limit(limit)
    )
    return session.exec(statement).all()


def resolve_incident(session: Session, incident_id: int) -> Incident | None:
    incident = session.get(Incident, incident_id)
    if not incident:
        return None
    incident.status = "resolved"
    incident.updated_at = datetime.utcnow()
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


def list_service_metrics(session: Session, metrics: Sequence[str]) -> List[TrackedMetric]:
    statement = select(MetricPoint.service, MetricPoint.metric).distinct()
    rows = session.exec(statement).all()
    tracked: List[TrackedMetric] = []
    seen: set[TrackedMetric] = set()
    for service, metric in rows:
        pair = (service, metric)
        if metric in metrics and pair not in seen:
            tracked.append(pair)
            seen.add(pair)
    return tracked

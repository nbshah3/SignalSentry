import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.config import settings
from app.crud import incidents as incident_crud
from app.crud import logs as log_crud
from app.crud import metrics as metric_crud
from app.db.session import get_session
from app.models import Incident, LogEntry, MetricPoint
from app.schemas import LogCreate, MetricPointCreate
from app.schemas.incidents import (
    IncidentListResponse,
    IncidentRead,
    IncidentRefreshResponse,
    IncidentTimelineResponse,
)
from app.schemas.postmortem import PostmortemResponse
from app.schemas.root_cause import RootCauseResponse
from app.seed import seed_sample_data
from app.services.event_bus import event_bus
from app.services.incident_detector import IncidentDetector
from app.services.postmortem import PostmortemGenerator
from app.services.root_cause import RootCauseAnalyzer
from app.services.simulator import SimulationPlan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/active", response_model=IncidentListResponse)
def list_active_incidents(
    session: Session = Depends(get_session),
) -> IncidentListResponse:
    incidents = incident_crud.list_active_incidents(session)
    return IncidentListResponse(
        items=[IncidentRead.model_validate(incident) for incident in incidents]
    )


@router.get("/recent", response_model=IncidentListResponse)
def list_recent_incidents(
    session: Session = Depends(get_session),
) -> IncidentListResponse:
    incidents = incident_crud.list_recent_incidents(session)
    return IncidentListResponse(
        items=[IncidentRead.model_validate(incident) for incident in incidents]
    )


@router.post("/refresh", response_model=IncidentRefreshResponse)
async def refresh_incidents(
    session: Session = Depends(get_session),
) -> IncidentRefreshResponse:
    detector = IncidentDetector(session)
    try:
        pairs = detector.candidate_pairs()
        if not pairs:
            return IncidentRefreshResponse(
                status="ok", incidents_created=0, reason="no metrics available"
            )

        incidents = detector.evaluate_metrics(pairs)
        if not incidents:
            return IncidentRefreshResponse(
                status="ok", incidents_created=0, reason="no anomalies detected"
            )

        for incident in incidents:
            await _broadcast_incident(incident)
        return IncidentRefreshResponse(status="ok", incidents_created=len(incidents))
    except Exception as exc:  # pragma: no cover - defensive path
        logger.exception("incident refresh failed")
        return IncidentRefreshResponse(status="error", incidents_created=0, reason=str(exc))


@router.post("/{incident_id}/resolve", response_model=IncidentRead)
def resolve_incident(incident_id: int, session: Session = Depends(get_session)) -> IncidentRead:
    incident = incident_crud.resolve_incident(session, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentRead.model_validate(incident)


@router.get("/{incident_id}", response_model=IncidentRead)
def retrieve_incident(incident_id: int, session: Session = Depends(get_session)) -> IncidentRead:
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentRead.model_validate(incident)


@router.get("/{incident_id}/analysis", response_model=RootCauseResponse)
def analyze_incident(
    incident_id: int, session: Session = Depends(get_session)
) -> RootCauseResponse:
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    analyzer = RootCauseAnalyzer(session)
    return analyzer.analyze(incident)


@router.get("/{incident_id}/timeline", response_model=IncidentTimelineResponse)
def incident_timeline(
    incident_id: int, session: Session = Depends(get_session)
) -> IncidentTimelineResponse:
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    series = metric_crud.get_metrics_window(
        session=session,
        service=incident.service,
        metric=incident.metric,
        window_start=incident.window_start,
        window_end=incident.window_end,
        limit=240,
    )
    points = [{"timestamp": point.timestamp.isoformat(), "value": point.value} for point in series]
    return IncidentTimelineResponse(
        incident_id=incident.id,
        metric=incident.metric,
        points=points,
        baseline=incident.baseline,
        observed=incident.observed,
    )


@router.post("/simulate")
async def simulate_incident(
    session: Session = Depends(get_session),
) -> dict[str, object]:
    try:
        if not metric_crud.list_services(session):
            seed_sample_data(session)

        metrics, logs, plan = _inject_payments_spike(session)
        detector = IncidentDetector(session)
        before_ids = {incident.id for incident in incident_crud.list_active_incidents(session)}
        incidents = detector.evaluate_all_services()
        after_ids = {incident.id for incident in incident_crud.list_active_incidents(session)}
        created_ids = after_ids - before_ids

        for entry in metrics[-10:]:
            await _publish_metric_entry(entry)

        for incident in incidents:
            if incident.id in created_ids:
                await _broadcast_incident(incident)

        return {
            "ok": True,
            "service": plan.service,
            "metrics_appended": len(metrics),
            "logs_appended": len(logs),
            "created_incidents": len(created_ids),
        }
    except Exception as exc:  # pragma: no cover
        logger.exception("simulation failed")
        raise HTTPException(status_code=500, detail={"ok": False, "reason": str(exc)}) from exc


@router.post("/{incident_id}/postmortem", response_model=PostmortemResponse)
def create_postmortem(
    incident_id: int, session: Session = Depends(get_session)
) -> PostmortemResponse:
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    analyzer = RootCauseAnalyzer(session)
    analysis = analyzer.analyze(incident)
    generator = PostmortemGenerator(settings.postmortem_export_dir)
    artifacts = generator.generate(incident, analysis)
    return artifacts.to_response()


async def _broadcast_incident(incident: Incident) -> None:
    payload = {
        "incident_id": incident.id,
        "service": incident.service,
        "metric": incident.metric,
        "severity": incident.severity,
        "summary": incident.summary,
    }
    await event_bus.publish({"type": "incident_created", **payload})
    await event_bus.publish({"type": "incident_alert", **payload})


async def _publish_metric_entry(entry: MetricPoint) -> None:
    event = {
        "service": entry.service,
        "metric": entry.metric,
        "timestamp": entry.timestamp.isoformat(),
        "value": entry.value,
    }
    await event_bus.publish({"type": "metric_appended", **event})
    await event_bus.publish({"type": "metric_update", **event})


def _inject_payments_spike(
    session: Session, minutes: int = 5
) -> tuple[list[MetricPoint], list[LogEntry], SimulationPlan]:
    now = datetime.utcnow()
    metric_points = []
    for idx in range(minutes):
        timestamp = now - timedelta(minutes=minutes - idx)
        latency = 220 + idx * 25
        error_rate = 0.03 + idx * 0.015
        metric_points.extend(
            [
                MetricPointCreate(
                    service="payments",
                    metric="latency_p95_ms",
                    timestamp=timestamp,
                    value=latency,
                ),
                MetricPointCreate(
                    service="payments",
                    metric="error_rate",
                    timestamp=timestamp,
                    value=error_rate,
                ),
            ]
        )
    metrics = metric_crud.bulk_create_metrics(session, metric_points)

    log_payloads = []
    for idx in range(4):
        log_payloads.append(
            LogCreate(
                service="payments",
                timestamp=now - timedelta(minutes=idx),
                level="ERROR",
                request_id=f"simulate-payments-{idx}",
                message="payments latency spike detected",
                latency_ms=350 + idx * 15,
                context={"simulate": True, "step": idx},
            )
        )
    logs = log_crud.bulk_create_logs(session, log_payloads)

    plan = SimulationPlan(key="payments-spike", service="payments", metric="latency_p95_ms")
    return metrics, logs, plan

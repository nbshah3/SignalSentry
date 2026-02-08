import logging
from statistics import fmean

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.config import settings
from app.crud import incidents as incident_crud
from app.crud import metrics as metric_crud
from app.db.session import get_session
from app.models import Incident, MetricPoint
from app.schemas.incidents import (
    IncidentListResponse,
    IncidentRead,
    IncidentRefreshResponse,
    IncidentTimelineResponse,
)
from app.schemas.postmortem import PostmortemResponse
from app.schemas.root_cause import RootCauseResponse
from app.services.anomaly import AnomalyAssessment
from app.services.event_bus import event_bus
from app.services.incident_detector import IncidentDetector
from app.services.postmortem import PostmortemGenerator
from app.services.root_cause import RootCauseAnalyzer
from app.services.simulator import IncidentSimulator, SimulationPlan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/active", response_model=IncidentListResponse)
def list_active_incidents(session: Session = Depends(get_session)) -> IncidentListResponse:
    incidents = incident_crud.list_active_incidents(session)
    return IncidentListResponse(
        items=[IncidentRead.model_validate(incident) for incident in incidents]
    )


@router.get("/recent", response_model=IncidentListResponse)
def list_recent_incidents(session: Session = Depends(get_session)) -> IncidentListResponse:
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
async def simulate_incident(session: Session = Depends(get_session)) -> dict[str, object]:
    try:
        simulator = IncidentSimulator(session)
        metrics, logs, plan = simulator.run()
        detector = IncidentDetector(session)
        incident = detector.evaluate_metric(plan.service, plan.metric)

        if not incident:
            incident = _create_simulated_incident(session, plan)

        for entry in metrics[-10:]:
            await _publish_metric_entry(entry)

        incident_id = incident.id if incident else None
        if incident:
            await _broadcast_incident(incident)

        return {
            "ok": True,
            "incident_id": incident_id,
            "metrics_appended": len(metrics),
            "logs_appended": len(logs),
        }
    except Exception as exc:  # pragma: no cover
        logger.exception("simulation failed")
        return {"ok": False, "reason": str(exc)}


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


def _create_simulated_incident(session: Session, plan: SimulationPlan) -> Incident | None:
    series = metric_crud.get_metric_series(session, plan.service, plan.metric, limit=80)
    if len(series) < 12:
        return None

    baseline_values = [point.value for point in series[:-10]]
    recent_values = [point.value for point in series[-10:]]
    if not baseline_values:
        return None

    baseline = fmean(baseline_values)
    observed = fmean(recent_values)
    severity = min(100, int(abs(observed - baseline) / (abs(baseline) + 1e-6) * 120))
    assessment = AnomalyAssessment(
        severity=severity,
        baseline=baseline,
        observed=observed,
        window_start=series[-10].timestamp,
        window_end=series[-1].timestamp,
        detector="simulation",
        summary=f"{plan.metric} deviated during simulation",
    )
    return incident_crud.upsert_incident(
        session=session,
        incident_key=f"simulate:{plan.service}:{plan.metric}",
        service=plan.service,
        metric=plan.metric,
        assessment=assessment,
    )

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.crud import metrics as metric_crud
from app.db.session import get_session
from app.schemas import MetricBatch, MetricIngestResult
from app.services.event_bus import event_bus
from app.services.incident_detector import IncidentDetector

router = APIRouter(prefix="/ingest", tags=["metrics"])


@router.post("/metrics", response_model=MetricIngestResult)
async def ingest_metrics(
    payload: MetricBatch,
    session: Session = Depends(get_session),
) -> MetricIngestResult:
    created = metric_crud.bulk_create_metrics(session, payload.metrics)
    triggered = 0
    if created:
        detector = IncidentDetector(session)
        unique_pairs = {(entry.service, entry.metric) for entry in created}
        incidents = detector.evaluate_metrics(unique_pairs)
        triggered = len(incidents)
        for entry in created[-10:]:
            await event_bus.publish(
                {
                    "type": "metric_update",
                    "service": entry.service,
                    "metric": entry.metric,
                    "timestamp": entry.timestamp.isoformat(),
                    "value": entry.value,
                }
            )
        for incident in incidents:
            await event_bus.publish(
                {
                    "type": "incident_alert",
                    "incident_id": incident.id,
                    "service": incident.service,
                    "metric": incident.metric,
                    "severity": incident.severity,
                    "summary": incident.summary,
                }
            )
    return MetricIngestResult(
        ingested=len(created),
        skipped=len(payload.metrics) - len(created),
        incidents_triggered=triggered,
    )

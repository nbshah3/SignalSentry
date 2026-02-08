from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.crud import metrics as metric_crud
from app.db.session import get_session
from app.schemas import MetricBatch, MetricIngestResult
from app.services.incident_detector import IncidentDetector

router = APIRouter(prefix="/ingest", tags=["metrics"])


@router.post("/metrics", response_model=MetricIngestResult)
def ingest_metrics(
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
    return MetricIngestResult(
        ingested=len(created),
        skipped=len(payload.metrics) - len(created),
        incidents_triggered=triggered,
    )

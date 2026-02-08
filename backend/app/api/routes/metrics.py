from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.crud import metrics as metric_crud
from app.db.session import get_session
from app.schemas import MetricBatch, MetricIngestResult

router = APIRouter(prefix="/ingest", tags=["metrics"])


@router.post("/metrics", response_model=MetricIngestResult)
def ingest_metrics(
    payload: MetricBatch,
    session: Session = Depends(get_session),
) -> MetricIngestResult:
    created = metric_crud.bulk_create_metrics(session, payload.metrics)
    return MetricIngestResult(ingested=len(created), skipped=len(payload.metrics) - len(created))

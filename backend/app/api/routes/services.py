import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.crud import logs as log_crud, metrics as metric_crud
from app.db.session import get_session
from app.models import LogEntry
from app.schemas import LogRead, ServiceLogsResponse, ServiceMetricsResponse, ServiceSummaryResponse
from app.services.service_summary import ServiceSummaryBuilder

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/summary", response_model=ServiceSummaryResponse)
def services_summary(session: Session = Depends(get_session)) -> ServiceSummaryResponse:
    summaries = ServiceSummaryBuilder(session).build()
    return ServiceSummaryResponse(services=summaries)


@router.get("/{service}/metrics", response_model=ServiceMetricsResponse)
def service_metrics(
    service: str,
    metric: str = Query(..., description="Metric key, e.g. latency_p95_ms"),
    limit: int = Query(120, ge=10, le=500),
    session: Session = Depends(get_session),
) -> ServiceMetricsResponse:
    series = metric_crud.get_metric_series(session, service=service, metric=metric, limit=limit)
    if not series:
        raise HTTPException(status_code=404, detail="Metric series not found")
    points = [{"timestamp": point.timestamp.isoformat(), "value": point.value} for point in series]
    return ServiceMetricsResponse(service=service, metric=metric, points=points)


@router.get("/{service}/logs", response_model=ServiceLogsResponse)
def service_logs(
    service: str,
    level: str | None = None,
    query: str | None = None,
    limit: int = Query(100, ge=10, le=500),
    session: Session = Depends(get_session),
) -> ServiceLogsResponse:
    logs = log_crud.list_recent_logs(session, service=service, level=level, query=query, limit=limit)
    items = [_serialize_log(entry) for entry in logs]
    return ServiceLogsResponse(service=service, items=items)


def _serialize_log(entry: LogEntry) -> LogRead:
    context = None
    if entry.context:
        try:
            context = json.loads(entry.context)
        except json.JSONDecodeError:
            context = {"raw": entry.context}
    return LogRead(
        id=entry.id,
        timestamp=entry.timestamp,
        service=entry.service,
        level=entry.level,
        request_id=entry.request_id,
        message=entry.message,
        latency_ms=entry.latency_ms,
        context=context,
    )

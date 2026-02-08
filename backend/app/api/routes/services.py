from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas import ServiceSummaryResponse
from app.services.service_summary import ServiceSummaryBuilder

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/summary", response_model=ServiceSummaryResponse)
def services_summary(session: Session = Depends(get_session)) -> ServiceSummaryResponse:
    summaries = ServiceSummaryBuilder(session).build()
    return ServiceSummaryResponse(services=summaries)

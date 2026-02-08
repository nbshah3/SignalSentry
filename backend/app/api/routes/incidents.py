from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.crud import incidents as incident_crud
from app.db.session import get_session
from app.schemas.incidents import IncidentListResponse, IncidentRead, IncidentRefreshResponse
from app.services.incident_detector import IncidentDetector

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/active", response_model=IncidentListResponse)
def list_active_incidents(session: Session = Depends(get_session)) -> IncidentListResponse:
    incidents = incident_crud.list_active_incidents(session)
    return IncidentListResponse(items=[IncidentRead.model_validate(incident) for incident in incidents])


@router.get("/recent", response_model=IncidentListResponse)
def list_recent_incidents(session: Session = Depends(get_session)) -> IncidentListResponse:
    incidents = incident_crud.list_recent_incidents(session)
    return IncidentListResponse(items=[IncidentRead.model_validate(incident) for incident in incidents])


@router.post("/refresh", response_model=IncidentRefreshResponse)
def refresh_incidents(session: Session = Depends(get_session)) -> IncidentRefreshResponse:
    detector = IncidentDetector(session)
    incidents = detector.evaluate_all_services()
    return IncidentRefreshResponse(count=len(incidents))


@router.post("/{incident_id}/resolve", response_model=IncidentRead)
def resolve_incident(incident_id: int, session: Session = Depends(get_session)) -> IncidentRead:
    incident = incident_crud.resolve_incident(session, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentRead.model_validate(incident)

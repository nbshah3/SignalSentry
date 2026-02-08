from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.config import settings
from app.crud import incidents as incident_crud
from app.db.session import get_session
from app.models import Incident
from app.schemas.incidents import IncidentListResponse, IncidentRead, IncidentRefreshResponse
from app.schemas.postmortem import PostmortemResponse
from app.schemas.root_cause import RootCauseResponse
from app.services.incident_detector import IncidentDetector
from app.services.postmortem import PostmortemGenerator
from app.services.root_cause import RootCauseAnalyzer

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


@router.get("/{incident_id}/analysis", response_model=RootCauseResponse)
def analyze_incident(incident_id: int, session: Session = Depends(get_session)) -> RootCauseResponse:
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    analyzer = RootCauseAnalyzer(session)
    return analyzer.analyze(incident)


@router.post("/{incident_id}/postmortem", response_model=PostmortemResponse)
def create_postmortem(incident_id: int, session: Session = Depends(get_session)) -> PostmortemResponse:
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    analyzer = RootCauseAnalyzer(session)
    analysis = analyzer.analyze(incident)
    generator = PostmortemGenerator(settings.postmortem_export_dir)
    artifacts = generator.generate(incident, analysis)
    return artifacts.to_response()

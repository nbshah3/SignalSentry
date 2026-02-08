from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class IncidentRead(BaseModel):
    id: int
    incident_key: str
    service: str
    metric: str
    severity: int
    detected_at: datetime
    window_start: datetime
    window_end: datetime
    baseline: Optional[float] = None
    observed: Optional[float] = None
    detector: str
    summary: Optional[str] = None
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    items: List[IncidentRead]


class IncidentRefreshResponse(BaseModel):
    count: int
    reason: Optional[str] = None


class TimelinePoint(BaseModel):
    timestamp: str
    value: float


class IncidentTimelineResponse(BaseModel):
    incident_id: int
    metric: str
    points: List[TimelinePoint]
    baseline: Optional[float] = None
    observed: Optional[float] = None

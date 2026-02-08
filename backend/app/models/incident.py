from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Incident(SQLModel, table=True):
    __tablename__ = "incidents"

    id: Optional[int] = Field(default=None, primary_key=True)
    incident_key: str = Field(index=True)
    service: str = Field(index=True)
    metric: str = Field(index=True)
    severity: int = Field(default=0)
    detected_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    window_start: datetime
    window_end: datetime
    baseline: Optional[float] = None
    observed: Optional[float] = None
    status: str = Field(default="open")

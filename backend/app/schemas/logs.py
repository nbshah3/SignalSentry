from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogBase(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    level: str = "INFO"
    request_id: Optional[str] = None
    message: str
    latency_ms: Optional[float] = None
    context: Optional[Dict[str, Any]] = None


class LogCreate(LogBase):
    pass


class LogBatch(BaseModel):
    logs: List[LogCreate]


class LogIngestResult(BaseModel):
    ingested: int
    skipped: int

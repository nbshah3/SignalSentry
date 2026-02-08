from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MetricPointBase(BaseModel):
    service: str
    metric: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float


class MetricPointCreate(MetricPointBase):
    pass


class MetricBatch(BaseModel):
    metrics: List[MetricPointCreate]


class MetricIngestResult(BaseModel):
    ingested: int
    skipped: int


class MetricQuery(BaseModel):
    service: str
    metric: str
    limit: Optional[int] = 200

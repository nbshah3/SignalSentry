from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class MetricPoint(SQLModel, table=True):
    __tablename__ = "metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    service: str = Field(index=True)
    metric: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    value: float

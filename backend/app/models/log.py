from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class LogEntry(SQLModel, table=True):
    __tablename__ = "logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    service: str = Field(index=True)
    level: str = Field(default="INFO", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    request_id: Optional[str] = Field(default=None, index=True)
    message: str
    latency_ms: Optional[float] = None
    context: Optional[str] = Field(default=None, sa_column=Column(Text))

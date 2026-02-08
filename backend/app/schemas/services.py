from typing import Dict, List, Optional

from pydantic import BaseModel


class SparklinePoint(BaseModel):
    timestamp: str
    value: float


class ServiceSummary(BaseModel):
    service: str
    latency_p95_ms: Optional[float] = None
    error_rate: Optional[float] = None
    cpu_pct: Optional[float] = None
    memory_rss_mb: Optional[float] = None
    sparklines: Dict[str, List[SparklinePoint]]


class ServiceSummaryResponse(BaseModel):
    services: List[ServiceSummary]

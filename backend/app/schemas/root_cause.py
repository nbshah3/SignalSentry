from typing import List, Literal

from pydantic import BaseModel


class Evidence(BaseModel):
    type: Literal["metric", "log"]
    detail: str


class Hypothesis(BaseModel):
    title: str
    confidence: int
    evidence: List[Evidence]


class RootCauseResponse(BaseModel):
    incident_id: int
    service: str
    metric: str
    hypotheses: List[Hypothesis]

from typing import Dict

from pydantic import BaseModel


class PostmortemResponse(BaseModel):
    incident_id: int
    summary: str
    json_path: str
    pdf_path: str
    downloads: Dict[str, str]

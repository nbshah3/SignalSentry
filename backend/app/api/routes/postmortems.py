from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(prefix="/postmortems", tags=["postmortem"])


@router.get("/{filename}")
def download_postmortem(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    target = Path(settings.postmortem_export_dir) / safe_name
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Postmortem not found")

    media_type = "application/pdf" if target.suffix.lower() == ".pdf" else "application/json"
    return FileResponse(target, media_type=media_type, filename=target.name)

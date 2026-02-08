import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.seed import seed_sample_data

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/seed")
def seed_endpoint(force: bool = False, session: Session = Depends(get_session)) -> dict[str, object]:
    try:
        result = seed_sample_data(session, force=force)
        return {"status": "ok", **result}
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("seed endpoint failed")
        return {"status": "error", "reason": str(exc)}

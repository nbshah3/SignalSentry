from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.seed import seed_sample_data

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed")
def seed_endpoint(force: bool = False, session: Session = Depends(get_session)) -> dict[str, object]:
    return seed_sample_data(session, force=force)

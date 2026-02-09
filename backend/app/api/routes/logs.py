from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.crud import logs as log_crud
from app.db.session import get_session
from app.schemas import LogBatch, LogIngestResult
from app.services.log_parser import parse_log_blob

router = APIRouter(prefix="/ingest", tags=["logs"])


@router.post("/logfile", response_model=LogIngestResult)
async def ingest_log_file(
    file: UploadFile,
    session: Session = Depends(get_session),
) -> LogIngestResult:
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover - guardrail
        raise HTTPException(
            status_code=400, detail="Invalid encoding in log file"
        ) from exc

    parsed_logs = parse_log_blob(text)
    created = log_crud.bulk_create_logs(session, parsed_logs)
    return LogIngestResult(
        ingested=len(created), skipped=len(text.splitlines()) - len(created)
    )


@router.post("/logs", response_model=LogIngestResult)
def ingest_log_batch(
    payload: LogBatch,
    session: Session = Depends(get_session),
) -> LogIngestResult:
    created = log_crud.bulk_create_logs(session, payload.logs)
    return LogIngestResult(
        ingested=len(created), skipped=len(payload.logs) - len(created)
    )

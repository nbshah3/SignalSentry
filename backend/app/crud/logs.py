import json
from datetime import datetime, timedelta
from typing import Iterable, List, Sequence

from sqlmodel import Session, select

from app.models import LogEntry
from app.schemas import LogCreate


def create_log(session: Session, log_in: LogCreate) -> LogEntry:
    entry = LogEntry(
        service=log_in.service,
        level=log_in.level.upper(),
        timestamp=log_in.timestamp,
        request_id=log_in.request_id,
        message=log_in.message,
        latency_ms=log_in.latency_ms,
        context=json.dumps(log_in.context) if log_in.context else None,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def bulk_create_logs(session: Session, logs: Iterable[LogCreate]) -> Sequence[LogEntry]:
    entries = [
        LogEntry(
            service=log.service,
            level=log.level.upper(),
            timestamp=log.timestamp,
            request_id=log.request_id,
            message=log.message,
            latency_ms=log.latency_ms,
            context=json.dumps(log.context) if log.context else None,
        )
        for log in logs
    ]

    if not entries:
        return []

    session.add_all(entries)
    session.commit()

    for entry in entries:
        session.refresh(entry)

    return entries


def get_logs_for_window(
    session: Session,
    service: str,
    window_start: datetime,
    window_end: datetime,
    limit: int = 200,
    padding_minutes: int = 5,
) -> List[LogEntry]:
    lower = window_start - timedelta(minutes=padding_minutes)
    upper = window_end + timedelta(minutes=padding_minutes)
    statement = (
        select(LogEntry)
        .where(
            LogEntry.service == service,
            LogEntry.timestamp >= lower,
            LogEntry.timestamp <= upper,
        )
        .order_by(LogEntry.timestamp)
        .limit(limit)
    )
    return session.exec(statement).all()

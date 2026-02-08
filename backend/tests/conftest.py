from datetime import datetime, timedelta
from typing import Iterator

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models import Incident, LogEntry, MetricPoint


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def baseline_metrics(session: Session) -> None:
    start = datetime.utcnow() - timedelta(minutes=60)
    for idx in range(40):
        session.add(
            MetricPoint(
                service="api-gateway",
                metric="latency_p95_ms",
                timestamp=start + timedelta(minutes=idx),
                value=120.0,
            )
        )
    session.commit()

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlmodel import select

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import init_db, session_scope
from app.models import LogEntry, MetricPoint
from app.seed import seed_sample_data

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:  # pragma: no cover
        logger.info("Using database %s", settings.database_url)
        init_db()
        with session_scope() as session:
            try:
                metric_count = session.exec(select(func.count(MetricPoint.id))).one()
                log_count = session.exec(select(func.count(LogEntry.id))).one()
                if metric_count == 0 and log_count == 0:
                    seed_sample_data(session)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("startup seeding failed", exc_info=exc)

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()

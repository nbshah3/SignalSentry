from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import init_db, session_scope
from app.seed import seed_sample_data


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
        init_db()
        if settings.environment in {"local", "development", "dev"}:
            with session_scope() as session:
                seed_sample_data(session)

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()

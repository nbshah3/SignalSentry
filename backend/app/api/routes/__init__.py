from fastapi import APIRouter

from . import health, incidents, logs, metrics, stream

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(logs.router)
api_router.include_router(metrics.router)
api_router.include_router(incidents.router)
api_router.include_router(stream.router)

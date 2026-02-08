from fastapi import APIRouter

from . import admin, health, incidents, logs, metrics, postmortems, services, stream

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(admin.router)
api_router.include_router(logs.router)
api_router.include_router(metrics.router)
api_router.include_router(incidents.router)
api_router.include_router(postmortems.router)
api_router.include_router(services.router)
api_router.include_router(stream.router)

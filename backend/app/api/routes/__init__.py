from fastapi import APIRouter

from . import health, logs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(logs.router)

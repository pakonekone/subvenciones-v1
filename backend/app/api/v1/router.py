"""
API v1 router aggregator
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()

# Include health endpoint
api_router.include_router(health.router, prefix="/health", tags=["health"])

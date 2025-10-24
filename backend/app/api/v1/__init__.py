from fastapi import APIRouter
from app.api.v1 import grants, capture, webhook, capture_boe, analytics, filters

api_router = APIRouter()

api_router.include_router(grants.router, prefix="/grants", tags=["grants"])
api_router.include_router(capture.router, prefix="/capture", tags=["capture"])
api_router.include_router(capture_boe.router, prefix="/capture", tags=["capture"])
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(filters.router, prefix="/filters", tags=["filters"])

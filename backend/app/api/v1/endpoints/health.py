"""
Health check endpoints
"""
from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "subvenciones-api",
        "version": settings.version
    }


@router.get("/n8n")
async def n8n_health():
    """N8n integration health check"""
    if not settings.n8n_webhook_url:
        return {
            "status": "not_configured",
            "n8n": "webhook_url_missing"
        }

    return {
        "status": "configured",
        "n8n": "webhook_url_set",
        "url": settings.n8n_webhook_url[:50] + "..."
    }

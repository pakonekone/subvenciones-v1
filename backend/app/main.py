"""
FastAPI main application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1 import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"🚀 Starting {settings.project_name} v{settings.version}")
    logger.info(f"📊 Database: {settings.database_url.split('@')[-1]}")
    logger.info(f"🔗 N8n: {'Configured' if settings.n8n_webhook_url else 'Not configured'}")

    yield

    # Shutdown
    logger.info("👋 Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="API REST para gestión de subvenciones BOE/BDNS con integración N8n",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.project_name}",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "version": settings.version,
        "database": "connected"
    }


@app.get("/debug/cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration"""
    return {
        "cors_origins": settings.cors_origins,
        "cors_origins_raw": settings.cors_origins_str,
        "count": len(settings.cors_origins)
    }


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    import os

    # Check if CORS_ORIGINS exists in environment
    cors_in_env = "CORS_ORIGINS" in os.environ
    cors_value = os.environ.get("CORS_ORIGINS", "NOT_FOUND")

    # List all environment variable names (not values for security)
    env_keys = sorted([k for k in os.environ.keys() if not k.startswith("_")])

    # Check specific vars we care about
    relevant_vars = {
        "DATABASE_URL": "EXISTS" if os.environ.get("DATABASE_URL") else "MISSING",
        "CORS_ORIGINS": cors_value if cors_in_env else "MISSING",
        "PORT": os.environ.get("PORT", "MISSING"),
        "N8N_WEBHOOK_URL": "EXISTS" if os.environ.get("N8N_WEBHOOK_URL") else "MISSING",
    }

    return {
        "cors_origins_in_env": cors_in_env,
        "cors_origins_value": cors_value,
        "relevant_vars": relevant_vars,
        "total_env_vars": len(env_keys),
        "env_var_names": env_keys[:20]  # First 20 to avoid huge response
    }

"""
Configuration management with Pydantic Settings
"""
import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = "postgresql://franconejosmengo@localhost:5432/subvenciones"
    db_echo: bool = False

    # N8n Integration
    n8n_webhook_url: str = ""
    n8n_chat_webhook_url: str = ""
    n8n_api_key: str = ""

    # BOE/BDNS Configuration
    min_relevance_score: float = 0.3
    bdns_max_results: int = 50
    process_pdfs: bool = True
    placsp_feed_url: str = "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"

    # Server
    api_host: str = "0.0.0.0"
    debug: bool = False

    @property
    def api_port(self) -> int:
        """Get API port from PORT env var (Render) or default to 8000 (local dev)"""
        return int(os.getenv("PORT", "8000"))

    # CORS - stored as string in .env, converted to list
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        validation_alias="CORS_ORIGINS"
    )

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins_str.split(',') if origin.strip()]

    # Logging
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Subvenciones API"
    version: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance (for dependency injection)"""
    return settings

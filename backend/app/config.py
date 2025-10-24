"""
Configuration management with Pydantic Settings
"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5433/subvenciones"
    db_echo: bool = False

    # N8n Integration
    n8n_webhook_url: str = ""
    n8n_api_key: str = ""

    # BOE/BDNS Configuration
    min_relevance_score: float = 0.3
    bdns_max_results: int = 50
    process_pdfs: bool = True

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # CORS - stored as string in .env, converted to list
    _cors_origins_str: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self._cors_origins_str.split(',') if origin.strip()]

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
        extra="ignore",
        # Map CORS_ORIGINS env var to _cors_origins_str field
        alias_generator=lambda field_name: "CORS_ORIGINS" if field_name == "_cors_origins_str" else field_name.upper()
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance (for dependency injection)"""
    return settings

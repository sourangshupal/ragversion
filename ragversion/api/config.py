"""API configuration."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APIConfig(BaseSettings):
    """FastAPI server configuration."""

    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=6699, description="Port to bind to")
    reload: bool = Field(default=False, description="Enable auto-reload")
    workers: int = Field(default=1, description="Number of worker processes")

    # CORS
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins"
    )

    # Authentication (optional)
    auth_enabled: bool = Field(default=False, description="Enable API key authentication")
    api_keys: list[str] = Field(
        default_factory=list,
        description="Valid API keys"
    )

    # API metadata
    title: str = Field(default="RAGVersion API", description="API title")
    description: str = Field(
        default="REST API for RAGVersion document tracking system",
        description="API description"
    )
    version: str = Field(default="0.7.0", description="API version")

    # Rate limiting (optional)
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Max requests per minute")

    model_config = SettingsConfigDict(
        env_prefix="RAGVERSION_API_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

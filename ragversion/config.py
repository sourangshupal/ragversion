"""Configuration management for RAGVersion."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SupabaseConfig(BaseSettings):
    """Supabase storage configuration."""

    url: str = Field(..., description="Supabase project URL")
    service_key: str = Field(..., description="Supabase service key")
    connection_pool_size: int = Field(default=10, description="Connection pool size")
    timeout_seconds: int = Field(default=30, description="Request timeout")

    model_config = SettingsConfigDict(
        env_prefix="SUPABASE_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def key(self) -> str:
        """Alias for service_key for backwards compatibility."""
        return self.service_key


class BatchConfig(BaseSettings):
    """Batch processing configuration."""

    max_workers: int = Field(default=4, description="Number of parallel workers")
    chunk_size: int = Field(default=100, description="Files per chunk")
    on_error: str = Field(default="continue", description="Error handling: continue|stop")

    model_config = SettingsConfigDict(env_prefix="RAGVERSION_BATCH_")


class ContentConfig(BaseSettings):
    """Content storage configuration."""

    compression: str = Field(default="gzip", description="Compression: gzip|none")
    ttl_days: Optional[int] = Field(default=365, description="Content TTL in days")

    model_config = SettingsConfigDict(env_prefix="RAGVERSION_CONTENT_")


class TrackingConfig(BaseSettings):
    """Document tracking configuration."""

    store_content: bool = Field(default=True, description="Store full content")
    max_file_size_mb: int = Field(default=50, description="Max file size in MB")
    hash_algorithm: str = Field(default="sha256", description="Hash algorithm")

    model_config = SettingsConfigDict(env_prefix="RAGVERSION_TRACKING_")


class AsyncConfig(BaseSettings):
    """Async configuration."""

    enabled: bool = Field(default=True, description="Enable async")
    callback_timeout: int = Field(default=60, description="Callback timeout in seconds")
    callback_mode: str = Field(default="sequential", description="Callback mode: sequential|parallel")

    model_config = SettingsConfigDict(env_prefix="RAGVERSION_ASYNC_")


class ErrorHandlingConfig(BaseSettings):
    """Error handling configuration."""

    continue_on_parse_error: bool = Field(default=True, description="Continue on parse errors")
    max_retries: int = Field(default=3, description="Max retry attempts")
    retry_backoff: str = Field(default="exponential", description="Retry backoff: exponential|linear")
    log_errors: bool = Field(default=True, description="Log errors")

    model_config = SettingsConfigDict(env_prefix="RAGVERSION_ERROR_")


class RAGVersionConfig(BaseSettings):
    """Main RAGVersion configuration."""

    # Storage backend
    storage_backend: str = Field(default="supabase", description="Storage backend: supabase")
    supabase: Optional[SupabaseConfig] = None

    # Tracking
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)

    # Batch processing
    batch: BatchConfig = Field(default_factory=BatchConfig)

    # Content storage
    content: ContentConfig = Field(default_factory=ContentConfig)

    # Async
    async_config: AsyncConfig = Field(default_factory=AsyncConfig, alias="async")

    # Error handling
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def from_yaml(cls, file_path: str) -> "RAGVersionConfig":
        """
        Load configuration from YAML file.

        Args:
            file_path: Path to YAML config file

        Returns:
            RAGVersionConfig instance
        """
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        # Handle nested configs
        if "storage" in data and "supabase" in data["storage"]:
            # Merge SUPABASE env vars with YAML
            supabase_data = data["storage"]["supabase"]
            supabase_data.setdefault("url", os.getenv("SUPABASE_URL", ""))
            supabase_data.setdefault("key", os.getenv("SUPABASE_SERVICE_KEY", ""))
            data["supabase"] = supabase_data

        if "tracking" in data:
            data["tracking"] = TrackingConfig(**data["tracking"])

        if "batch" in data.get("tracking", {}):
            data["batch"] = BatchConfig(**data["tracking"]["batch"])

        if "content" in data.get("tracking", {}):
            data["content"] = ContentConfig(**data["tracking"]["content"])

        if "async" in data:
            data["async_config"] = AsyncConfig(**data["async"])

        if "error_handling" in data:
            data["error_handling"] = ErrorHandlingConfig(**data["error_handling"])

        return cls(**data)

    @classmethod
    def from_env(cls) -> "RAGVersionConfig":
        """
        Load configuration from environment variables.

        Returns:
            RAGVersionConfig instance
        """
        # Load SUPABASE config from env
        try:
            # Let SupabaseConfig load from environment automatically
            supabase = SupabaseConfig()
        except Exception:
            supabase = None

        return cls(
            storage_backend="supabase",
            supabase=supabase,
            tracking=TrackingConfig(),
            batch=BatchConfig(),
            content=ContentConfig(),
            async_config=AsyncConfig(),
            error_handling=ErrorHandlingConfig(),
        )

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "RAGVersionConfig":
        """
        Load configuration from file or environment.

        Args:
            config_path: Optional path to config file

        Returns:
            RAGVersionConfig instance
        """
        if config_path and Path(config_path).exists():
            return cls.from_yaml(config_path)

        # Try default locations
        default_paths = [
            "ragversion.yaml",
            "ragversion.yml",
            ".ragversion.yaml",
            ".ragversion.yml",
        ]

        for path in default_paths:
            if Path(path).exists():
                return cls.from_yaml(path)

        # Fall back to environment variables
        return cls.from_env()

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump(exclude_none=True)

    def save_yaml(self, file_path: str) -> None:
        """
        Save configuration to YAML file.

        Args:
            file_path: Path to save config
        """
        data = self.to_dict()

        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

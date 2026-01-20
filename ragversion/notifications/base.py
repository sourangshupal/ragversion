"""Base notification interface and configuration."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from ragversion.models import ChangeEvent


class NotificationConfig(BaseModel):
    """Configuration for a notification provider."""

    enabled: bool = Field(default=True, description="Enable this notifier")
    name: str = Field(..., description="Notifier name for logging")
    timeout_seconds: int = Field(default=10, description="Request timeout")

    class Config:
        extra = "allow"  # Allow provider-specific config


class BaseNotifier(ABC):
    """Base class for all notification providers."""

    def __init__(self, config: NotificationConfig) -> None:
        """Initialize notifier with configuration.

        Args:
            config: Notification configuration
        """
        self.config = config
        self.enabled = config.enabled

    @abstractmethod
    async def send(self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send notification for a document change.

        Args:
            change: The change event to notify about
            metadata: Optional additional metadata

        Returns:
            True if notification sent successfully, False otherwise
        """
        pass

    def format_change_message(self, change: ChangeEvent) -> str:
        """Format a change event into a human-readable message.

        Args:
            change: The change event

        Returns:
            Formatted message string
        """
        icon = {
            "created": "✨",
            "modified": "📝",
            "deleted": "🗑️",
            "restored": "♻️",
        }.get(change.change_type.value, "📄")

        return (
            f"{icon} Document {change.change_type.value.upper()}: {change.file_name}\n"
            f"Path: {change.file_path}\n"
            f"Version: {change.version_number}\n"
            f"Hash: {change.content_hash[:16]}...\n"
            f"Size: {self._format_size(change.file_size)}\n"
            f"Time: {change.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.config.name}, enabled={self.enabled})"

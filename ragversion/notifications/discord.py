"""Discord notification provider."""

import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import Field

from ragversion.models import ChangeEvent
from ragversion.notifications.base import BaseNotifier, NotificationConfig

logger = logging.getLogger(__name__)


class DiscordConfig(NotificationConfig):
    """Discord notification configuration."""

    webhook_url: str = Field(..., description="Discord webhook URL")
    username: str = Field(default="RAGVersion", description="Bot username")
    avatar_url: Optional[str] = Field(None, description="Bot avatar URL")
    mention_users: list[str] = Field(
        default_factory=list, description="User IDs to mention (e.g., ['123456789'])"
    )
    mention_roles: list[str] = Field(
        default_factory=list, description="Role IDs to mention (e.g., ['987654321'])"
    )
    mention_on_types: list[str] = Field(
        default_factory=lambda: ["deleted"],
        description="Change types that trigger mentions",
    )


class DiscordNotifier(BaseNotifier):
    """Send notifications to Discord via webhooks."""

    def __init__(self, config: DiscordConfig) -> None:
        """Initialize Discord notifier.

        Args:
            config: Discord configuration
        """
        super().__init__(config)
        self.config: DiscordConfig = config

    async def send(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send Discord notification.

        Args:
            change: The change event
            metadata: Optional additional metadata

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug(f"Discord notifier '{self.config.name}' is disabled")
            return False

        try:
            # Build message
            message = self._build_message(change, metadata)

            # Send via webhook
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    self.config.webhook_url,
                    json=message,
                    params={"wait": "true"},  # Wait for confirmation
                )
                response.raise_for_status()

            logger.info(f"Sent Discord notification for {change.file_name}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Discord notification: {e}")
            return False

    def _build_message(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build Discord message payload.

        Args:
            change: The change event
            metadata: Optional metadata

        Returns:
            Discord message payload
        """
        # Icon emoji for change type
        icon = {
            "created": "✨",
            "modified": "📝",
            "deleted": "🗑️",
            "restored": "♻️",
        }.get(change.change_type.value, "📄")

        # Color for embed (decimal format)
        color = {
            "created": 3066993,  # Green
            "modified": 16750899,  # Orange
            "deleted": 16711680,  # Red
            "restored": 2196219,  # Blue
        }.get(change.change_type.value, 13421772)

        # Build embed fields
        fields = [
            {"name": "File", "value": f"`{change.file_name}`", "inline": True},
            {"name": "Version", "value": str(change.version_number), "inline": True},
            {"name": "Size", "value": self._format_size(change.file_size), "inline": True},
            {"name": "Path", "value": f"`{change.file_path}`", "inline": False},
            {"name": "Hash", "value": f"`{change.content_hash[:16]}...`", "inline": False},
        ]

        # Add metadata if provided
        if metadata:
            for key, value in metadata.items():
                fields.append({"name": key.title(), "value": str(value), "inline": True})

        # Build embed
        embed = {
            "title": f"{icon} Document {change.change_type.value.title()}",
            "color": color,
            "fields": fields,
            "timestamp": change.timestamp.isoformat(),
            "footer": {"text": "RAGVersion"},
        }

        # Build message
        message: Dict[str, Any] = {
            "username": self.config.username,
            "embeds": [embed],
        }

        # Add avatar if specified
        if self.config.avatar_url:
            message["avatar_url"] = self.config.avatar_url

        # Add mentions if configured
        if change.change_type.value in self.config.mention_on_types:
            mentions = []

            # Add user mentions
            for user_id in self.config.mention_users:
                mentions.append(f"<@{user_id}>")

            # Add role mentions
            for role_id in self.config.mention_roles:
                mentions.append(f"<@&{role_id}>")

            if mentions:
                message["content"] = " ".join(mentions) + " Document change requires attention"

        return message

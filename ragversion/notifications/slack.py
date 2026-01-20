"""Slack notification provider."""

import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import Field

from ragversion.models import ChangeEvent
from ragversion.notifications.base import BaseNotifier, NotificationConfig

logger = logging.getLogger(__name__)


class SlackConfig(NotificationConfig):
    """Slack notification configuration."""

    webhook_url: str = Field(..., description="Slack webhook URL")
    channel: Optional[str] = Field(None, description="Override channel (e.g., #docs)")
    username: str = Field(default="RAGVersion", description="Bot username")
    icon_emoji: str = Field(default=":page_facing_up:", description="Bot icon emoji")
    mention_users: list[str] = Field(
        default_factory=list, description="Users to mention (e.g., ['@john', '@jane'])"
    )
    mention_on_types: list[str] = Field(
        default_factory=lambda: ["deleted"],
        description="Change types that trigger mentions",
    )


class SlackNotifier(BaseNotifier):
    """Send notifications to Slack via webhooks."""

    def __init__(self, config: SlackConfig) -> None:
        """Initialize Slack notifier.

        Args:
            config: Slack configuration
        """
        super().__init__(config)
        self.config: SlackConfig = config

    async def send(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send Slack notification.

        Args:
            change: The change event
            metadata: Optional additional metadata

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug(f"Slack notifier '{self.config.name}' is disabled")
            return False

        try:
            # Build message
            message = self._build_message(change, metadata)

            # Send via webhook
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(self.config.webhook_url, json=message)
                response.raise_for_status()

            logger.info(f"Sent Slack notification for {change.file_name}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack notification: {e}")
            return False

    def _build_message(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build Slack message payload.

        Args:
            change: The change event
            metadata: Optional metadata

        Returns:
            Slack message payload
        """
        # Icon for change type
        icon = {
            "created": ":sparkles:",
            "modified": ":pencil2:",
            "deleted": ":wastebasket:",
            "restored": ":recycle:",
        }.get(change.change_type.value, ":page_facing_up:")

        # Color for attachment
        color = {
            "created": "#36a64f",  # Green
            "modified": "#ff9900",  # Orange
            "deleted": "#ff0000",  # Red
            "restored": "#2196F3",  # Blue
        }.get(change.change_type.value, "#cccccc")

        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icon} Document {change.change_type.value.title()}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*File:*\n`{change.file_name}`"},
                    {"type": "mrkdwn", "text": f"*Version:*\n{change.version_number}"},
                    {"type": "mrkdwn", "text": f"*Size:*\n{self._format_size(change.file_size)}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Hash:*\n`{change.content_hash[:16]}...`",
                    },
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Path:*\n`{change.file_path}`"},
            },
        ]

        # Add metadata if provided
        if metadata:
            metadata_text = "\n".join(
                [f"*{k.title()}:* {v}" for k, v in metadata.items()]
            )
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": metadata_text}}
            )

        # Add context
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ {change.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    }
                ],
            }
        )

        # Build message payload
        message: Dict[str, Any] = {
            "username": self.config.username,
            "icon_emoji": self.config.icon_emoji,
            "blocks": blocks,
            "attachments": [{"color": color, "fallback": self.format_change_message(change)}],
        }

        # Override channel if specified
        if self.config.channel:
            message["channel"] = self.config.channel

        # Add mentions if configured
        if (
            change.change_type.value in self.config.mention_on_types
            and self.config.mention_users
        ):
            mentions = " ".join(self.config.mention_users)
            message["text"] = f"{mentions} Document change requires attention"

        return message

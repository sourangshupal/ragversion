"""Generic webhook notification provider."""

import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import Field

from ragversion.models import ChangeEvent
from ragversion.notifications.base import BaseNotifier, NotificationConfig

logger = logging.getLogger(__name__)


class WebhookConfig(NotificationConfig):
    """Webhook notification configuration."""

    url: str = Field(..., description="Webhook URL")
    method: str = Field(default="POST", description="HTTP method (POST, PUT, PATCH)")
    headers: Dict[str, str] = Field(
        default_factory=dict, description="Custom HTTP headers"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata in payload"
    )


class WebhookNotifier(BaseNotifier):
    """Send notifications to generic webhooks."""

    def __init__(self, config: WebhookConfig) -> None:
        """Initialize webhook notifier.

        Args:
            config: Webhook configuration
        """
        super().__init__(config)
        self.config: WebhookConfig = config

    async def send(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send webhook notification.

        Args:
            change: The change event
            metadata: Optional additional metadata

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug(f"Webhook notifier '{self.config.name}' is disabled")
            return False

        try:
            # Build payload
            payload = self._build_payload(change, metadata)

            # Send request
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.request(
                    method=self.config.method,
                    url=self.config.url,
                    json=payload,
                    headers=self.config.headers,
                )
                response.raise_for_status()

            logger.info(f"Sent webhook notification for {change.file_name}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending webhook notification: {e}")
            return False

    def _build_payload(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build webhook payload.

        Args:
            change: The change event
            metadata: Optional metadata

        Returns:
            Webhook payload
        """
        # Basic payload with change event data
        payload = {
            "event": "document_change",
            "change_type": change.change_type.value,
            "document": {
                "id": str(change.document_id),
                "file_name": change.file_name,
                "file_path": change.file_path,
                "file_size": change.file_size,
                "content_hash": change.content_hash,
            },
            "version": {
                "id": str(change.version_id),
                "number": change.version_number,
                "previous_hash": change.previous_hash,
            },
            "timestamp": change.timestamp.isoformat(),
        }

        # Add metadata if configured and provided
        if self.config.include_metadata and metadata:
            payload["metadata"] = metadata

        return payload

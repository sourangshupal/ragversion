"""Notification system for document change alerts."""

import logging
from typing import Any, Dict, List, Optional

from ragversion.notifications.base import BaseNotifier, NotificationConfig
from ragversion.notifications.discord import DiscordConfig, DiscordNotifier
from ragversion.notifications.email import EmailConfig, EmailNotifier
from ragversion.notifications.manager import NotificationManager
from ragversion.notifications.slack import SlackConfig, SlackNotifier
from ragversion.notifications.webhook import WebhookConfig, WebhookNotifier

logger = logging.getLogger(__name__)

__all__ = [
    "BaseNotifier",
    "NotificationConfig",
    "SlackNotifier",
    "DiscordNotifier",
    "EmailNotifier",
    "WebhookNotifier",
    "NotificationManager",
    "create_notification_manager",
]


def create_notification_manager(
    notifiers_config: List[Dict[str, Any]]
) -> Optional[NotificationManager]:
    """
    Create a NotificationManager from configuration.

    Args:
        notifiers_config: List of notifier configurations

    Returns:
        NotificationManager instance or None if no notifiers configured
    """
    if not notifiers_config:
        return None

    notifiers: List[BaseNotifier] = []

    for config_dict in notifiers_config:
        notifier_type = config_dict.get("type", "").lower()

        try:
            if notifier_type == "slack":
                config = SlackConfig(**config_dict)
                notifiers.append(SlackNotifier(config))
            elif notifier_type == "discord":
                config = DiscordConfig(**config_dict)
                notifiers.append(DiscordNotifier(config))
            elif notifier_type == "email":
                config = EmailConfig(**config_dict)
                notifiers.append(EmailNotifier(config))
            elif notifier_type == "webhook":
                config = WebhookConfig(**config_dict)
                notifiers.append(WebhookNotifier(config))
            else:
                logger.warning(f"Unknown notifier type: {notifier_type}")
                continue
        except Exception as e:
            logger.error(f"Failed to create notifier {config_dict.get('name', 'unknown')}: {e}")
            continue

    if not notifiers:
        return None

    return NotificationManager(notifiers)

"""Notification manager for handling multiple notifiers."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from ragversion.models import ChangeEvent
from ragversion.notifications.base import BaseNotifier

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manage multiple notification providers."""

    def __init__(self, notifiers: Optional[List[BaseNotifier]] = None) -> None:
        """Initialize notification manager.

        Args:
            notifiers: List of notifier instances
        """
        self.notifiers = notifiers or []

    def add_notifier(self, notifier: BaseNotifier) -> None:
        """Add a notifier to the manager.

        Args:
            notifier: Notifier instance to add
        """
        self.notifiers.append(notifier)
        logger.info(f"Added notifier: {notifier}")

    def remove_notifier(self, notifier: BaseNotifier) -> None:
        """Remove a notifier from the manager.

        Args:
            notifier: Notifier instance to remove
        """
        if notifier in self.notifiers:
            self.notifiers.remove(notifier)
            logger.info(f"Removed notifier: {notifier}")

    async def notify(
        self,
        change: ChangeEvent,
        metadata: Optional[Dict[str, Any]] = None,
        parallel: bool = True,
    ) -> Dict[str, bool]:
        """Send notifications to all enabled notifiers.

        Args:
            change: The change event to notify about
            metadata: Optional additional metadata
            parallel: Send notifications in parallel (default: True)

        Returns:
            Dictionary mapping notifier names to success status
        """
        if not self.notifiers:
            logger.debug("No notifiers configured")
            return {}

        enabled_notifiers = [n for n in self.notifiers if n.enabled]

        if not enabled_notifiers:
            logger.debug("No enabled notifiers")
            return {}

        logger.info(
            f"Sending notifications to {len(enabled_notifiers)} notifiers for {change.file_name}"
        )

        if parallel:
            # Send in parallel
            tasks = [
                self._send_with_logging(notifier, change, metadata)
                for notifier in enabled_notifiers
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Build results dict
            return {
                notifier.config.name: (
                    result if not isinstance(result, Exception) else False
                )
                for notifier, result in zip(enabled_notifiers, results)
            }
        else:
            # Send sequentially
            results = {}
            for notifier in enabled_notifiers:
                success = await self._send_with_logging(notifier, change, metadata)
                results[notifier.config.name] = success

            return results

    async def _send_with_logging(
        self,
        notifier: BaseNotifier,
        change: ChangeEvent,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send notification with error logging.

        Args:
            notifier: Notifier to use
            change: Change event
            metadata: Optional metadata

        Returns:
            True if sent successfully
        """
        try:
            return await notifier.send(change, metadata)
        except Exception as e:
            logger.error(f"Error sending notification via {notifier.config.name}: {e}")
            return False

    def get_notifier(self, name: str) -> Optional[BaseNotifier]:
        """Get notifier by name.

        Args:
            name: Notifier name

        Returns:
            Notifier instance or None if not found
        """
        for notifier in self.notifiers:
            if notifier.config.name == name:
                return notifier
        return None

    def list_notifiers(self) -> List[Dict[str, Any]]:
        """List all notifiers with their status.

        Returns:
            List of notifier info dictionaries
        """
        return [
            {
                "name": n.config.name,
                "type": n.__class__.__name__,
                "enabled": n.enabled,
            }
            for n in self.notifiers
        ]

    def enable_notifier(self, name: str) -> bool:
        """Enable a notifier by name.

        Args:
            name: Notifier name

        Returns:
            True if found and enabled
        """
        notifier = self.get_notifier(name)
        if notifier:
            notifier.enabled = True
            logger.info(f"Enabled notifier: {name}")
            return True
        return False

    def disable_notifier(self, name: str) -> bool:
        """Disable a notifier by name.

        Args:
            name: Notifier name

        Returns:
            True if found and disabled
        """
        notifier = self.get_notifier(name)
        if notifier:
            notifier.enabled = False
            logger.info(f"Disabled notifier: {name}")
            return True
        return False

    def __len__(self) -> int:
        """Get number of notifiers."""
        return len(self.notifiers)

    def __repr__(self) -> str:
        enabled = sum(1 for n in self.notifiers if n.enabled)
        return f"NotificationManager(notifiers={len(self.notifiers)}, enabled={enabled})"

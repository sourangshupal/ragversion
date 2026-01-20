"""FastAPI dependencies for dependency injection."""

from typing import Optional
from fastapi import Depends, HTTPException, Header, status

from ragversion import AsyncVersionTracker
from ragversion.api.config import APIConfig


# Global tracker instance (set during app initialization)
_tracker: Optional[AsyncVersionTracker] = None


def set_tracker(tracker: AsyncVersionTracker) -> None:
    """Set the global tracker instance."""
    global _tracker
    _tracker = tracker


def get_tracker() -> AsyncVersionTracker:
    """Get the tracker instance."""
    if _tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracker not initialized"
        )
    return _tracker


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    config: APIConfig = Depends(lambda: APIConfig())
) -> None:
    """Verify API key if authentication is enabled."""
    if not config.auth_enabled:
        return

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if x_api_key not in config.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

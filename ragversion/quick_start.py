"""Quick start utilities for RAGVersion.

This module provides convenience functions to quickly set up RAGVersion
with sensible defaults, reducing boilerplate code for common use cases.
"""

import os
from typing import Literal, Optional

from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage, SupabaseStorage
from ragversion.storage.base import BaseStorage


async def create_tracker_from_config(
    storage_backend: Literal["sqlite", "supabase", "auto"] = "auto",
    store_content: bool = True,
    enable_chunk_tracking: bool = True,
    db_path: str = "ragversion.db",
    **kwargs
) -> AsyncVersionTracker:
    """Create and initialize tracker with smart defaults.

    This function automatically detects the best storage backend based on
    environment variables and initializes the tracker ready for use.

    Args:
        storage_backend: Storage type to use:
            - "auto": Detect from environment (checks for Supabase env vars,
              falls back to SQLite)
            - "sqlite": Use SQLite storage (local file-based)
            - "supabase": Use Supabase storage (requires env vars)
        store_content: Whether to store full file content (recommended: True)
        enable_chunk_tracking: Enable smart chunk-level tracking (v0.10.0 feature)
        db_path: Path to SQLite database file (only used for SQLite backend)
        **kwargs: Additional tracker configuration options:
            - max_file_size_mb: Maximum file size to process (default: 50)
            - hash_algorithm: Hash algorithm to use (default: "sha256")
            - callback_timeout: Timeout for callbacks in seconds (default: 60)

    Returns:
        Initialized AsyncVersionTracker instance ready to use

    Raises:
        ValueError: If unknown storage backend is specified
        StorageError: If Supabase is requested but environment variables are missing

    Example:
        >>> # Auto-detect storage from environment
        >>> tracker = await create_tracker_from_config()
        >>> await tracker.track("./document.pdf")
        >>> await tracker.close()
        >>>
        >>> # Explicitly use SQLite
        >>> tracker = await create_tracker_from_config(
        ...     storage_backend="sqlite",
        ...     db_path="./my_versions.db"
        ... )
        >>>
        >>> # Use Supabase (requires SUPABASE_URL and SUPABASE_SERVICE_KEY env vars)
        >>> tracker = await create_tracker_from_config(storage_backend="supabase")
    """
    # Auto-detect storage backend
    if storage_backend == "auto":
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"):
            storage_backend = "supabase"
        else:
            storage_backend = "sqlite"

    # Create storage based on backend type
    storage: BaseStorage
    if storage_backend == "sqlite":
        storage = SQLiteStorage(db_path=db_path)
    elif storage_backend == "supabase":
        storage = SupabaseStorage.from_env()
    else:
        raise ValueError(
            f"Unknown storage backend: {storage_backend}. "
            "Valid options: 'sqlite', 'supabase', 'auto'"
        )

    # Create tracker with configuration
    tracker = AsyncVersionTracker(
        storage=storage,
        store_content=store_content,
        chunk_tracking_enabled=enable_chunk_tracking,
        **kwargs
    )

    # Initialize the tracker
    await tracker.initialize()

    return tracker

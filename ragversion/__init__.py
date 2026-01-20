"""RAGVersion - Async-first version tracking for RAG applications."""

from ragversion.models import (
    ChangeEvent,
    ChangeType,
    Document,
    Version,
    BatchResult,
    FileProcessingError,
    StorageStatistics,
    DocumentStatistics,
)
from ragversion.tracker import AsyncVersionTracker
from ragversion.storage import BaseStorage, SQLiteStorage, SupabaseStorage
from ragversion.watcher import FileWatcher, watch_directory, watch_paths
from ragversion.exceptions import (
    RAGVersionError,
    ParsingError,
    StorageError,
    ConfigurationError,
)

__version__ = "0.10.0"

__all__ = [
    # Core tracker
    "AsyncVersionTracker",
    # Models
    "ChangeEvent",
    "ChangeType",
    "Document",
    "Version",
    "BatchResult",
    "FileProcessingError",
    "StorageStatistics",
    "DocumentStatistics",
    # Storage
    "BaseStorage",
    "SQLiteStorage",
    "SupabaseStorage",
    # Watcher
    "FileWatcher",
    "watch_directory",
    "watch_paths",
    # Exceptions
    "RAGVersionError",
    "ParsingError",
    "StorageError",
    "ConfigurationError",
]

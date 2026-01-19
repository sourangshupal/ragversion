"""RAGVersion - Async-first version tracking for RAG applications."""

from ragversion.models import (
    ChangeEvent,
    ChangeType,
    Document,
    Version,
    BatchResult,
    FileProcessingError,
)
from ragversion.tracker import AsyncVersionTracker
from ragversion.storage import BaseStorage, SupabaseStorage
from ragversion.exceptions import (
    RAGVersionError,
    ParsingError,
    StorageError,
    ConfigurationError,
)

__version__ = "0.1.0"

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
    # Storage
    "BaseStorage",
    "SupabaseStorage",
    # Exceptions
    "RAGVersionError",
    "ParsingError",
    "StorageError",
    "ConfigurationError",
]

"""Core AsyncVersionTracker implementation."""

import asyncio
import inspect
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union, TYPE_CHECKING
from uuid import UUID

from ragversion.detector import ChangeDetector
from ragversion.exceptions import ParsingError, StorageError, RAGVersionError
from ragversion.models import (
    BatchResult,
    ChangeEvent,
    DiffResult,
    Document,
    DocumentStatistics,
    FileProcessingError,
    StorageStatistics,
    TrackResult,
    Version,
    ChunkDiff,
    ChunkingConfig,
)
from ragversion.storage.base import BaseStorage

if TYPE_CHECKING:
    from ragversion.notifications.manager import NotificationManager

logger = logging.getLogger(__name__)

CallbackType = Union[
    Callable[[ChangeEvent], None],
    Callable[[ChangeEvent], Awaitable[None]],
]


class AsyncVersionTracker:
    """Async-first version tracker for RAG applications."""

    def __init__(
        self,
        storage: BaseStorage,
        store_content: bool = True,
        max_file_size_mb: int = 50,
        hash_algorithm: str = "sha256",
        callback_timeout: int = 60,
        notification_manager: Optional["NotificationManager"] = None,
        chunk_tracking_enabled: bool = False,
        chunk_config: Optional[ChunkingConfig] = None,
    ):
        """
        Initialize AsyncVersionTracker.

        Args:
            storage: Storage backend
            store_content: Whether to store full content
            max_file_size_mb: Maximum file size to process
            hash_algorithm: Hash algorithm to use
            callback_timeout: Timeout for callbacks in seconds
            notification_manager: Optional notification manager
            chunk_tracking_enabled: Enable chunk-level tracking (v0.10.0)
            chunk_config: Chunk tracking configuration (v0.10.0)
        """
        self.storage = storage
        self.detector = ChangeDetector(
            storage=storage,
            store_content=store_content,
            max_file_size_mb=max_file_size_mb,
            hash_algorithm=hash_algorithm,
        )
        self.callback_timeout = callback_timeout
        self.notification_manager = notification_manager
        self._callbacks: List[CallbackType] = []
        self._initialized = False

        # Chunk tracking (v0.10.0)
        self.chunk_tracking_enabled = chunk_tracking_enabled
        self.chunk_config = chunk_config or ChunkingConfig()
        self.chunker = None
        self.chunk_detector = None

        # Initialize chunking components if enabled
        if self.chunk_tracking_enabled:
            try:
                from ragversion.chunking import ChunkerRegistry, ChunkChangeDetector

                self.chunker = ChunkerRegistry.get_chunker(
                    self.chunk_config.splitter_type,
                    chunk_size=self.chunk_config.chunk_size,
                    chunk_overlap=self.chunk_config.chunk_overlap,
                )
                self.chunk_detector = ChunkChangeDetector(storage, self.chunker)
                logger.info(
                    f"Chunk tracking enabled: {self.chunk_config.splitter_type} splitter, "
                    f"chunk_size={self.chunk_config.chunk_size}, overlap={self.chunk_config.chunk_overlap}"
                )
            except ImportError as e:
                logger.warning(f"Failed to initialize chunk tracking: {e}")
                self.chunk_tracking_enabled = False

    @classmethod
    async def create(
        cls,
        storage: Union[str, BaseStorage] = "sqlite",
        db_path: str = "ragversion.db",
        **kwargs
    ) -> "AsyncVersionTracker":
        """Create and initialize tracker with smart defaults.

        This factory method provides a convenient way to create and initialize
        a tracker with minimal configuration. It supports SQLite (default) and
        Supabase backends with automatic initialization.

        Args:
            storage: Storage backend ("sqlite", "supabase", or BaseStorage instance)
            db_path: Database path for SQLite (default: "ragversion.db")
            **kwargs: Additional tracker configuration (store_content, max_file_size_mb, etc.)

        Returns:
            Initialized tracker ready to use

        Raises:
            ValueError: If storage backend name is invalid
            ConfigurationError: If environment variables are missing for Supabase

        Examples:
            >>> # SQLite (zero config)
            >>> tracker = await AsyncVersionTracker.create()
            >>>
            >>> # Supabase (from environment variables)
            >>> tracker = await AsyncVersionTracker.create("supabase")
            >>>
            >>> # With custom configuration
            >>> tracker = await AsyncVersionTracker.create(
            ...     storage="sqlite",
            ...     db_path="my_db.db",
            ...     max_file_size_mb=100
            ... )
        """
        from ragversion.storage import SQLiteStorage, SupabaseStorage

        # Handle storage parameter
        if isinstance(storage, str):
            if storage == "sqlite":
                storage_instance = SQLiteStorage(db_path=db_path)
            elif storage == "supabase":
                storage_instance = SupabaseStorage.from_env()
            else:
                raise ValueError(
                    f"Unknown storage backend: {storage}\n\n"
                    f"Supported backends: 'sqlite', 'supabase'\n"
                    f"Or pass a BaseStorage instance directly."
                )
        else:
            storage_instance = storage

        # Create tracker
        tracker = cls(storage=storage_instance, **kwargs)

        # Initialize immediately
        await tracker.initialize()

        return tracker

    async def initialize(self) -> None:
        """Initialize the tracker and storage backend."""
        await self.storage.initialize()
        self._initialized = True

    async def close(self) -> None:
        """Close connections and cleanup resources."""
        await self.storage.close()
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure tracker is initialized."""
        if not self._initialized:
            raise RuntimeError("Tracker not initialized. Call initialize() first.")

    async def __aenter__(self) -> "AsyncVersionTracker":
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.close()

    # Event system

    def on_change(self, callback: CallbackType) -> None:
        """
        Register a callback for change events.

        Args:
            callback: Sync or async function that takes a ChangeEvent
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: CallbackType) -> None:
        """
        Remove a registered callback.

        Args:
            callback: The callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def _emit_event(self, event: ChangeEvent) -> None:
        """
        Emit a change event to all callbacks and notifications.

        Args:
            event: The change event to emit
        """
        # Send notifications if manager is configured
        if self.notification_manager:
            try:
                await self.notification_manager.notify(event)
            except Exception as e:
                logger.error(f"Error sending notifications: {e}")

        # Execute callbacks
        for callback in self._callbacks:
            try:
                # Check if callback is async
                if inspect.iscoroutinefunction(callback):
                    await asyncio.wait_for(
                        callback(event), timeout=self.callback_timeout
                    )
                else:
                    # Run sync callback in executor
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, callback, event),
                        timeout=self.callback_timeout,
                    )
            except asyncio.TimeoutError:
                logger.error(
                    f"Callback {callback.__name__} timed out after {self.callback_timeout}s"
                )
            except Exception as e:
                logger.error(f"Callback {callback.__name__} raised exception: {e}")

    # Core tracking methods

    async def track(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrackResult:
        """
        Track a single file for changes.

        Args:
            file_path: Path to the file
            metadata: Optional metadata to attach

        Returns:
            TrackResult with change information and tracking status

        Raises:
            ParsingError: If file parsing fails
            StorageError: If storage operation fails
            RAGVersionError: If tracker not initialized

        Examples:
            >>> result = await tracker.track("document.pdf")
            >>> if result.changed:
            ...     print(f"New version: {result.version_number}")
            ... else:
            ...     print("No changes detected")
            >>>
            >>> # Access properties without null checks
            >>> if result.change_type:
            ...     print(f"Change: {result.change_type}")
        """
        self._ensure_initialized()

        # Validate file_path
        if not file_path:
            raise ValueError("file_path cannot be empty")

        # Normalize file path
        normalized_path = str(Path(file_path).absolute())
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}\n\n"
                f"Troubleshooting:\n"
                f"  • Check file path is correct\n"
                f"  • Use absolute path: {normalized_path}\n"
                f"  • To track deletion, file must have been tracked before"
            )

        # Validate file size
        file_size = path.stat().st_size
        max_size = self.detector.max_file_size_mb * 1024 * 1024

        if file_size > max_size:
            raise ValueError(
                f"File too large: {file_size / 1024 / 1024:.1f}MB > {self.detector.max_file_size_mb}MB\n\n"
                f"Troubleshooting:\n"
                f"  • Increase limit: tracker = await AsyncVersionTracker.create(max_file_size_mb={int(file_size / 1024 / 1024) + 10})\n"
                f"  • Split large files into smaller chunks\n"
                f"  • Use external storage for large files"
            )

        # Check if file was tracked before
        existing_doc = await self.storage.get_document_by_path(normalized_path)
        was_tracked = existing_doc is not None
        current_version = existing_doc.current_version if existing_doc else 0

        try:
            # Detect change
            event = await self.detector.detect_change(file_path, metadata)

            # Emit event if change detected
            if event:
                await self._emit_event(event)

                # Return result with change
                return TrackResult(
                    changed=True,
                    event=event,
                    file_path=normalized_path,
                    was_tracked=was_tracked,
                    version_number=event.version_number,
                )
            else:
                # No change detected
                return TrackResult(
                    changed=False,
                    event=None,
                    file_path=normalized_path,
                    was_tracked=was_tracked,
                    version_number=current_version,
                )

        except ParsingError:
            raise
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error tracking {file_path}: {e}")
            raise

    async def track_directory(
        self,
        dir_path: str,
        patterns: Optional[List[str]] = None,
        recursive: bool = True,
        max_workers: int = 4,
        on_error: str = "continue",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BatchResult:
        """
        Track all files in a directory (batch processing).

        Args:
            dir_path: Path to directory to track
            patterns: Glob patterns for files to include (default: all files)
            recursive: Whether to search subdirectories
            max_workers: Number of parallel workers (default: 4)
            on_error: How to handle errors ("continue" or "stop")
            metadata: Optional metadata to attach to all files

        Returns:
            BatchResult with summary of tracked files

        Pattern Syntax:
            Uses glob patterns (https://docs.python.org/3/library/glob.html)

            Examples:
                ["*.pdf"]               # All PDF files
                ["*.txt", "*.md"]       # Text and Markdown files
                ["data/*.json"]         # JSON files in data/ folder
                ["**/*.py"]             # Python files in any subdirectory
                ["[!_]*.txt"]           # Text files not starting with _
                ["report_202[0-9].pdf"] # Reports from 2020-2029

            Special characters:
                *       # Matches any characters
                ?       # Matches single character
                [seq]   # Matches any character in seq
                [!seq]  # Matches any character not in seq
                **      # Matches directories recursively (requires recursive=True)

            Default:
                If patterns=None, tracks ALL files in directory

        Examples:
            >>> # Track all PDFs
            >>> result = await tracker.track_directory("./docs", patterns=["*.pdf"])
            >>>
            >>> # Track markdown and text files recursively
            >>> result = await tracker.track_directory(
            ...     "./notes",
            ...     patterns=["**/*.md", "**/*.txt"],
            ...     recursive=True
            ... )
            >>>
            >>> # Track everything
            >>> result = await tracker.track_directory("./data")
        """
        self._ensure_initialized()

        # Validate directory path
        dir_path_obj = Path(dir_path)
        if not dir_path_obj.exists():
            raise FileNotFoundError(
                f"Directory not found: {dir_path}\n\n"
                f"Troubleshooting:\n"
                f"  • Check path is correct: {dir_path_obj.absolute()}\n"
                f"  • Create directory: mkdir -p {dir_path}"
            )

        if not dir_path_obj.is_dir():
            raise ValueError(
                f"Path is not a directory: {dir_path}\n\n"
                f"Use tracker.track() for single files"
            )

        # Validate patterns syntax
        if patterns:
            for pattern in patterns:
                if not pattern:
                    raise ValueError("Empty pattern in list")

        started_at = datetime.utcnow()
        successful: List[ChangeEvent] = []
        failed: List[FileProcessingError] = []

        # Find all files
        files = self._find_files(dir_path, patterns, recursive)
        total_files = len(files)

        # Process files with semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_workers)

        async def process_file(file_path: str) -> None:
            async with semaphore:
                try:
                    result = await self.track(file_path, metadata)
                    if result.changed and result.event:
                        successful.append(result.event)
                except ParsingError as e:
                    error = FileProcessingError(
                        file_path=file_path,
                        error=str(e),
                        error_type="parsing",
                        exception_type=type(e.original_error).__name__,
                    )
                    failed.append(error)
                    logger.error(f"Parsing error for {file_path}: {e}")

                    if on_error == "stop":
                        raise
                except StorageError as e:
                    error = FileProcessingError(
                        file_path=file_path,
                        error=str(e),
                        error_type="storage",
                        exception_type=type(e.original_error).__name__ if e.original_error else "StorageError",
                    )
                    failed.append(error)
                    logger.error(f"Storage error for {file_path}: {e}")

                    if on_error == "stop":
                        raise
                except Exception as e:
                    error = FileProcessingError(
                        file_path=file_path,
                        error=str(e),
                        error_type="unknown",
                        exception_type=type(e).__name__,
                    )
                    failed.append(error)
                    logger.error(f"Unknown error for {file_path}: {e}")

                    if on_error == "stop":
                        raise

        # Process all files concurrently
        tasks = [process_file(file_path) for file_path in files]

        try:
            await asyncio.gather(*tasks)
        except Exception:
            # If on_error='stop', an exception will propagate here
            pass

        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        return BatchResult(
            successful=successful,
            failed=failed,
            total_files=total_files,
            duration_seconds=duration,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _find_files(
        self,
        dir_path: str,
        patterns: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> List[str]:
        """Find files matching patterns in directory."""
        path = Path(dir_path)

        if not path.exists() or not path.is_dir():
            return []

        files = []

        if recursive:
            for pattern in patterns or ["*"]:
                files.extend([str(p) for p in path.rglob(pattern) if p.is_file()])
        else:
            for pattern in patterns or ["*"]:
                files.extend([str(p) for p in path.glob(pattern) if p.is_file()])

        return files

    # Document queries

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        self._ensure_initialized()
        return await self.storage.get_document(document_id)

    async def get_document_by_path(self, file_path: str) -> Optional[Document]:
        """Get a document by file path."""
        self._ensure_initialized()
        return await self.storage.get_document_by_path(file_path)

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "updated_at",
    ) -> List[Document]:
        """List documents with pagination."""
        self._ensure_initialized()
        return await self.storage.list_documents(limit, offset, order_by)

    async def search_documents(
        self,
        metadata_filter: Optional[dict] = None,
        file_type: Optional[str] = None,
    ) -> List[Document]:
        """Search documents by metadata or file type."""
        self._ensure_initialized()
        return await self.storage.search_documents(metadata_filter, file_type)

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document and all its versions."""
        self._ensure_initialized()
        await self.storage.delete_document(document_id)

    # Version queries

    async def get_version(self, version_id: UUID) -> Optional[Version]:
        """Get a version by ID."""
        self._ensure_initialized()
        return await self.storage.get_version(version_id)

    async def get_version_by_number(
        self, document_id: UUID, version_number: int
    ) -> Optional[Version]:
        """Get a specific version of a document."""
        self._ensure_initialized()
        return await self.storage.get_version_by_number(document_id, version_number)

    async def list_versions(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Version]:
        """List all versions of a document."""
        self._ensure_initialized()
        return await self.storage.list_versions(document_id, limit, offset)

    async def get_latest_version(self, document_id: UUID) -> Optional[Version]:
        """Get the latest version of a document."""
        self._ensure_initialized()
        return await self.storage.get_latest_version(document_id)

    # Content operations

    async def get_content(self, version_id: UUID) -> Optional[str]:
        """Get content for a specific version."""
        self._ensure_initialized()
        return await self.storage.get_content(version_id)

    async def restore_version(
        self,
        document_id: UUID,
        version_number: int,
        target_path: Optional[str] = None,
        trigger_callbacks: bool = True,
    ) -> ChangeEvent:
        """
        Restore a document to a specific version.

        Args:
            document_id: ID of the document
            version_number: Version number to restore
            target_path: Optional path to restore to
            trigger_callbacks: Whether to trigger change callbacks

        Returns:
            ChangeEvent for the restoration
        """
        self._ensure_initialized()

        restored_path, event = await self.detector.restore_version(
            document_id, version_number, target_path
        )

        if trigger_callbacks:
            await self._emit_event(event)

        return event

    # Diff operations

    async def get_diff(
        self,
        document_id: UUID,
        from_version: int,
        to_version: int,
    ) -> Optional[DiffResult]:
        """Get diff between two versions."""
        self._ensure_initialized()
        return await self.storage.compute_diff(document_id, from_version, to_version)

    # Chunk-level operations (v0.10.0)

    async def get_chunk_diff(
        self,
        document_id: UUID,
        from_version: int,
        to_version: int,
    ) -> Optional[ChunkDiff]:
        """Get chunk-level diff between two versions.

        This method compares chunks between versions to identify which chunks
        have been added, removed, unchanged, or reordered. This enables
        cost-optimized embedding updates by only re-embedding changed chunks.

        Args:
            document_id: ID of the document
            from_version: Source version number
            to_version: Target version number

        Returns:
            ChunkDiff containing categorized chunk changes, or None if chunk
            tracking is disabled or versions not found

        Example:
            >>> chunk_diff = await tracker.get_chunk_diff(doc_id, 1, 2)
            >>> print(f"Savings: {chunk_diff.savings_percentage:.1f}%")
            >>> print(f"Chunks to re-embed: {len(chunk_diff.added_chunks)}")
        """
        self._ensure_initialized()

        if not self.chunk_tracking_enabled:
            logger.debug("Chunk tracking is disabled, returning None")
            return None

        try:
            # Get version records
            from_ver = await self.storage.get_version_by_number(document_id, from_version)
            to_ver = await self.storage.get_version_by_number(document_id, to_version)

            if not from_ver or not to_ver:
                logger.warning(
                    f"Version not found: from_version={from_version}, to_version={to_version}"
                )
                return None

            # Get content for to_version
            to_content = await self.storage.get_content(to_ver.id)
            if not to_content:
                logger.warning(f"No content found for version {to_ver.id}")
                return None

            # Detect chunk changes
            chunk_diff = await self.chunk_detector.detect_chunk_changes(
                document_id, from_ver.id, to_content, to_ver.id
            )

            # Log savings metrics
            metrics = self.chunk_detector.calculate_savings_metrics(chunk_diff)
            logger.info(
                f"Chunk diff for document {document_id} v{from_version}→v{to_version}: "
                f"{metrics['savings_percentage']:.1f}% savings, "
                f"{metrics['chunks_to_embed']} chunks to embed"
            )

            return chunk_diff

        except Exception as e:
            logger.error(f"Failed to compute chunk diff: {e}")
            return None

    async def track_with_chunks(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[Optional[ChangeEvent], Optional[ChunkDiff]]:
        """Track a file and create chunks if chunk tracking is enabled.

        This is an enhanced version of track() that also creates and stores
        chunks when chunk tracking is enabled.

        Args:
            file_path: Path to the file
            metadata: Optional metadata to attach

        Returns:
            Tuple of (ChangeEvent, ChunkDiff) if change detected, (None, None) otherwise

        Example:
            >>> event, chunk_diff = await tracker.track_with_chunks("doc.txt")
            >>> if chunk_diff:
            >>>     print(f"Created {len(chunk_diff.added_chunks)} chunks")
        """
        self._ensure_initialized()

        # First, track the document normally
        event = await self.track(file_path, metadata)

        if not event:
            return None, None

        # If chunk tracking disabled, return early
        if not self.chunk_tracking_enabled:
            return event, None

        try:
            # Get content for the new version
            content = await self.storage.get_content(event.version_id)
            if not content:
                logger.warning(f"No content found for version {event.version_id}")
                return event, None

            # Detect chunk changes (or create initial chunks)
            old_version_id = None
            if event.version_number > 1:
                # Get previous version
                old_version = await self.storage.get_version_by_number(
                    event.document_id, event.version_number - 1
                )
                old_version_id = old_version.id if old_version else None

            chunk_diff = await self.chunk_detector.detect_chunk_changes(
                event.document_id,
                old_version_id,
                content,
                event.version_id,
            )

            # Store chunks (all new chunks from the diff)
            chunks_to_store = []
            chunks_to_store.extend(chunk_diff.added_chunks)
            chunks_to_store.extend(chunk_diff.unchanged_chunks)
            chunks_to_store.extend(chunk_diff.reordered_chunks)

            if chunks_to_store and self.chunk_config.store_chunk_content:
                await self.storage.create_chunks_batch(chunks_to_store)
                logger.debug(f"Stored {len(chunks_to_store)} chunks for version {event.version_id}")

            # Log savings metrics
            metrics = self.chunk_detector.calculate_savings_metrics(chunk_diff)
            logger.info(
                f"Chunk tracking for {event.file_name}: "
                f"{metrics['total_chunks']} total chunks, "
                f"{metrics['savings_percentage']:.1f}% savings"
            )

            return event, chunk_diff

        except Exception as e:
            logger.error(f"Failed to create chunks for {file_path}: {e}")
            return event, None

    # Cleanup operations

    async def cleanup_old_versions(
        self,
        document_id: UUID,
        keep_count: int = 10,
    ) -> int:
        """Delete old versions, keeping only the most recent ones."""
        self._ensure_initialized()
        return await self.storage.cleanup_old_versions(document_id, keep_count)

    async def cleanup_by_age(self, days: int) -> int:
        """Delete versions older than specified days."""
        self._ensure_initialized()
        return await self.storage.cleanup_by_age(days)

    # Health check

    async def health_check(self) -> bool:
        """Check if storage backend is healthy."""
        return await self.storage.health_check()

    # Statistics operations

    async def get_statistics(self) -> StorageStatistics:
        """Get overall storage statistics."""
        self._ensure_initialized()
        return await self.storage.get_statistics()

    async def get_document_statistics(self, document_id: UUID) -> DocumentStatistics:
        """Get statistics for a specific document."""
        self._ensure_initialized()
        return await self.storage.get_document_statistics(document_id)

    async def get_top_documents(
        self,
        limit: int = 10,
        order_by: str = "version_count",
    ) -> List[Document]:
        """Get top documents by version count or other criteria."""
        self._ensure_initialized()
        return await self.storage.get_top_documents(limit, order_by)

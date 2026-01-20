"""Real-time file watching for automatic document tracking.

This module provides file system monitoring capabilities to automatically track
document changes without manual intervention.
"""

import asyncio
import logging
import signal
import time
from pathlib import Path
from typing import Callable, List, Optional, Set

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
)
from watchdog.observers import Observer

from ragversion.models import ChangeEvent
from ragversion.tracker import AsyncVersionTracker

logger = logging.getLogger(__name__)


class DocumentEventHandler(FileSystemEventHandler):
    """Handle file system events and queue them for processing."""

    def __init__(
        self,
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
    ) -> None:
        """Initialize event handler.

        Args:
            patterns: File patterns to watch (e.g., ["*.md", "*.txt"])
            ignore_patterns: Patterns to ignore (e.g., ["*.tmp", ".git/*"])
        """
        super().__init__()
        self.patterns = patterns or []
        self.ignore_patterns = ignore_patterns or [
            "*.tmp",
            "*.swp",
            "*~",
            ".git/*",
            ".DS_Store",
            "*.pyc",
            "__pycache__/*",
            ".ragversion/*",
            "ragversion.db*",
        ]
        self.event_queue: asyncio.Queue[FileSystemEvent] = asyncio.Queue()
        self._last_processed: dict[str, float] = {}  # Path -> timestamp
        self._debounce_seconds = 1.0  # Debounce rapid file changes

    def _should_process(self, event: FileSystemEvent) -> bool:
        """Check if event should be processed."""
        # Ignore directories
        if event.is_directory:
            return False

        path = Path(event.src_path)

        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if path.match(pattern):
                logger.debug(f"Ignoring {path} (matches ignore pattern: {pattern})")
                return False

        # If specific patterns provided, check them
        if self.patterns:
            matched = any(path.match(pattern) for pattern in self.patterns)
            if not matched:
                logger.debug(f"Ignoring {path} (doesn't match any pattern)")
                return False

        # Debounce: Ignore if same file was processed recently
        path_str = str(path)
        last_time = self._last_processed.get(path_str, 0)
        current_time = time.time()

        if current_time - last_time < self._debounce_seconds:
            logger.debug(f"Debouncing {path} (processed {current_time - last_time:.2f}s ago)")
            return False

        self._last_processed[path_str] = current_time
        return True

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events."""
        if self._should_process(event):
            logger.info(f"File created: {event.src_path}")
            self.event_queue.put_nowait(event)

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification events."""
        if self._should_process(event):
            logger.info(f"File modified: {event.src_path}")
            self.event_queue.put_nowait(event)

    def on_deleted(self, event: FileDeletedEvent) -> None:
        """Handle file deletion events."""
        if self._should_process(event):
            logger.info(f"File deleted: {event.src_path}")
            self.event_queue.put_nowait(event)

    def on_moved(self, event: FileMovedEvent) -> None:
        """Handle file move/rename events."""
        # Treat move as delete + create
        if self._should_process(event):
            logger.info(f"File moved: {event.src_path} -> {event.dest_path}")
            # Queue both deletion and creation
            delete_event = FileDeletedEvent(event.src_path)
            create_event = FileCreatedEvent(event.dest_path)
            self.event_queue.put_nowait(delete_event)
            self.event_queue.put_nowait(create_event)


class FileWatcher:
    """Watch directories for file changes and automatically track them."""

    def __init__(
        self,
        tracker: AsyncVersionTracker,
        paths: List[str],
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        recursive: bool = True,
        on_change: Optional[Callable[[ChangeEvent], None]] = None,
    ) -> None:
        """Initialize file watcher.

        Args:
            tracker: AsyncVersionTracker instance
            paths: Paths to watch (files or directories)
            patterns: File patterns to watch (e.g., ["*.md", "*.txt"])
            ignore_patterns: Patterns to ignore (e.g., ["*.tmp", ".git/*"])
            recursive: Watch subdirectories recursively
            on_change: Optional callback for change events
        """
        self.tracker = tracker
        self.paths = [Path(p).absolute() for p in paths]
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns
        self.recursive = recursive
        self.on_change = on_change

        self.event_handler = DocumentEventHandler(
            patterns=patterns, ignore_patterns=ignore_patterns
        )
        self.observer = Observer()
        self._running = False
        self._tasks: Set[asyncio.Task] = set()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame: object) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def start(self) -> None:
        """Start watching for file changes."""
        if self._running:
            logger.warning("Watcher already running")
            return

        logger.info("Starting file watcher...")
        self._running = True

        # Schedule observers for each path
        for path in self.paths:
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue

            logger.info(f"Watching: {path} (recursive={self.recursive})")
            self.observer.schedule(
                self.event_handler, str(path), recursive=self.recursive
            )

        self.observer.start()
        logger.info("File watcher started successfully")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if not self._running:
            return

        logger.info("Stopping file watcher...")
        self._running = False
        self.observer.stop()
        self.observer.join(timeout=5)
        logger.info("File watcher stopped")

    async def process_events(self) -> None:
        """Process file system events from the queue."""
        logger.info("Event processor started")

        while self._running:
            try:
                # Wait for events with timeout to allow graceful shutdown
                event = await asyncio.wait_for(
                    self.event_handler.event_queue.get(), timeout=1.0
                )

                # Process the event
                await self._process_event(event)

            except asyncio.TimeoutError:
                # No events in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

        logger.info("Event processor stopped")

    async def _process_event(self, event: FileSystemEvent) -> None:
        """Process a single file system event."""
        try:
            path = event.src_path

            # Track the file
            logger.debug(f"Tracking: {path}")
            result = await self.tracker.track(path)

            if result.changed and result.event:
                logger.info(f"Change detected: {result.change_type.value} - {path}")

                # Call user callback if provided
                if self.on_change:
                    if asyncio.iscoroutinefunction(self.on_change):
                        await self.on_change(result.event)
                    else:
                        self.on_change(result.event)
            else:
                logger.debug(f"No changes detected: {path}")

        except Exception as e:
            logger.error(f"Failed to track {event.src_path}: {e}")

    async def watch_blocking(
        self,
        on_change: Optional[Callable[[ChangeEvent], None]] = None,
    ) -> None:
        """Watch for file changes (blocks until stopped).

        This method runs forever until explicitly stopped with stop().
        Use this in scripts where file watching is the main task.

        Args:
            on_change: Optional callback function called for each change event

        Examples:
            >>> watcher = FileWatcher(tracker, ["./docs"])
            >>> await watcher.watch_blocking()  # Runs until Ctrl+C
        """
        if on_change:
            self.on_change = on_change

        # Start the observer
        self.start()

        try:
            # Process events until stopped
            await self.process_events()
        finally:
            # Ensure cleanup
            self.stop()

    async def watch_async(
        self,
        on_change: Optional[Callable[[ChangeEvent], None]] = None,
    ) -> asyncio.Task:
        """Watch for file changes in background (non-blocking).

        This method returns a Task that runs in the background.
        Use this when file watching is one of many concurrent tasks.

        Args:
            on_change: Optional callback function called for each change event

        Returns:
            asyncio.Task that can be cancelled or awaited

        Examples:
            >>> watcher = FileWatcher(tracker, ["./docs"])
            >>> task = await watcher.watch_async()
            >>> # Do other work...
            >>> await task  # Wait for watcher when ready
        """
        if on_change:
            self.on_change = on_change

        self.start()
        task = asyncio.create_task(self.process_events())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    # Aliases for backward compatibility
    async def watch(self) -> None:
        """Alias for watch_blocking() (deprecated, use watch_blocking instead)."""
        await self.watch_blocking()

    async def watch_in_background(self) -> asyncio.Task:
        """Alias for watch_async() (deprecated, use watch_async instead)."""
        return await self.watch_async()

    async def __aenter__(self) -> "FileWatcher":
        """Async context manager entry."""
        await self.tracker.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Async context manager exit."""
        self.stop()
        await self.tracker.close()


async def watch_directory(
    tracker: AsyncVersionTracker,
    path: str,
    patterns: Optional[List[str]] = None,
    ignore_patterns: Optional[List[str]] = None,
    recursive: bool = True,
    on_change: Optional[Callable[[ChangeEvent], None]] = None,
) -> None:
    """Watch a directory for changes and automatically track them.

    Args:
        tracker: AsyncVersionTracker instance
        path: Directory path to watch
        patterns: File patterns to watch (e.g., ["*.md", "*.txt"])
        ignore_patterns: Patterns to ignore (e.g., ["*.tmp", ".git/*"])
        recursive: Watch subdirectories recursively
        on_change: Optional callback for change events

    Example:
        ```python
        async with AsyncVersionTracker(storage=storage) as tracker:
            await watch_directory(
                tracker,
                "./docs",
                patterns=["*.md", "*.txt"],
                on_change=lambda change: print(f"Changed: {change.document.file_path}")
            )
        ```
    """
    watcher = FileWatcher(
        tracker=tracker,
        paths=[path],
        patterns=patterns,
        ignore_patterns=ignore_patterns,
        recursive=recursive,
        on_change=on_change,
    )

    await watcher.watch()


async def watch_paths(
    tracker: AsyncVersionTracker,
    paths: List[str],
    patterns: Optional[List[str]] = None,
    ignore_patterns: Optional[List[str]] = None,
    recursive: bool = True,
    on_change: Optional[Callable[[ChangeEvent], None]] = None,
) -> None:
    """Watch multiple paths for changes and automatically track them.

    Args:
        tracker: AsyncVersionTracker instance
        paths: List of paths to watch (files or directories)
        patterns: File patterns to watch (e.g., ["*.md", "*.txt"])
        ignore_patterns: Patterns to ignore (e.g., ["*.tmp", ".git/*"])
        recursive: Watch subdirectories recursively
        on_change: Optional callback for change events

    Example:
        ```python
        async with AsyncVersionTracker(storage=storage) as tracker:
            await watch_paths(
                tracker,
                ["./docs", "./guides", "README.md"],
                patterns=["*.md"],
                on_change=lambda change: print(f"Changed: {change.document.file_path}")
            )
        ```
    """
    watcher = FileWatcher(
        tracker=tracker,
        paths=paths,
        patterns=patterns,
        ignore_patterns=ignore_patterns,
        recursive=recursive,
        on_change=on_change,
    )

    await watcher.watch()

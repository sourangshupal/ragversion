"""
Basic usage example for RAGVersion.

This example shows how to:
1. Initialize AsyncVersionTracker
2. Track a single file
3. Track a directory
4. Handle change events with callbacks
"""

import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage


async def main():
    """Basic usage example."""

    # Initialize storage backend
    storage = SupabaseStorage.from_env()

    # Create tracker
    tracker = AsyncVersionTracker(
        storage=storage,
        store_content=True,
        max_file_size_mb=50,
    )

    # Initialize tracker
    await tracker.initialize()

    # Register a callback for changes
    def on_change(event):
        print(f"Change detected: {event.change_type.value} - {event.file_name}")
        print(f"  Version: {event.version_number}")
        print(f"  Hash: {event.content_hash[:8]}")

    tracker.on_change(on_change)

    # Track a single file
    print("\n=== Tracking single file ===")
    event = await tracker.track("./example_document.pdf")

    if event:
        print(f"Created new version: {event.version_number}")
    else:
        print("No changes detected")

    # Track a directory (batch processing)
    print("\n=== Tracking directory ===")
    result = await tracker.track_directory(
        "./documents",
        patterns=["*.pdf", "*.docx", "*.md"],
        recursive=True,
        max_workers=4,
    )

    print(f"Total files: {result.total_files}")
    print(f"Changes detected: {result.success_count}")
    print(f"Errors: {result.failure_count}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print(f"Success rate: {result.success_rate:.1f}%")

    # List tracked documents
    print("\n=== Tracked documents ===")
    documents = await tracker.list_documents(limit=10)

    for doc in documents:
        print(f"- {doc.file_name} (v{doc.current_version})")

    # Get version history for a document
    if documents:
        doc = documents[0]
        print(f"\n=== Version history for {doc.file_name} ===")

        versions = await tracker.list_versions(doc.id)
        for version in versions:
            print(f"  v{version.version_number}: {version.change_type.value}")

    # Close tracker
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())

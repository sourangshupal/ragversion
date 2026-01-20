"""Integration test for file watcher functionality."""

import asyncio
import tempfile
from pathlib import Path
import time

from ragversion import AsyncVersionTracker, FileWatcher
from ragversion.storage import SQLiteStorage


async def test_file_watcher():
    """Test file watcher with real file system operations."""
    print("🧪 Testing FileWatcher integration...")

    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        db_path = tmpdir_path / "test.db"

        print(f"📁 Test directory: {tmpdir}")

        # Create storage and tracker
        storage = SQLiteStorage(db_path=str(db_path))
        tracker = AsyncVersionTracker(storage=storage)
        await tracker.initialize()

        changes_detected = []

        def on_change(change):
            """Callback to collect changes."""
            changes_detected.append(change)
            print(f"  ✓ Change detected: {change.change_type.value} - {change.file_name}")

        # Create watcher
        watcher = FileWatcher(
            tracker=tracker,
            paths=[str(tmpdir)],
            patterns=["*.md", "*.txt"],
            recursive=True,
            on_change=on_change,
        )

        # Start watcher in background
        print("\n👀 Starting file watcher...")
        watcher_task = await watcher.watch_in_background()

        # Give watcher time to start
        await asyncio.sleep(0.5)

        # Test 1: Create a file
        print("\n📝 Test 1: Creating a new file...")
        test_file = tmpdir_path / "test_doc.md"
        test_file.write_text("# Test Document\n\nInitial content")
        await asyncio.sleep(1.5)  # Wait for event processing

        # Test 2: Modify the file
        print("\n✏️ Test 2: Modifying the file...")
        test_file.write_text("# Test Document\n\nModified content")
        await asyncio.sleep(1.5)

        # Test 3: Create another file
        print("\n📄 Test 3: Creating another file...")
        test_file2 = tmpdir_path / "test_doc2.txt"
        test_file2.write_text("Another test document")
        await asyncio.sleep(1.5)

        # Test 4: Delete a file
        print("\n🗑️ Test 4: Deleting a file...")
        test_file2.unlink()
        await asyncio.sleep(1.5)

        # Stop watcher
        print("\n⏹️ Stopping watcher...")
        watcher.stop()
        await asyncio.sleep(0.5)

        # Cleanup
        await tracker.close()

        # Verify results
        print("\n📊 Results:")
        print(f"  Total changes detected: {len(changes_detected)}")
        for i, change in enumerate(changes_detected, 1):
            print(f"  {i}. {change.change_type.value} - {change.file_name}")

        # Assertions
        assert len(changes_detected) >= 3, f"Expected at least 3 changes, got {len(changes_detected)}"

        change_types = [c.change_type.value for c in changes_detected]
        assert "created" in change_types, "No CREATE events detected"
        assert "modified" in change_types or "created" in change_types, "No MODIFY/CREATE events detected"

        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_file_watcher())

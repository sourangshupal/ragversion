"""Tests for AsyncVersionTracker."""

import pytest
from ragversion import AsyncVersionTracker
from ragversion.testing import MockStorage, create_test_file


@pytest.mark.asyncio
async def test_tracker_initialization():
    """Test tracker initialization."""
    storage = MockStorage()
    tracker = AsyncVersionTracker(storage=storage)

    await tracker.initialize()
    assert tracker._initialized

    await tracker.close()
    assert not tracker._initialized


@pytest.mark.asyncio
async def test_track_new_file():
    """Test tracking a new file."""
    storage = MockStorage()
    tracker = AsyncVersionTracker(storage=storage)

    await tracker.initialize()

    # Create a test file
    file_path = create_test_file(content="Hello, World!")

    # Track the file
    event = await tracker.track(file_path)

    assert event is not None
    assert event.change_type.value == "created"
    assert event.version_number == 1

    # Track again - should not create new version
    event2 = await tracker.track(file_path)
    assert event2 is None

    await tracker.close()


@pytest.mark.asyncio
async def test_track_modified_file():
    """Test tracking a modified file."""
    storage = MockStorage()
    tracker = AsyncVersionTracker(storage=storage)

    await tracker.initialize()

    # Create and track file
    file_path = create_test_file(content="Version 1")
    event1 = await tracker.track(file_path)

    assert event1.version_number == 1

    # Modify file
    with open(file_path, "w") as f:
        f.write("Version 2")

    # Track again
    event2 = await tracker.track(file_path)

    assert event2 is not None
    assert event2.change_type.value == "modified"
    assert event2.version_number == 2

    await tracker.close()


@pytest.mark.asyncio
async def test_callbacks():
    """Test event callbacks."""
    storage = MockStorage()
    tracker = AsyncVersionTracker(storage=storage)

    await tracker.initialize()

    # Track callback invocations
    events = []

    def callback(event):
        events.append(event)

    tracker.on_change(callback)

    # Create and track file
    file_path = create_test_file(content="Test")
    await tracker.track(file_path)

    assert len(events) == 1
    assert events[0].change_type.value == "created"

    await tracker.close()


@pytest.mark.asyncio
async def test_async_callback():
    """Test async callbacks."""
    storage = MockStorage()
    tracker = AsyncVersionTracker(storage=storage)

    await tracker.initialize()

    events = []

    async def async_callback(event):
        events.append(event)

    tracker.on_change(async_callback)

    # Create and track file
    file_path = create_test_file(content="Test")
    await tracker.track(file_path)

    assert len(events) == 1

    await tracker.close()


@pytest.mark.asyncio
async def test_context_manager():
    """Test context manager usage."""
    storage = MockStorage()

    async with AsyncVersionTracker(storage=storage) as tracker:
        assert tracker._initialized

        file_path = create_test_file(content="Test")
        event = await tracker.track(file_path)

        assert event is not None

    assert not tracker._initialized

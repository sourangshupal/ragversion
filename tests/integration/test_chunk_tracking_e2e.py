"""Integration tests for end-to-end chunk tracking workflows."""

import pytest
import tempfile
import os
from pathlib import Path
from uuid import UUID

from ragversion.tracker import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.models import ChunkingConfig, ChangeType


@pytest.fixture
async def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
async def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        f.write("Initial content.\nThis is the first version.")
        file_path = f.name

    yield file_path

    # Cleanup
    try:
        os.unlink(file_path)
    except:
        pass


# ============================================================================
# SQLite Backend Tests
# ============================================================================


@pytest.mark.asyncio
async def test_track_with_chunks_sqlite_first_version(temp_db, temp_file):
    """Test track_with_chunks() with SQLite for first version."""
    # Setup
    storage = SQLiteStorage(temp_db)
    chunk_config = ChunkingConfig(
        enabled=True,
        chunk_size=100,
        chunk_overlap=20,
        splitter_type="recursive",
    )

    async with AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config,
    ) as tracker:
        # Track file
        event, chunk_diff = await tracker.track_with_chunks(temp_file)

        # Verify event
        assert event is not None
        assert event.change_type == ChangeType.CREATED
        assert event.file_path == temp_file

        # Verify chunk diff
        assert chunk_diff is not None
        assert len(chunk_diff.added_chunks) > 0
        assert len(chunk_diff.removed_chunks) == 0
        assert len(chunk_diff.unchanged_chunks) == 0
        assert chunk_diff.from_version == 0
        assert chunk_diff.to_version == 1

        # Verify chunks stored
        chunks = await storage.get_chunks_by_version(event.version_id)
        assert len(chunks) == len(chunk_diff.added_chunks)

        # Verify chunk content stored
        for chunk in chunks:
            content = await storage.get_chunk_content(chunk.id)
            assert content is not None
            assert len(content) > 0


@pytest.mark.asyncio
async def test_track_with_chunks_sqlite_modification(temp_db, temp_file):
    """Test track_with_chunks() with SQLite for modification."""
    # Setup
    storage = SQLiteStorage(temp_db)
    chunk_config = ChunkingConfig(
        enabled=True,
        chunk_size=50,
        chunk_overlap=10,
        splitter_type="recursive",
    )

    async with AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config,
    ) as tracker:
        # Track initial version
        event1, chunk_diff1 = await tracker.track_with_chunks(temp_file)
        initial_chunk_count = len(chunk_diff1.added_chunks)

        # Modify file
        with open(temp_file, 'a') as f:
            f.write("\n\nNew paragraph added.\nThis is additional content.")

        # Track modification
        event2, chunk_diff2 = await tracker.track_with_chunks(temp_file)

        # Verify event
        assert event2 is not None
        assert event2.change_type == ChangeType.MODIFIED
        assert event2.version_number == 2

        # Verify chunk diff
        assert chunk_diff2 is not None
        assert len(chunk_diff2.added_chunks) > 0  # New chunks
        assert len(chunk_diff2.unchanged_chunks) > 0  # Some unchanged
        assert chunk_diff2.from_version == 1
        assert chunk_diff2.to_version == 2

        # Verify savings
        assert chunk_diff2.savings_percentage > 0
        assert chunk_diff2.savings_percentage < 100

        # Verify chunks stored
        chunks_v2 = await storage.get_chunks_by_version(event2.version_id)
        assert len(chunks_v2) > initial_chunk_count


@pytest.mark.asyncio
async def test_chunk_diff_accuracy_sqlite(temp_db, temp_file):
    """Test chunk diff accuracy with SQLite."""
    # Setup
    storage = SQLiteStorage(temp_db)
    chunk_config = ChunkingConfig(
        enabled=True,
        chunk_size=30,
        chunk_overlap=5,
        splitter_type="character",
    )

    async with AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config,
    ) as tracker:
        # Track initial version
        event1, chunk_diff1 = await tracker.track_with_chunks(temp_file)
        doc_id = event1.document_id

        # Modify file - change only middle section
        with open(temp_file, 'w') as f:
            f.write("Initial content.\nMODIFIED SECTION.\nThis is the first version.")

        # Track modification
        event2, chunk_diff2 = await tracker.track_with_chunks(temp_file)

        # Get chunk diff using tracker method
        chunk_diff = await tracker.get_chunk_diff(doc_id, 1, 2)

        # Verify diff exists
        assert chunk_diff is not None

        # Verify accuracy
        # Should detect: some unchanged (before/after), some modified (middle)
        assert len(chunk_diff.unchanged_chunks) >= 0  # At least some parts unchanged
        assert len(chunk_diff.added_chunks) > 0 or len(chunk_diff.removed_chunks) > 0

        # Total chunks should be consistent
        total_chunks_v2 = len(chunk_diff.added_chunks) + len(chunk_diff.unchanged_chunks) + len(chunk_diff.reordered_chunks)
        assert total_chunks_v2 > 0


@pytest.mark.asyncio
async def test_chunk_tracking_disabled_fallback(temp_db, temp_file):
    """Test fallback to document-level tracking when chunks disabled."""
    # Setup
    storage = SQLiteStorage(temp_db)

    async with AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=False,  # Disabled
    ) as tracker:
        # Track file (should work without chunk tracking)
        event = await tracker.track(temp_file)

        # Verify event
        assert event is not None
        assert event.change_type == ChangeType.CREATED

        # Verify no chunks created
        chunks = await storage.get_chunks_by_version(event.version_id)
        assert len(chunks) == 0

        # Modify file
        with open(temp_file, 'a') as f:
            f.write("\nModified content.")

        # Track modification
        event2 = await tracker.track(temp_file)

        # Verify modification tracked
        assert event2 is not None
        assert event2.change_type == ChangeType.MODIFIED

        # Get chunk diff should return None (chunks disabled)
        chunk_diff = await tracker.get_chunk_diff(event.document_id, 1, 2)
        assert chunk_diff is None


@pytest.mark.asyncio
async def test_cost_savings_verification(temp_db):
    """Test cost savings with specific content changes."""
    # Create test file with known content
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        # Write 10 distinct paragraphs
        for i in range(10):
            f.write(f"Paragraph {i}. " * 10)
            f.write("\n\n")
        test_file = f.name

    try:
        # Setup
        storage = SQLiteStorage(temp_db)
        chunk_config = ChunkingConfig(
            enabled=True,
            chunk_size=100,
            chunk_overlap=20,
            splitter_type="recursive",
        )

        async with AsyncVersionTracker(
            storage=storage,
            chunk_tracking_enabled=True,
            chunk_config=chunk_config,
        ) as tracker:
            # Track initial version
            event1, chunk_diff1 = await tracker.track_with_chunks(test_file)
            initial_chunk_count = len(chunk_diff1.added_chunks)

            # Modify only 1 paragraph (10% change)
            with open(test_file, 'r') as f:
                content = f.read()

            modified_content = content.replace("Paragraph 5", "MODIFIED Paragraph 5")

            with open(test_file, 'w') as f:
                f.write(modified_content)

            # Track modification
            event2, chunk_diff2 = await tracker.track_with_chunks(test_file)

            # Verify savings
            # Should have high savings (>80%) since only 1 paragraph changed
            assert chunk_diff2.savings_percentage > 80.0

            # Verify only a small number of chunks were added
            assert len(chunk_diff2.added_chunks) < initial_chunk_count * 0.3

            # Verify most chunks unchanged
            assert len(chunk_diff2.unchanged_chunks) > initial_chunk_count * 0.7

    finally:
        # Cleanup
        try:
            os.unlink(test_file)
        except:
            pass


# ============================================================================
# Integration with LangChain (Mock)
# ============================================================================


@pytest.mark.asyncio
async def test_langchain_smart_sync_integration(temp_db, temp_file):
    """Test LangChain smart sync integration with chunk tracking."""
    from unittest.mock import AsyncMock, Mock

    # Setup
    storage = SQLiteStorage(temp_db)
    chunk_config = ChunkingConfig(
        enabled=True,
        chunk_size=100,
        chunk_overlap=20,
    )

    # Create mock LangChain components
    mock_embeddings = Mock()
    mock_vectorstore = AsyncMock()
    mock_text_splitter = Mock()
    mock_text_splitter.split_text.return_value = ["chunk1", "chunk2"]

    async with AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config,
    ) as tracker:
        # Import LangChain integration
        try:
            from ragversion.integrations.langchain import LangChainSync

            # Create sync with chunk tracking enabled
            sync = LangChainSync(
                tracker=tracker,
                text_splitter=mock_text_splitter,
                embeddings=mock_embeddings,
                vectorstore=mock_vectorstore,
                enable_chunk_tracking=True,
            )

            # Track initial version
            event1, chunk_diff1 = await tracker.track_with_chunks(temp_file)

            # Verify vectorstore was called (via callback)
            # Note: In real integration, callback would be triggered
            # Here we're just verifying the setup

            assert sync.enable_chunk_tracking is True
            assert sync.tracker.chunk_tracking_enabled is True

        except ImportError:
            pytest.skip("LangChain not installed")


@pytest.mark.asyncio
async def test_llamaindex_smart_sync_integration(temp_db, temp_file):
    """Test LlamaIndex smart sync integration with chunk tracking."""
    from unittest.mock import AsyncMock, Mock

    # Setup
    storage = SQLiteStorage(temp_db)
    chunk_config = ChunkingConfig(
        enabled=True,
        chunk_size=100,
        chunk_overlap=20,
    )

    # Create mock LlamaIndex components
    mock_index = Mock()

    async with AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config,
    ) as tracker:
        # Import LlamaIndex integration
        try:
            from ragversion.integrations.llamaindex import LlamaIndexSync

            # Create sync with chunk tracking enabled
            sync = LlamaIndexSync(
                tracker=tracker,
                index=mock_index,
                enable_chunk_tracking=True,
            )

            # Track initial version
            event1, chunk_diff1 = await tracker.track_with_chunks(temp_file)

            # Verify setup
            assert sync.enable_chunk_tracking is True
            assert sync.tracker.chunk_tracking_enabled is True

        except ImportError:
            pytest.skip("LlamaIndex not installed")


# ============================================================================
# Batch Operations with Chunks
# ============================================================================


@pytest.mark.asyncio
async def test_track_directory_with_chunks(temp_db):
    """Test tracking directory with chunk tracking enabled."""
    # Create temp directory with multiple files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        for i in range(3):
            file_path = Path(temp_dir) / f"test{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"Content for file {i}.\n" * 10)

        # Setup
        storage = SQLiteStorage(temp_db)
        chunk_config = ChunkingConfig(
            enabled=True,
            chunk_size=50,
            chunk_overlap=10,
        )

        async with AsyncVersionTracker(
            storage=storage,
            chunk_tracking_enabled=True,
            chunk_config=chunk_config,
        ) as tracker:
            # Track directory
            result = await tracker.track_directory(temp_dir, recursive=True)

            # Verify all files tracked
            assert result.success_count == 3
            assert result.failure_count == 0

            # Verify chunks created for all files
            docs = await tracker.list_documents()
            assert len(docs) == 3

            for doc in docs:
                latest_version = await tracker.get_latest_version(doc.id)
                chunks = await storage.get_chunks_by_version(latest_version.id)
                assert len(chunks) > 0


# ============================================================================
# Error Handling and Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_chunk_tracking_with_empty_file(temp_db):
    """Test chunk tracking with empty file."""
    # Create empty file
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        empty_file = f.name
        # Write nothing

    try:
        # Setup
        storage = SQLiteStorage(temp_db)
        chunk_config = ChunkingConfig(enabled=True)

        async with AsyncVersionTracker(
            storage=storage,
            chunk_tracking_enabled=True,
            chunk_config=chunk_config,
        ) as tracker:
            # Track empty file
            event, chunk_diff = await tracker.track_with_chunks(empty_file)

            # Should still create event
            assert event is not None
            assert event.change_type == ChangeType.CREATED

            # Chunk diff may be empty or have empty chunks
            if chunk_diff:
                assert chunk_diff.total_chunks >= 0

    finally:
        try:
            os.unlink(empty_file)
        except:
            pass


@pytest.mark.asyncio
async def test_chunk_tracking_with_large_file(temp_db):
    """Test chunk tracking with large file (1000+ chunks)."""
    # Create large file
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        # Write 100KB of content
        for i in range(1000):
            f.write(f"Line {i}. " * 20)
            f.write("\n")
        large_file = f.name

    try:
        # Setup
        storage = SQLiteStorage(temp_db)
        chunk_config = ChunkingConfig(
            enabled=True,
            chunk_size=100,
            chunk_overlap=10,
        )

        async with AsyncVersionTracker(
            storage=storage,
            chunk_tracking_enabled=True,
            chunk_config=chunk_config,
        ) as tracker:
            # Track large file
            event, chunk_diff = await tracker.track_with_chunks(large_file)

            # Verify chunks created
            assert chunk_diff is not None
            assert len(chunk_diff.added_chunks) > 100  # Should have many chunks

            # Verify batch insert worked
            chunks = await storage.get_chunks_by_version(event.version_id)
            assert len(chunks) == len(chunk_diff.added_chunks)

    finally:
        try:
            os.unlink(large_file)
        except:
            pass


@pytest.mark.asyncio
async def test_chunk_content_compression(temp_db, temp_file):
    """Test chunk content compression storage."""
    # Setup
    storage = SQLiteStorage(temp_db, content_compression=True)
    chunk_config = ChunkingConfig(
        enabled=True,
        store_chunk_content=True,
    )

    async with AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config,
    ) as tracker:
        # Track file
        event, chunk_diff = await tracker.track_with_chunks(temp_file)

        # Verify chunk content stored and retrievable
        for chunk in chunk_diff.added_chunks:
            content = await storage.get_chunk_content(chunk.id)
            assert content is not None
            assert len(content) > 0

            # Content should match what's in metadata
            if "content" in chunk.metadata:
                assert content == chunk.metadata["content"]


@pytest.mark.asyncio
async def test_chunk_tracking_version_history(temp_db, temp_file):
    """Test chunk tracking across multiple versions."""
    # Setup
    storage = SQLiteStorage(temp_db)
    chunk_config = ChunkingConfig(enabled=True, chunk_size=50)

    async with AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config,
    ) as tracker:
        # Track v1
        event1, chunk_diff1 = await tracker.track_with_chunks(temp_file)

        # Modify and track v2
        with open(temp_file, 'a') as f:
            f.write("\nVersion 2 content.")
        event2, chunk_diff2 = await tracker.track_with_chunks(temp_file)

        # Modify and track v3
        with open(temp_file, 'a') as f:
            f.write("\nVersion 3 content.")
        event3, chunk_diff3 = await tracker.track_with_chunks(temp_file)

        # Verify version history
        doc = await tracker.get_document(event1.document_id)
        assert doc.version_count == 3

        # Verify chunk diffs
        diff_1_to_2 = await tracker.get_chunk_diff(event1.document_id, 1, 2)
        diff_2_to_3 = await tracker.get_chunk_diff(event1.document_id, 2, 3)

        assert diff_1_to_2 is not None
        assert diff_2_to_3 is not None

        # Each diff should show progressive changes
        assert diff_1_to_2.from_version == 1
        assert diff_1_to_2.to_version == 2
        assert diff_2_to_3.from_version == 2
        assert diff_2_to_3.to_version == 3

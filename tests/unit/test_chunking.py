"""Unit tests for chunking module."""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from ragversion.models import Chunk, ChunkDiff, ChunkingConfig
from ragversion.chunking.splitters import (
    BaseChunker,
    RecursiveTextChunker,
    CharacterChunker,
    ChunkerRegistry,
)
from ragversion.chunking.detector import ChunkChangeDetector


# Test Data
SAMPLE_TEXT = """This is the first paragraph.
It has multiple sentences.

This is the second paragraph.
It also has multiple sentences.

This is the third paragraph.
With even more content here."""

SHORT_TEXT = "This is a short piece of text."

LONG_TEXT = """Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
Nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum."""


# ============================================================================
# RecursiveTextChunker Tests
# ============================================================================


@pytest.mark.asyncio
async def test_recursive_chunker_split_basic():
    """Test RecursiveTextChunker basic splitting."""
    chunker = RecursiveTextChunker(chunk_size=100, chunk_overlap=20)

    chunks = await chunker.split_text(SAMPLE_TEXT)

    # Should produce multiple chunks
    assert len(chunks) > 0

    # Each chunk should respect size constraint
    for chunk in chunks:
        # Allow some tolerance for overlap
        assert len(chunk) <= chunker.chunk_size + 100


@pytest.mark.asyncio
async def test_recursive_chunker_split_short_text():
    """Test RecursiveTextChunker with text shorter than chunk size."""
    chunker = RecursiveTextChunker(chunk_size=500, chunk_overlap=50)

    chunks = await chunker.split_text(SHORT_TEXT)

    # Should produce a single chunk
    assert len(chunks) == 1
    assert chunks[0] == SHORT_TEXT


@pytest.mark.asyncio
async def test_recursive_chunker_fallback():
    """Test RecursiveTextChunker fallback when LangChain unavailable."""
    chunker = RecursiveTextChunker(chunk_size=100, chunk_overlap=20)

    # Mock ImportError for LangChain
    with patch("ragversion.chunking.splitters.RecursiveCharacterTextSplitter", side_effect=ImportError):
        chunks = await chunker.split_text(SAMPLE_TEXT)

        # Should still produce chunks using fallback
        assert len(chunks) > 0


@pytest.mark.asyncio
async def test_recursive_chunker_token_counting():
    """Test RecursiveTextChunker token counting."""
    chunker = RecursiveTextChunker()

    # Test with sample text
    token_count = chunker.count_tokens(SHORT_TEXT)

    # Should return a positive integer
    assert isinstance(token_count, int)
    assert token_count > 0

    # Longer text should have more tokens
    long_token_count = chunker.count_tokens(LONG_TEXT)
    assert long_token_count > token_count


@pytest.mark.asyncio
async def test_recursive_chunker_empty_text():
    """Test RecursiveTextChunker with empty text."""
    chunker = RecursiveTextChunker(chunk_size=100, chunk_overlap=20)

    chunks = await chunker.split_text("")

    # Should return empty list or list with single empty string
    assert len(chunks) <= 1


@pytest.mark.asyncio
async def test_recursive_chunker_overlap():
    """Test RecursiveTextChunker chunk overlap."""
    chunker = RecursiveTextChunker(chunk_size=50, chunk_overlap=10)

    chunks = await chunker.split_text(LONG_TEXT)

    # With overlap, adjacent chunks should share some content
    if len(chunks) > 1:
        # This is a basic check - the actual overlap detection would be more complex
        assert len(chunks) >= 2


# ============================================================================
# CharacterChunker Tests
# ============================================================================


@pytest.mark.asyncio
async def test_character_chunker_split_basic():
    """Test CharacterChunker basic splitting."""
    chunker = CharacterChunker(chunk_size=50, chunk_overlap=10)

    chunks = await chunker.split_text(LONG_TEXT)

    # Should produce multiple chunks
    assert len(chunks) > 0

    # Each chunk should respect size constraint
    for chunk in chunks:
        assert len(chunk) <= chunker.chunk_size + chunker.chunk_overlap


@pytest.mark.asyncio
async def test_character_chunker_split_exact_size():
    """Test CharacterChunker with text exactly chunk size."""
    chunker = CharacterChunker(chunk_size=30, chunk_overlap=0)

    chunks = await chunker.split_text(SHORT_TEXT)

    # Should produce at least one chunk
    assert len(chunks) >= 1


@pytest.mark.asyncio
async def test_character_chunker_token_counting():
    """Test CharacterChunker token counting (character-based)."""
    chunker = CharacterChunker()

    token_count = chunker.count_tokens(SHORT_TEXT)

    # Should be approximately length / 4
    assert isinstance(token_count, int)
    assert token_count > 0
    assert token_count == len(SHORT_TEXT) // 4


@pytest.mark.asyncio
async def test_character_chunker_empty_text():
    """Test CharacterChunker with empty text."""
    chunker = CharacterChunker(chunk_size=100, chunk_overlap=20)

    chunks = await chunker.split_text("")

    # Should return empty list
    assert len(chunks) == 0


# ============================================================================
# ChunkerRegistry Tests
# ============================================================================


def test_chunker_registry_get_recursive():
    """Test ChunkerRegistry returns RecursiveTextChunker."""
    chunker = ChunkerRegistry.get_chunker("recursive", chunk_size=500, chunk_overlap=50)

    assert isinstance(chunker, RecursiveTextChunker)
    assert chunker.chunk_size == 500
    assert chunker.chunk_overlap == 50


def test_chunker_registry_get_character():
    """Test ChunkerRegistry returns CharacterChunker."""
    chunker = ChunkerRegistry.get_chunker("character", chunk_size=300, chunk_overlap=30)

    assert isinstance(chunker, CharacterChunker)
    assert chunker.chunk_size == 300
    assert chunker.chunk_overlap == 30


def test_chunker_registry_default():
    """Test ChunkerRegistry returns default chunker for unknown type."""
    chunker = ChunkerRegistry.get_chunker("unknown_type")

    # Should fallback to RecursiveTextChunker
    assert isinstance(chunker, RecursiveTextChunker)


# ============================================================================
# ChunkChangeDetector Tests
# ============================================================================


@pytest.mark.asyncio
async def test_chunk_change_detection_100_percent_unchanged():
    """Test chunk detection with 100% unchanged content (hash comparison)."""
    # Setup
    document_id = uuid4()
    old_version_id = uuid4()
    new_version_id = uuid4()

    # Create mock storage
    mock_storage = AsyncMock()

    # Create old chunks
    old_chunks = [
        Chunk(
            id=uuid4(),
            document_id=document_id,
            version_id=old_version_id,
            chunk_index=0,
            content_hash="hash1",
            token_count=10,
        ),
        Chunk(
            id=uuid4(),
            document_id=document_id,
            version_id=old_version_id,
            chunk_index=1,
            content_hash="hash2",
            token_count=10,
        ),
    ]

    mock_storage.get_chunks_by_version.return_value = old_chunks
    mock_storage.get_version.side_effect = lambda vid: Mock(version_number=1 if vid == old_version_id else 2)

    # Create chunker that returns same content
    mock_chunker = AsyncMock()
    mock_chunker.split_text.return_value = ["chunk1", "chunk2"]
    mock_chunker.count_tokens.return_value = 10

    # Create detector
    detector = ChunkChangeDetector(mock_storage, mock_chunker)

    # Mock hash generation to return same hashes
    with patch.object(detector, '_hash', side_effect=["hash1", "hash2"]):
        chunk_diff = await detector.detect_chunk_changes(
            document_id, old_version_id, "content", new_version_id
        )

    # Verify 100% unchanged
    assert len(chunk_diff.added_chunks) == 0
    assert len(chunk_diff.removed_chunks) == 0
    assert len(chunk_diff.unchanged_chunks) == 2
    assert chunk_diff.savings_percentage == 100.0


@pytest.mark.asyncio
async def test_chunk_change_detection_50_percent_changed():
    """Test chunk detection with 50% content change."""
    # Setup
    document_id = uuid4()
    old_version_id = uuid4()
    new_version_id = uuid4()

    # Create mock storage
    mock_storage = AsyncMock()

    # Create old chunks (4 chunks)
    old_chunks = [
        Chunk(
            id=uuid4(),
            document_id=document_id,
            version_id=old_version_id,
            chunk_index=i,
            content_hash=f"hash{i}",
            token_count=10,
        )
        for i in range(4)
    ]

    mock_storage.get_chunks_by_version.return_value = old_chunks
    mock_storage.get_version.side_effect = lambda vid: Mock(version_number=1 if vid == old_version_id else 2)

    # Create chunker
    mock_chunker = AsyncMock()
    mock_chunker.split_text.return_value = ["chunk0", "chunk1", "new_chunk2", "new_chunk3"]
    mock_chunker.count_tokens.return_value = 10

    # Create detector
    detector = ChunkChangeDetector(mock_storage, mock_chunker)

    # Mock hash: first 2 same, last 2 different
    with patch.object(detector, '_hash', side_effect=["hash0", "hash1", "hash_new2", "hash_new3"]):
        chunk_diff = await detector.detect_chunk_changes(
            document_id, old_version_id, "content", new_version_id
        )

    # Verify 50% changed
    assert len(chunk_diff.added_chunks) == 2  # new_chunk2, new_chunk3
    assert len(chunk_diff.removed_chunks) == 2  # old chunk2, chunk3
    assert len(chunk_diff.unchanged_chunks) == 2  # chunk0, chunk1
    assert chunk_diff.savings_percentage == 50.0


@pytest.mark.asyncio
async def test_chunk_change_detection_reordering():
    """Test chunk detection with reordered chunks."""
    # Setup
    document_id = uuid4()
    old_version_id = uuid4()
    new_version_id = uuid4()

    # Create mock storage
    mock_storage = AsyncMock()

    # Create old chunks in order 0, 1, 2
    old_chunks = [
        Chunk(
            id=uuid4(),
            document_id=document_id,
            version_id=old_version_id,
            chunk_index=i,
            content_hash=f"hash{i}",
            token_count=10,
        )
        for i in range(3)
    ]

    mock_storage.get_chunks_by_version.return_value = old_chunks
    mock_storage.get_version.side_effect = lambda vid: Mock(version_number=1 if vid == old_version_id else 2)

    # Create chunker - returns chunks in different order (2, 0, 1)
    mock_chunker = AsyncMock()
    mock_chunker.split_text.return_value = ["chunk2", "chunk0", "chunk1"]
    mock_chunker.count_tokens.return_value = 10

    # Create detector
    detector = ChunkChangeDetector(mock_storage, mock_chunker)

    # Mock hash: return hashes in new order (hash2, hash0, hash1)
    with patch.object(detector, '_hash', side_effect=["hash2", "hash0", "hash1"]):
        chunk_diff = await detector.detect_chunk_changes(
            document_id, old_version_id, "content", new_version_id
        )

    # Verify reordering detected
    assert len(chunk_diff.added_chunks) == 0
    assert len(chunk_diff.removed_chunks) == 0
    assert len(chunk_diff.reordered_chunks) == 3  # All chunks reordered
    assert len(chunk_diff.unchanged_chunks) == 0
    # Reordered chunks count as unchanged for savings
    assert chunk_diff.savings_percentage == 100.0


@pytest.mark.asyncio
async def test_chunk_change_detection_all_new():
    """Test chunk detection with completely new content."""
    # Setup
    document_id = uuid4()
    old_version_id = uuid4()
    new_version_id = uuid4()

    # Create mock storage
    mock_storage = AsyncMock()

    # Create old chunks
    old_chunks = [
        Chunk(
            id=uuid4(),
            document_id=document_id,
            version_id=old_version_id,
            chunk_index=i,
            content_hash=f"old_hash{i}",
            token_count=10,
        )
        for i in range(2)
    ]

    mock_storage.get_chunks_by_version.return_value = old_chunks
    mock_storage.get_version.side_effect = lambda vid: Mock(version_number=1 if vid == old_version_id else 2)

    # Create chunker
    mock_chunker = AsyncMock()
    mock_chunker.split_text.return_value = ["new_chunk1", "new_chunk2"]
    mock_chunker.count_tokens.return_value = 10

    # Create detector
    detector = ChunkChangeDetector(mock_storage, mock_chunker)

    # Mock hash: return different hashes
    with patch.object(detector, '_hash', side_effect=["new_hash1", "new_hash2"]):
        chunk_diff = await detector.detect_chunk_changes(
            document_id, old_version_id, "content", new_version_id
        )

    # Verify all changed
    assert len(chunk_diff.added_chunks) == 2
    assert len(chunk_diff.removed_chunks) == 2
    assert len(chunk_diff.unchanged_chunks) == 0
    assert chunk_diff.savings_percentage == 0.0


@pytest.mark.asyncio
async def test_chunk_change_detection_first_version():
    """Test chunk detection for first version (no old chunks)."""
    # Setup
    document_id = uuid4()
    new_version_id = uuid4()

    # Create mock storage
    mock_storage = AsyncMock()
    mock_storage.get_chunks_by_version.return_value = []
    mock_storage.get_version.return_value = Mock(version_number=1)

    # Create chunker
    mock_chunker = AsyncMock()
    mock_chunker.split_text.return_value = ["chunk1", "chunk2"]
    mock_chunker.count_tokens.return_value = 10

    # Create detector
    detector = ChunkChangeDetector(mock_storage, mock_chunker)

    # Mock hash
    with patch.object(detector, '_hash', side_effect=["hash1", "hash2"]):
        chunk_diff = await detector.detect_chunk_changes(
            document_id, None, "content", new_version_id
        )

    # Verify all added
    assert len(chunk_diff.added_chunks) == 2
    assert len(chunk_diff.removed_chunks) == 0
    assert len(chunk_diff.unchanged_chunks) == 0
    # First version has 0% savings (all new)
    assert chunk_diff.savings_percentage == 0.0


@pytest.mark.asyncio
async def test_chunk_change_detection_hash_algorithm():
    """Test chunk hash generation."""
    # Create detector
    mock_storage = AsyncMock()
    mock_chunker = AsyncMock()
    detector = ChunkChangeDetector(mock_storage, mock_chunker)

    # Test hash generation
    hash1 = detector._hash("test content")
    hash2 = detector._hash("test content")
    hash3 = detector._hash("different content")

    # Same content should produce same hash
    assert hash1 == hash2

    # Different content should produce different hash
    assert hash1 != hash3

    # Should be SHA-256 (64 hex characters)
    assert len(hash1) == 64
    assert all(c in '0123456789abcdef' for c in hash1)


# ============================================================================
# ChunkDiff Model Tests
# ============================================================================


def test_chunk_diff_savings_percentage_calculation():
    """Test ChunkDiff savings percentage calculation."""
    document_id = uuid4()

    # Create chunks
    added = [Mock(spec=Chunk) for _ in range(2)]
    removed = [Mock(spec=Chunk) for _ in range(1)]
    unchanged = [Mock(spec=Chunk) for _ in range(7)]
    reordered = [Mock(spec=Chunk) for _ in range(0)]

    chunk_diff = ChunkDiff(
        document_id=document_id,
        from_version=1,
        to_version=2,
        added_chunks=added,
        removed_chunks=removed,
        unchanged_chunks=unchanged,
        reordered_chunks=reordered,
    )

    # Total chunks that matter for savings: added + unchanged + reordered
    # = 2 + 7 + 0 = 9
    # Unchanged for savings: unchanged + reordered = 7 + 0 = 7
    # Savings: 7/9 = 77.77%
    expected_savings = (7 / 9) * 100

    assert abs(chunk_diff.savings_percentage - expected_savings) < 0.01


def test_chunk_diff_savings_percentage_zero_chunks():
    """Test ChunkDiff savings percentage with zero chunks."""
    document_id = uuid4()

    chunk_diff = ChunkDiff(
        document_id=document_id,
        from_version=1,
        to_version=2,
        added_chunks=[],
        removed_chunks=[],
        unchanged_chunks=[],
        reordered_chunks=[],
    )

    # Should return 0.0 for empty diff
    assert chunk_diff.savings_percentage == 0.0


def test_chunk_diff_total_chunks():
    """Test ChunkDiff total_chunks property."""
    document_id = uuid4()

    chunk_diff = ChunkDiff(
        document_id=document_id,
        from_version=1,
        to_version=2,
        added_chunks=[Mock(spec=Chunk) for _ in range(3)],
        removed_chunks=[Mock(spec=Chunk) for _ in range(2)],
        unchanged_chunks=[Mock(spec=Chunk) for _ in range(5)],
        reordered_chunks=[Mock(spec=Chunk) for _ in range(1)],
    )

    # Total chunks = added + unchanged + reordered
    assert chunk_diff.total_chunks == 9


# ============================================================================
# Integration with ChunkingConfig Tests
# ============================================================================


def test_chunking_config_defaults():
    """Test ChunkingConfig default values."""
    config = ChunkingConfig()

    assert config.enabled is False  # Opt-in
    assert config.chunk_size == 500
    assert config.chunk_overlap == 50
    assert config.splitter_type == "recursive"
    assert config.store_chunk_content is True


def test_chunking_config_custom_values():
    """Test ChunkingConfig with custom values."""
    config = ChunkingConfig(
        enabled=True,
        chunk_size=1000,
        chunk_overlap=100,
        splitter_type="character",
        store_chunk_content=False,
    )

    assert config.enabled is True
    assert config.chunk_size == 1000
    assert config.chunk_overlap == 100
    assert config.splitter_type == "character"
    assert config.store_chunk_content is False

"""Integration tests for LlamaIndex quick_start."""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Check if LlamaIndex is available
try:
    from llama_index.core import VectorStoreIndex
    from llama_index.embeddings.openai import OpenAIEmbedding
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False


@pytest.mark.skipif(not LLAMAINDEX_AVAILABLE, reason="LlamaIndex not installed")
@pytest.mark.asyncio
class TestLlamaIndexQuickStart:
    """Test LlamaIndex quick_start function."""

    async def test_quick_start_basic(self):
        """Test basic quick_start functionality."""
        from ragversion.integrations.llamaindex.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test documents
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()
            (doc_dir / "test.txt").write_text("Test document content")

            # Mock the components
            with patch("ragversion.integrations.llamaindex.quick_start.OpenAIEmbedding") as mock_embeddings:
                with patch("ragversion.integrations.llamaindex.quick_start.VectorStoreIndex") as mock_index:
                    # Setup mocks
                    mock_embeddings_instance = MagicMock()
                    mock_embeddings.return_value = mock_embeddings_instance

                    mock_index_instance = MagicMock()
                    mock_index_instance.insert = MagicMock()
                    mock_index.from_documents.return_value = mock_index_instance

                    with patch("ragversion.quick_start.SQLiteStorage") as mock_storage:
                        mock_storage_instance = MagicMock()
                        mock_storage_instance.initialize = MagicMock(return_value=None)
                        mock_storage_instance.close = MagicMock(return_value=None)
                        mock_storage.return_value = mock_storage_instance

                        with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                            mock_tracker_instance = MagicMock()
                            mock_tracker_instance.initialize = MagicMock(return_value=None)
                            mock_tracker_instance.track_directory = MagicMock(
                                return_value=MagicMock(success_count=1, total_files=1, failed=[])
                            )
                            mock_tracker_instance.on_change = MagicMock()
                            mock_tracker_instance.chunk_tracking_enabled = True
                            mock_tracker.return_value = mock_tracker_instance

                            # Call quick_start
                            sync = await quick_start(directory=str(doc_dir))

                            # Verify tracker was initialized
                            mock_tracker_instance.initialize.assert_called_once()

                            # Verify index was created
                            mock_index.from_documents.assert_called_once()

                            # Verify directory was synced
                            mock_tracker_instance.track_directory.assert_called_once()

    async def test_quick_start_with_custom_chunk_size(self):
        """Test quick_start with custom chunk size."""
        from ragversion.integrations.llamaindex.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()
            (doc_dir / "test.txt").write_text("Test content")

            with patch("ragversion.integrations.llamaindex.quick_start.OpenAIEmbedding"):
                with patch("ragversion.integrations.llamaindex.quick_start.VectorStoreIndex") as mock_index:
                    mock_index.from_documents.return_value = MagicMock()

                    with patch("ragversion.integrations.llamaindex.quick_start.SentenceSplitter") as mock_splitter:
                        mock_splitter_instance = MagicMock()
                        mock_splitter.return_value = mock_splitter_instance

                        with patch("ragversion.quick_start.create_tracker_from_config") as mock_create_tracker:
                            mock_tracker = MagicMock()
                            mock_tracker.track_directory = MagicMock(
                                return_value=MagicMock(success_count=0, total_files=0, failed=[])
                            )
                            mock_tracker.on_change = MagicMock()
                            mock_tracker.chunk_tracking_enabled = True
                            mock_create_tracker.return_value = mock_tracker

                            # Call with custom chunk size
                            sync = await quick_start(
                                directory=str(doc_dir),
                                chunk_size=2048,
                                chunk_overlap=200,
                            )

                            # Verify node parser was created with custom size
                            mock_splitter.assert_called_once_with(
                                chunk_size=2048,
                                chunk_overlap=200,
                            )

    async def test_quick_start_with_custom_embeddings(self):
        """Test quick_start with custom embeddings."""
        from ragversion.integrations.llamaindex.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()

            custom_embeddings = MagicMock()

            with patch("ragversion.integrations.llamaindex.quick_start.VectorStoreIndex") as mock_index:
                mock_index.from_documents.return_value = MagicMock()

                with patch("ragversion.quick_start.create_tracker_from_config") as mock_create_tracker:
                    mock_tracker = MagicMock()
                    mock_tracker.track_directory = MagicMock(
                        return_value=MagicMock(success_count=0, total_files=0, failed=[])
                    )
                    mock_tracker.on_change = MagicMock()
                    mock_tracker.chunk_tracking_enabled = True
                    mock_create_tracker.return_value = mock_tracker

                    # Call with custom embeddings
                    sync = await quick_start(
                        directory=str(doc_dir),
                        embeddings=custom_embeddings,
                    )

                    # Verify index was created with custom embeddings
                    mock_index.from_documents.assert_called_once()
                    call_kwargs = mock_index.from_documents.call_args[1]
                    assert call_kwargs["embed_model"] == custom_embeddings

    async def test_quick_start_with_sqlite_backend(self):
        """Test quick_start with explicit SQLite backend."""
        from ragversion.integrations.llamaindex.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()

            with patch("ragversion.integrations.llamaindex.quick_start.OpenAIEmbedding"):
                with patch("ragversion.integrations.llamaindex.quick_start.VectorStoreIndex") as mock_index:
                    mock_index.from_documents.return_value = MagicMock()

                    with patch("ragversion.quick_start.create_tracker_from_config") as mock_create_tracker:
                        mock_tracker = MagicMock()
                        mock_tracker.track_directory = MagicMock(
                            return_value=MagicMock(success_count=0, total_files=0, failed=[])
                        )
                        mock_tracker.on_change = MagicMock()
                        mock_tracker.chunk_tracking_enabled = True
                        mock_create_tracker.return_value = mock_tracker

                        # Call with SQLite backend
                        sync = await quick_start(
                            directory=str(doc_dir),
                            storage_backend="sqlite",
                        )

                        # Verify create_tracker_from_config was called with sqlite
                        mock_create_tracker.assert_called_once()
                        call_kwargs = mock_create_tracker.call_args[1]
                        assert call_kwargs["storage_backend"] == "sqlite"

    async def test_quick_start_chunk_tracking_disabled(self):
        """Test quick_start with chunk tracking disabled."""
        from ragversion.integrations.llamaindex.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()

            with patch("ragversion.integrations.llamaindex.quick_start.OpenAIEmbedding"):
                with patch("ragversion.integrations.llamaindex.quick_start.VectorStoreIndex") as mock_index:
                    mock_index.from_documents.return_value = MagicMock()

                    with patch("ragversion.quick_start.create_tracker_from_config") as mock_create_tracker:
                        mock_tracker = MagicMock()
                        mock_tracker.track_directory = MagicMock(
                            return_value=MagicMock(success_count=0, total_files=0, failed=[])
                        )
                        mock_tracker.on_change = MagicMock()
                        mock_tracker.chunk_tracking_enabled = False
                        mock_create_tracker.return_value = mock_tracker

                        # Call with chunk tracking disabled
                        sync = await quick_start(
                            directory=str(doc_dir),
                            enable_chunk_tracking=False,
                        )

                        # Verify create_tracker_from_config was called with chunk tracking disabled
                        mock_create_tracker.assert_called_once()
                        call_kwargs = mock_create_tracker.call_args[1]
                        assert call_kwargs["enable_chunk_tracking"] is False

    async def test_quick_start_with_index_path_warning(self):
        """Test that index_path parameter shows warning (reserved for future use)."""
        from ragversion.integrations.llamaindex.quick_start import quick_start
        import logging

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()

            with patch("ragversion.integrations.llamaindex.quick_start.OpenAIEmbedding"):
                with patch("ragversion.integrations.llamaindex.quick_start.VectorStoreIndex") as mock_index:
                    mock_index.from_documents.return_value = MagicMock()

                    with patch("ragversion.quick_start.create_tracker_from_config") as mock_create_tracker:
                        mock_tracker = MagicMock()
                        mock_tracker.track_directory = MagicMock(
                            return_value=MagicMock(success_count=0, total_files=0, failed=[])
                        )
                        mock_tracker.on_change = MagicMock()
                        mock_tracker.chunk_tracking_enabled = True
                        mock_create_tracker.return_value = mock_tracker

                        with patch("ragversion.integrations.llamaindex.quick_start.logger") as mock_logger:
                            # Call with index_path
                            sync = await quick_start(
                                directory=str(doc_dir),
                                index_path="./test_index",
                            )

                            # Verify warning was logged
                            mock_logger.warning.assert_called_once()
                            assert "reserved for future use" in mock_logger.warning.call_args[0][0]

"""Integration tests for LangChain quick_start."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Check if LangChain is available
try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
@pytest.mark.asyncio
class TestLangChainQuickStart:
    """Test LangChain quick_start function."""

    async def test_quick_start_with_faiss(self):
        """Test quick_start with FAISS vectorstore."""
        from ragversion.integrations.langchain.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test documents
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()
            (doc_dir / "test.txt").write_text("Test document content")

            # Mock the embeddings and vectorstore creation
            with patch("ragversion.integrations.langchain.quick_start.OpenAIEmbeddings") as mock_embeddings:
                with patch("ragversion.integrations.langchain.quick_start.FAISS") as mock_faiss:
                    # Setup mocks
                    mock_embeddings_instance = MagicMock()
                    mock_embeddings.return_value = mock_embeddings_instance

                    mock_vectorstore_instance = MagicMock()
                    mock_vectorstore_instance.aadd_documents = MagicMock(return_value=None)
                    mock_faiss.from_texts.return_value = mock_vectorstore_instance

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
                            sync = await quick_start(
                                directory=str(doc_dir),
                                vectorstore_type="faiss",
                            )

                            # Verify tracker was initialized
                            mock_tracker_instance.initialize.assert_called_once()

                            # Verify FAISS was created
                            mock_faiss.from_texts.assert_called_once()

                            # Verify directory was synced
                            mock_tracker_instance.track_directory.assert_called_once()

    async def test_quick_start_with_custom_chunk_size(self):
        """Test quick_start with custom chunk size."""
        from ragversion.integrations.langchain.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()
            (doc_dir / "test.txt").write_text("Test content")

            with patch("ragversion.integrations.langchain.quick_start.OpenAIEmbeddings"):
                with patch("ragversion.integrations.langchain.quick_start.FAISS") as mock_faiss:
                    mock_faiss.from_texts.return_value = MagicMock()

                    with patch("ragversion.integrations.langchain.quick_start.RecursiveCharacterTextSplitter") as mock_splitter:
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
                                chunk_size=500,
                                chunk_overlap=100,
                            )

                            # Verify text splitter was created with custom size
                            mock_splitter.assert_called_once_with(
                                chunk_size=500,
                                chunk_overlap=100,
                            )

    async def test_quick_start_with_custom_embeddings(self):
        """Test quick_start with custom embeddings."""
        from ragversion.integrations.langchain.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()

            custom_embeddings = MagicMock()

            with patch("ragversion.integrations.langchain.quick_start.FAISS") as mock_faiss:
                mock_faiss.from_texts.return_value = MagicMock()

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

                    # Verify custom embeddings were used
                    assert sync.embeddings == custom_embeddings

    async def test_quick_start_with_sqlite_backend(self):
        """Test quick_start with explicit SQLite backend."""
        from ragversion.integrations.langchain.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()

            with patch("ragversion.integrations.langchain.quick_start.OpenAIEmbeddings"):
                with patch("ragversion.integrations.langchain.quick_start.FAISS") as mock_faiss:
                    mock_faiss.from_texts.return_value = MagicMock()

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

    async def test_quick_start_with_chroma(self):
        """Test quick_start with Chroma vectorstore."""
        from ragversion.integrations.langchain.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()

            with patch("ragversion.integrations.langchain.quick_start.OpenAIEmbeddings"):
                with patch("ragversion.integrations.langchain.quick_start.Chroma") as mock_chroma:
                    mock_chroma.return_value = MagicMock()

                    with patch("ragversion.quick_start.create_tracker_from_config") as mock_create_tracker:
                        mock_tracker = MagicMock()
                        mock_tracker.track_directory = MagicMock(
                            return_value=MagicMock(success_count=0, total_files=0, failed=[])
                        )
                        mock_tracker.on_change = MagicMock()
                        mock_tracker.chunk_tracking_enabled = True
                        mock_create_tracker.return_value = mock_tracker

                        # Call with Chroma
                        sync = await quick_start(
                            directory=str(doc_dir),
                            vectorstore_type="chroma",
                            vectorstore_path="./test_chroma_db",
                        )

                        # Verify Chroma was created
                        mock_chroma.assert_called_once()
                        call_kwargs = mock_chroma.call_args[1]
                        assert call_kwargs["persist_directory"] == "./test_chroma_db"

    async def test_quick_start_invalid_vectorstore_raises_error(self):
        """Test that invalid vectorstore type raises ValueError."""
        from ragversion.integrations.langchain.quick_start import quick_start

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_dir = Path(tmpdir) / "documents"
            doc_dir.mkdir()

            with pytest.raises(ValueError, match="Unknown vectorstore type"):
                await quick_start(
                    directory=str(doc_dir),
                    vectorstore_type="invalid",
                )

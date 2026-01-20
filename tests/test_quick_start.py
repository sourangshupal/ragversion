"""Unit tests for core quick_start module."""

import os
import pytest
from unittest.mock import patch, MagicMock

from ragversion.quick_start import create_tracker_from_config
from ragversion.storage import SQLiteStorage, SupabaseStorage


@pytest.mark.asyncio
class TestCreateTrackerFromConfig:
    """Test create_tracker_from_config function."""

    async def test_auto_detects_supabase_from_env(self):
        """Test that auto mode detects Supabase when env vars are set."""
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_SERVICE_KEY": "test-key"
        }):
            with patch("ragversion.quick_start.SupabaseStorage") as mock_supabase:
                # Mock the storage and tracker
                mock_storage_instance = MagicMock()
                mock_supabase.from_env.return_value = mock_storage_instance

                with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                    mock_tracker_instance = MagicMock()
                    mock_tracker_instance.initialize = MagicMock(return_value=None)
                    mock_tracker.return_value = mock_tracker_instance

                    # Call the function
                    tracker = await create_tracker_from_config(storage_backend="auto")

                    # Verify Supabase was used
                    mock_supabase.from_env.assert_called_once()
                    mock_tracker.assert_called_once()

    async def test_auto_falls_back_to_sqlite(self):
        """Test that auto mode falls back to SQLite when no Supabase env vars."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("ragversion.quick_start.SQLiteStorage") as mock_sqlite:
                # Mock the storage and tracker
                mock_storage_instance = MagicMock()
                mock_sqlite.return_value = mock_storage_instance

                with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                    mock_tracker_instance = MagicMock()
                    mock_tracker_instance.initialize = MagicMock(return_value=None)
                    mock_tracker.return_value = mock_tracker_instance

                    # Call the function
                    tracker = await create_tracker_from_config(storage_backend="auto")

                    # Verify SQLite was used
                    mock_sqlite.assert_called_once_with(db_path="ragversion.db")
                    mock_tracker.assert_called_once()

    async def test_explicit_sqlite_backend(self):
        """Test explicitly using SQLite backend."""
        with patch("ragversion.quick_start.SQLiteStorage") as mock_sqlite:
            # Mock the storage and tracker
            mock_storage_instance = MagicMock()
            mock_sqlite.return_value = mock_storage_instance

            with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.initialize = MagicMock(return_value=None)
                mock_tracker.return_value = mock_tracker_instance

                # Call with explicit SQLite
                tracker = await create_tracker_from_config(
                    storage_backend="sqlite",
                    db_path="custom.db"
                )

                # Verify SQLite was used with custom path
                mock_sqlite.assert_called_once_with(db_path="custom.db")

    async def test_explicit_supabase_backend(self):
        """Test explicitly using Supabase backend."""
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_SERVICE_KEY": "test-key"
        }):
            with patch("ragversion.quick_start.SupabaseStorage") as mock_supabase:
                # Mock the storage and tracker
                mock_storage_instance = MagicMock()
                mock_supabase.from_env.return_value = mock_storage_instance

                with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                    mock_tracker_instance = MagicMock()
                    mock_tracker_instance.initialize = MagicMock(return_value=None)
                    mock_tracker.return_value = mock_tracker_instance

                    # Call with explicit Supabase
                    tracker = await create_tracker_from_config(storage_backend="supabase")

                    # Verify Supabase was used
                    mock_supabase.from_env.assert_called_once()

    async def test_invalid_storage_backend_raises_error(self):
        """Test that invalid storage backend raises ValueError."""
        with pytest.raises(ValueError, match="Unknown storage backend"):
            await create_tracker_from_config(storage_backend="invalid")

    async def test_tracker_initialization_called(self):
        """Test that tracker.initialize() is called."""
        with patch("ragversion.quick_start.SQLiteStorage") as mock_sqlite:
            mock_storage_instance = MagicMock()
            mock_sqlite.return_value = mock_storage_instance

            with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.initialize = MagicMock(return_value=None)
                mock_tracker.return_value = mock_tracker_instance

                # Call the function
                tracker = await create_tracker_from_config(storage_backend="sqlite")

                # Verify initialize was called
                mock_tracker_instance.initialize.assert_called_once()

    async def test_chunk_tracking_enabled_by_default(self):
        """Test that chunk tracking is enabled by default."""
        with patch("ragversion.quick_start.SQLiteStorage") as mock_sqlite:
            mock_storage_instance = MagicMock()
            mock_sqlite.return_value = mock_storage_instance

            with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.initialize = MagicMock(return_value=None)
                mock_tracker.return_value = mock_tracker_instance

                # Call the function
                tracker = await create_tracker_from_config(storage_backend="sqlite")

                # Verify chunk_tracking_enabled was passed as True
                call_kwargs = mock_tracker.call_args[1]
                assert call_kwargs["chunk_tracking_enabled"] is True

    async def test_chunk_tracking_can_be_disabled(self):
        """Test that chunk tracking can be explicitly disabled."""
        with patch("ragversion.quick_start.SQLiteStorage") as mock_sqlite:
            mock_storage_instance = MagicMock()
            mock_sqlite.return_value = mock_storage_instance

            with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.initialize = MagicMock(return_value=None)
                mock_tracker.return_value = mock_tracker_instance

                # Call with chunk tracking disabled
                tracker = await create_tracker_from_config(
                    storage_backend="sqlite",
                    enable_chunk_tracking=False
                )

                # Verify chunk_tracking_enabled was passed as False
                call_kwargs = mock_tracker.call_args[1]
                assert call_kwargs["chunk_tracking_enabled"] is False

    async def test_store_content_true_by_default(self):
        """Test that store_content is True by default."""
        with patch("ragversion.quick_start.SQLiteStorage") as mock_sqlite:
            mock_storage_instance = MagicMock()
            mock_sqlite.return_value = mock_storage_instance

            with patch("ragversion.quick_start.AsyncVersionTracker") as mock_tracker:
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.initialize = MagicMock(return_value=None)
                mock_tracker.return_value = mock_tracker_instance

                # Call the function
                tracker = await create_tracker_from_config(storage_backend="sqlite")

                # Verify store_content was passed as True
                call_kwargs = mock_tracker.call_args[1]
                assert call_kwargs["store_content"] is True

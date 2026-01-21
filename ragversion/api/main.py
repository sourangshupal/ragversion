"""Main entry point for uvicorn to start the RAGVersion web server.

This module creates a FastAPI app instance at module level so that uvicorn
can be started with: uvicorn ragversion.api.main:app
"""
import os
from dotenv import load_dotenv

from ragversion import AsyncVersionTracker
from ragversion.api.app import create_app
from ragversion.api.config import APIConfig
from ragversion.storage.supabase import SupabaseStorage
from ragversion.storage.sqlite import SQLiteStorage

# Load environment variables
load_dotenv()

# Determine storage backend
storage_backend = os.getenv("RAGVERSION_STORAGE_BACKEND", "sqlite")

# Create storage instance
if storage_backend == "supabase":
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError(
            "Supabase backend requires SUPABASE_URL and SUPABASE_SERVICE_KEY "
            "environment variables"
        )

    storage = SupabaseStorage(url=supabase_url, key=supabase_key)
else:
    # Default to SQLite
    db_path = os.getenv("RAGVERSION_SQLITE_PATH", "./ragversion.db")
    storage = SQLiteStorage(db_path=db_path)

# Create tracker instance
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=os.getenv("RAGVERSION_TRACKING_STORE_CONTENT", "true").lower() == "true",
    max_file_size_mb=int(os.getenv("RAGVERSION_TRACKING_MAX_FILE_SIZE_MB", "50")),
)

# Create API config
api_config = APIConfig(
    host=os.getenv("RAGVERSION_API_HOST", "0.0.0.0"),
    port=int(os.getenv("RAGVERSION_API_PORT", "6699")),
    cors_enabled=os.getenv("RAGVERSION_API_CORS_ENABLED", "true").lower() == "true",
    cors_origins=os.getenv("RAGVERSION_API_CORS_ORIGINS", "*").split(","),
)

# Create FastAPI app
app = create_app(tracker=tracker, config=api_config)

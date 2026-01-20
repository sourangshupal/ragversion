"""Quick start utilities for LangChain integration.

This module provides a one-line setup for LangChain integration,
dramatically reducing boilerplate code from ~35 lines to just 3 lines.
"""

import logging
from pathlib import Path
from typing import Any, List, Literal, Optional

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS, Chroma
    from langchain_core.embeddings import Embeddings
    from langchain_text_splitters import TextSplitter

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    RecursiveCharacterTextSplitter = Any
    OpenAIEmbeddings = Any
    FAISS = Any
    Chroma = Any
    Embeddings = Any
    TextSplitter = Any

from ragversion.quick_start import create_tracker_from_config
from ragversion.integrations.langchain.sync import LangChainSync

logger = logging.getLogger(__name__)


async def quick_start(
    directory: str,
    vectorstore_type: Literal["faiss", "chroma"] = "faiss",
    vectorstore_path: Optional[str] = None,
    embeddings: Optional[Embeddings] = None,
    storage_backend: Literal["sqlite", "supabase", "auto"] = "auto",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    file_patterns: Optional[List[str]] = None,
    enable_chunk_tracking: bool = True,
) -> LangChainSync:
    """One-line LangChain integration with RAGVersion.

    This function handles all setup automatically:
    - Creates and initializes RAGVersion tracker
    - Sets up LangChain components (embeddings, text splitter, vectorstore)
    - Creates LangChainSync integration
    - Syncs the directory

    **Before (35 lines):**
    ```python
    storage = SupabaseStorage.from_env()
    tracker = AsyncVersionTracker(storage=storage, store_content=True)
    await tracker.initialize()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(["placeholder"], embeddings)
    sync = LangChainSync(tracker, text_splitter, embeddings, vectorstore)
    await sync.sync_directory("./documents")
    ```

    **After (3 lines):**
    ```python
    from ragversion.integrations.langchain import quick_start
    sync = await quick_start("./documents")
    # Done! Documents tracked and synced to vector store
    ```

    Args:
        directory: Directory to track and sync
        vectorstore_type: Vector store type ("faiss" or "chroma")
            - "faiss": In-memory FAISS index (fast, ephemeral unless saved)
            - "chroma": Persistent Chroma database
        vectorstore_path: Path for persistent storage (optional)
            - For FAISS: Load existing index or save location
            - For Chroma: Database directory (default: "./chroma_db")
        embeddings: Custom embeddings model (default: OpenAIEmbeddings from env)
        storage_backend: RAGVersion storage backend
            - "auto": Auto-detect from environment (default)
            - "sqlite": Use local SQLite database
            - "supabase": Use Supabase (requires SUPABASE_URL and SUPABASE_SERVICE_KEY)
        chunk_size: Text splitter chunk size (default: 1000 chars)
        chunk_overlap: Text splitter overlap (default: 200 chars)
        file_patterns: File patterns to track (default: ["*.txt", "*.md", "*.pdf"])
        enable_chunk_tracking: Enable smart chunk-level tracking (default: True)
            - Reduces embedding costs by 80-95% on document updates
            - Only re-embeds changed chunks instead of full documents

    Returns:
        Initialized LangChainSync instance with documents already synced

    Raises:
        ImportError: If LangChain is not installed
        ValueError: If invalid vectorstore_type is specified
        StorageError: If storage backend initialization fails

    Example:
        >>> # Simplest usage - just specify directory
        >>> sync = await quick_start("./documents")
        >>>
        >>> # Custom vectorstore path
        >>> sync = await quick_start(
        ...     "./documents",
        ...     vectorstore_path="./my_vectorstore"
        ... )
        >>>
        >>> # With Chroma (persistent)
        >>> sync = await quick_start(
        ...     "./documents",
        ...     vectorstore_type="chroma",
        ...     vectorstore_path="./chroma_db"
        ... )
        >>>
        >>> # Disable chunk tracking (full re-embedding on updates)
        >>> sync = await quick_start(
        ...     "./documents",
        ...     enable_chunk_tracking=False
        ... )
        >>>
        >>> # After setup, the vectorstore is ready to use
        >>> results = await sync.vectorstore.asimilarity_search("query", k=5)
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain is not installed. Install with: pip install ragversion[langchain]"
        )

    if file_patterns is None:
        file_patterns = ["*.txt", "*.md", "*.pdf"]

    # Step 1: Create tracker with smart defaults
    logger.info("Creating RAGVersion tracker...")
    tracker = await create_tracker_from_config(
        storage_backend=storage_backend,
        store_content=True,
        enable_chunk_tracking=enable_chunk_tracking,
    )

    # Step 2: Create embeddings (default: OpenAI from env)
    if embeddings is None:
        logger.info("Creating OpenAI embeddings (requires OPENAI_API_KEY env var)...")
        embeddings = OpenAIEmbeddings()

    # Step 3: Create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Step 4: Create vectorstore
    logger.info(f"Creating {vectorstore_type} vectorstore...")
    vectorstore = _create_vectorstore(
        vectorstore_type=vectorstore_type,
        embeddings=embeddings,
        vectorstore_path=vectorstore_path,
    )

    # Step 5: Create sync integration
    logger.info("Creating LangChain sync integration...")
    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore,
        enable_chunk_tracking=enable_chunk_tracking,
    )

    # Step 6: Sync directory
    logger.info(f"Syncing directory: {directory}")
    await sync.sync_directory(
        directory,
        patterns=file_patterns,
        recursive=True,
    )

    logger.info("✓ LangChain integration ready!")
    return sync


def _create_vectorstore(
    vectorstore_type: str,
    embeddings: Embeddings,
    vectorstore_path: Optional[str],
) -> Any:
    """Create vectorstore based on type.

    Args:
        vectorstore_type: Type of vectorstore ("faiss" or "chroma")
        embeddings: Embeddings model to use
        vectorstore_path: Optional path for persistent storage

    Returns:
        Initialized vectorstore instance

    Raises:
        ValueError: If unknown vectorstore type is specified
    """
    if vectorstore_type == "faiss":
        if vectorstore_path and Path(vectorstore_path).exists():
            # Load existing FAISS index
            logger.info(f"Loading existing FAISS index from: {vectorstore_path}")
            return FAISS.load_local(
                vectorstore_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            # Create new in-memory FAISS index
            # Note: Use a placeholder document to initialize
            logger.info("Creating new in-memory FAISS index")
            return FAISS.from_texts(["placeholder"], embeddings)

    elif vectorstore_type == "chroma":
        # Chroma is always persistent
        persist_dir = vectorstore_path or "./chroma_db"
        logger.info(f"Creating Chroma database at: {persist_dir}")
        return Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
        )

    else:
        raise ValueError(
            f"Unknown vectorstore type: {vectorstore_type}. "
            "Valid options: 'faiss', 'chroma'"
        )

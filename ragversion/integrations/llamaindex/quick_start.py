"""Quick start utilities for LlamaIndex integration.

This module provides a one-line setup for LlamaIndex integration,
dramatically reducing boilerplate code from ~20 lines to just 3 lines.
"""

import logging
import os
from typing import Any, List, Literal, Optional

try:
    from llama_index.core import VectorStoreIndex
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.core.embeddings import BaseEmbedding
    from llama_index.core.node_parser import NodeParser

    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    VectorStoreIndex = Any
    SentenceSplitter = Any
    OpenAIEmbedding = Any
    BaseEmbedding = Any
    NodeParser = Any

from ragversion.quick_start import create_tracker_from_config
from ragversion.integrations.llamaindex.sync import LlamaIndexSync

logger = logging.getLogger(__name__)


def _is_package_installed(package_name: str) -> bool:
    """Check if a package is installed without importing it."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def _create_embeddings(provider: Literal["auto", "openai", "huggingface", "ollama"]) -> BaseEmbedding:
    """Auto-detect or create embeddings based on provider.

    Args:
        provider: Embedding provider to use ("auto", "openai", "huggingface", or "ollama")

    Returns:
        Initialized embeddings instance

    Raises:
        ValueError: If provider is unknown or no provider is available
        ImportError: If required package for provider is not installed
    """
    if provider == "auto":
        # Try OpenAI first (if API key is set)
        if os.getenv("OPENAI_API_KEY"):
            try:
                from llama_index.embeddings.openai import OpenAIEmbedding
                logger.info("Auto-detected OpenAI embeddings (OPENAI_API_KEY found)")
                return OpenAIEmbedding(model="text-embedding-3-small")
            except ImportError:
                logger.debug("OpenAI API key found but llama-index-embeddings-openai not installed")

        # Try HuggingFace (if sentence-transformers is installed)
        if _is_package_installed("sentence_transformers"):
            try:
                from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                logger.info("Auto-detected HuggingFace embeddings (sentence-transformers installed)")
                return HuggingFaceEmbedding(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            except ImportError:
                logger.debug("sentence-transformers found but llama-index-embeddings-huggingface not installed")

        # Try Ollama (if ollama package is installed)
        if _is_package_installed("ollama"):
            try:
                from llama_index.embeddings.ollama import OllamaEmbedding
                logger.info("Auto-detected Ollama embeddings (ollama installed)")
                return OllamaEmbedding(model_name="llama2")
            except ImportError:
                logger.debug("ollama found but llama-index-embeddings-ollama not installed")

        # Nothing available
        raise ValueError(
            "No embeddings provider available. Please choose one:\n\n"
            "Option 1 - OpenAI (paid, best quality):\n"
            "  export OPENAI_API_KEY='sk-...'\n"
            "  pip install llama-index-embeddings-openai\n\n"
            "Option 2 - HuggingFace (free, local):\n"
            "  pip install llama-index-embeddings-huggingface sentence-transformers\n\n"
            "Option 3 - Ollama (free, local):\n"
            "  pip install llama-index-embeddings-ollama ollama\n\n"
            "Or provide your own: embeddings=YourEmbedding()\n"
            "See: https://docs.ragversion.com/embeddings"
        )

    elif provider == "openai":
        try:
            from llama_index.embeddings.openai import OpenAIEmbedding
            return OpenAIEmbedding(model="text-embedding-3-small")
        except ImportError:
            raise ImportError(
                "OpenAI embeddings require llama-index-embeddings-openai. Install with:\n"
                "  pip install llama-index-embeddings-openai"
            )

    elif provider == "huggingface":
        try:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            return HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        except ImportError:
            raise ImportError(
                "HuggingFace embeddings require llama-index-embeddings-huggingface. Install with:\n"
                "  pip install llama-index-embeddings-huggingface sentence-transformers"
            )

    elif provider == "ollama":
        try:
            from llama_index.embeddings.ollama import OllamaEmbedding
            return OllamaEmbedding(model_name="llama2")
        except ImportError:
            raise ImportError(
                "Ollama embeddings require llama-index-embeddings-ollama. Install with:\n"
                "  pip install llama-index-embeddings-ollama ollama"
            )

    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. "
            f"Valid options: 'auto', 'openai', 'huggingface', 'ollama'"
        )


async def quick_start(
    directory: str,
    index_path: Optional[str] = None,
    embedding_provider: Literal["auto", "openai", "huggingface", "ollama"] = "auto",
    embeddings: Optional[BaseEmbedding] = None,
    storage_backend: Literal["sqlite", "supabase", "auto"] = "auto",
    chunk_size: int = 1024,
    chunk_overlap: int = 20,
    file_patterns: Optional[List[str]] = None,
    enable_chunk_tracking: bool = True,
) -> LlamaIndexSync:
    """One-line LlamaIndex integration with RAGVersion.

    This function handles all setup automatically:
    - Creates and initializes RAGVersion tracker
    - Sets up LlamaIndex components (embeddings, node parser, index)
    - Creates LlamaIndexSync integration
    - Syncs the directory

    **Before (20 lines):**
    ```python
    storage = SupabaseStorage.from_env()
    tracker = AsyncVersionTracker(storage=storage, store_content=True)
    await tracker.initialize()
    embeddings = OpenAIEmbedding()
    node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
    index = VectorStoreIndex.from_documents([], embed_model=embeddings)
    sync = LlamaIndexSync(tracker, index, node_parser)
    await sync.sync_directory("./documents")
    ```

    **After (3 lines):**
    ```python
    from ragversion.integrations.llamaindex import quick_start
    sync = await quick_start("./documents")
    # Done! Documents tracked and synced to index
    ```

    Args:
        directory: Directory to track and sync
        index_path: Path for persistent index storage (optional, reserved for future use)
        embedding_provider: Embedding provider to use (default: "auto")
            - "auto": Auto-detect (tries OpenAI → HuggingFace → Ollama)
            - "openai": OpenAI embeddings (requires OPENAI_API_KEY and llama-index-embeddings-openai)
            - "huggingface": HuggingFace local embeddings (requires llama-index-embeddings-huggingface)
            - "ollama": Ollama local embeddings (requires llama-index-embeddings-ollama)
        embeddings: Custom embeddings model (overrides embedding_provider if provided)
        storage_backend: RAGVersion storage backend
            - "auto": Auto-detect from environment (default)
            - "sqlite": Use local SQLite database
            - "supabase": Use Supabase (requires SUPABASE_URL and SUPABASE_SERVICE_KEY)
        chunk_size: Node parser chunk size (default: 1024 chars)
        chunk_overlap: Node parser overlap (default: 20 chars)
        file_patterns: File patterns to track (default: ["*.txt", "*.md", "*.pdf"])
        enable_chunk_tracking: Enable smart chunk-level tracking (default: True)
            - Reduces embedding costs by 80-95% on document updates
            - Only re-embeds changed chunks instead of full documents

    Returns:
        Initialized LlamaIndexSync instance with documents already synced

    Raises:
        ImportError: If LlamaIndex is not installed
        StorageError: If storage backend initialization fails

    Example:
        >>> # Simplest usage - just specify directory
        >>> sync = await quick_start("./documents")
        >>>
        >>> # Disable chunk tracking (full re-embedding on updates)
        >>> sync = await quick_start(
        ...     "./documents",
        ...     enable_chunk_tracking=False
        ... )
        >>>
        >>> # Custom chunk size for larger documents
        >>> sync = await quick_start(
        ...     "./documents",
        ...     chunk_size=2048,
        ...     chunk_overlap=200
        ... )
        >>>
        >>> # After setup, the index is ready to use
        >>> query_engine = sync.index.as_query_engine()
        >>> response = query_engine.query("What changed today?")
    """
    if not LLAMAINDEX_AVAILABLE:
        raise ImportError(
            "LlamaIndex is not installed. Install with: pip install ragversion[llamaindex]"
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

    # Step 2: Create embeddings (auto-detect or use specified provider)
    if embeddings is None:
        logger.info(f"Creating embeddings with provider: {embedding_provider}")
        embeddings = _create_embeddings(embedding_provider)

    # Step 3: Create node parser
    node_parser = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Step 4: Create index
    logger.info("Creating VectorStoreIndex...")
    # Note: index_path reserved for future persistence support
    if index_path:
        logger.warning("index_path parameter is reserved for future use (persistence not yet implemented)")

    # Create in-memory index
    index = VectorStoreIndex.from_documents([], embed_model=embeddings)

    # Step 5: Create sync integration
    logger.info("Creating LlamaIndex sync integration...")
    sync = LlamaIndexSync(
        tracker=tracker,
        index=index,
        node_parser=node_parser,
        enable_chunk_tracking=enable_chunk_tracking,
    )

    # Step 6: Sync directory
    logger.info(f"Syncing directory: {directory}")
    await sync.sync_directory(
        directory,
        patterns=file_patterns,
        recursive=True,
    )

    logger.info("✓ LlamaIndex integration ready!")
    return sync

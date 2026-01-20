"""LangChain integration for RAGVersion."""

import logging
from typing import Any, List, Optional

try:
    from langchain_core.documents import Document as LCDocument
    from langchain_text_splitters import TextSplitter
    from langchain_core.vectorstores import VectorStore
    from langchain_core.embeddings import Embeddings

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LCDocument = Any
    TextSplitter = Any
    VectorStore = Any
    Embeddings = Any

from ragversion.models import ChangeEvent, ChangeType
from ragversion.tracker import AsyncVersionTracker

logger = logging.getLogger(__name__)


class LangChainSync:
    """
    LangChain integration for RAGVersion.

    Automatically syncs document changes to LangChain vector stores.
    """

    def __init__(
        self,
        tracker: AsyncVersionTracker,
        text_splitter: TextSplitter,
        embeddings: Embeddings,
        vectorstore: VectorStore,
        metadata_extractor: Optional[callable] = None,
        enable_chunk_tracking: bool = False,
    ):
        """
        Initialize LangChain sync.

        Args:
            tracker: AsyncVersionTracker instance
            text_splitter: LangChain text splitter
            embeddings: LangChain embeddings
            vectorstore: LangChain vector store
            metadata_extractor: Optional function to extract metadata from file path
            enable_chunk_tracking: Enable smart chunk-level updates (v0.10.0)
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. Install with: pip install ragversion[langchain]"
            )

        self.tracker = tracker
        self.text_splitter = text_splitter
        self.embeddings = embeddings
        self.vectorstore = vectorstore
        self.metadata_extractor = metadata_extractor
        self.enable_chunk_tracking = enable_chunk_tracking

        # Verify chunk tracking compatibility
        if self.enable_chunk_tracking and not self.tracker.chunk_tracking_enabled:
            logger.warning(
                "Chunk tracking enabled in LangChainSync but disabled in tracker. "
                "Falling back to full document re-embedding."
            )
            self.enable_chunk_tracking = False

        # Register change callback
        self.tracker.on_change(self._handle_change)

    async def _handle_change(self, event: ChangeEvent) -> None:
        """Handle document change events."""
        try:
            if event.change_type == ChangeType.CREATED:
                await self._handle_creation(event)
            elif event.change_type == ChangeType.MODIFIED:
                await self._handle_modification(event)
            elif event.change_type == ChangeType.DELETED:
                await self._handle_deletion(event)
            elif event.change_type == ChangeType.RESTORED:
                await self._handle_restoration(event)

        except Exception as e:
            logger.error(f"Failed to sync change to LangChain: {e}")

    async def _handle_creation(self, event: ChangeEvent) -> None:
        """Handle document creation."""
        # Get content
        content = await self.tracker.get_content(event.version_id)
        if not content:
            logger.warning(f"No content for version {event.version_id}")
            return

        # Split text
        texts = self.text_splitter.split_text(content)

        # Create metadata
        metadata = {
            "document_id": str(event.document_id),
            "version_id": str(event.version_id),
            "version_number": event.version_number,
            "file_path": event.file_path,
            "file_name": event.file_name,
            "content_hash": event.content_hash,
        }

        # Add custom metadata
        if self.metadata_extractor:
            custom_metadata = self.metadata_extractor(event.file_path)
            metadata.update(custom_metadata)

        # Create LangChain documents
        documents = [
            LCDocument(page_content=text, metadata=metadata) for text in texts
        ]

        # Add to vector store
        await self.vectorstore.aadd_documents(documents)

        logger.info(f"Added {len(documents)} chunks to vector store for {event.file_name}")

    async def _handle_modification(self, event: ChangeEvent) -> None:
        """Handle document modification with optional chunk-level updates."""
        if self.enable_chunk_tracking:
            await self._handle_modification_smart(event)
        else:
            # Legacy: delete all + re-add all
            await self._delete_document(event.document_id)
            await self._handle_creation(event)
            logger.info(f"Updated vector store for {event.file_name}")

    async def _handle_modification_smart(self, event: ChangeEvent) -> None:
        """Handle modification using smart chunk-level updates (v0.10.0).

        This method uses chunk diffs to only re-embed changed chunks,
        achieving 80-95% cost savings compared to full re-embedding.
        """
        try:
            # Get chunk diff
            chunk_diff = await self.tracker.get_chunk_diff(
                event.document_id,
                event.version_number - 1,
                event.version_number,
            )

            if not chunk_diff:
                # Fallback to legacy mode if chunk diff unavailable
                logger.debug("Chunk diff unavailable, falling back to full re-embedding")
                await self._delete_document(event.document_id)
                await self._handle_creation(event)
                return

            # Delete removed chunks
            for removed_chunk in chunk_diff.removed_chunks:
                try:
                    self.vectorstore.delete(filter={
                        "document_id": str(event.document_id),
                        "chunk_id": str(removed_chunk.id),
                    })
                except Exception as e:
                    logger.warning(f"Could not delete chunk {removed_chunk.id}: {e}")

            # Prepare metadata base
            base_metadata = {
                "document_id": str(event.document_id),
                "version_id": str(event.version_id),
                "version_number": event.version_number,
                "file_path": event.file_path,
                "file_name": event.file_name,
                "content_hash": event.content_hash,
            }

            # Add custom metadata
            if self.metadata_extractor:
                custom_metadata = self.metadata_extractor(event.file_path)
                base_metadata.update(custom_metadata)

            # Embed only new chunks
            chunks_to_embed = []
            for added_chunk in chunk_diff.added_chunks:
                content = await self.tracker.storage.get_chunk_content(added_chunk.id)
                if content:
                    metadata = base_metadata.copy()
                    metadata.update({
                        "chunk_id": str(added_chunk.id),
                        "chunk_index": added_chunk.chunk_index,
                        "chunk_hash": added_chunk.content_hash,
                        "token_count": added_chunk.token_count,
                    })
                    chunks_to_embed.append(LCDocument(page_content=content, metadata=metadata))

            # Add to vector store
            if chunks_to_embed:
                await self.vectorstore.aadd_documents(chunks_to_embed)

            # Log savings
            savings_pct = chunk_diff.savings_percentage
            total_chunks = chunk_diff.total_chunks
            embedded_count = len(chunks_to_embed)

            logger.info(
                f"Smart update for {event.file_name}: "
                f"Embedded {embedded_count}/{total_chunks} chunks "
                f"(saved {savings_pct:.1f}% embedding cost)"
            )

        except Exception as e:
            logger.error(f"Smart chunk update failed: {e}, falling back to full re-embedding")
            # Fallback to legacy mode on error
            await self._delete_document(event.document_id)
            await self._handle_creation(event)

    async def _handle_deletion(self, event: ChangeEvent) -> None:
        """Handle document deletion."""
        await self._delete_document(event.document_id)
        logger.info(f"Deleted {event.file_name} from vector store")

    async def _handle_restoration(self, event: ChangeEvent) -> None:
        """Handle document restoration."""
        # Same as modification
        await self._handle_modification(event)

    async def _delete_document(self, document_id: str) -> None:
        """Delete document from vector store."""
        # Note: This requires vector store to support deletion by metadata
        # Not all vector stores support this - may need custom implementation
        try:
            # Try to delete by metadata filter
            self.vectorstore.delete(filter={"document_id": str(document_id)})
        except Exception as e:
            logger.warning(f"Could not delete document {document_id}: {e}")

    async def sync_directory(
        self,
        dir_path: str,
        patterns: Optional[List[str]] = None,
        recursive: bool = True,
        max_workers: int = 4,
    ) -> None:
        """
        Sync all files in a directory to vector store.

        Args:
            dir_path: Path to directory
            patterns: File patterns to match
            recursive: Whether to search recursively
            max_workers: Number of parallel workers
        """
        result = await self.tracker.track_directory(
            dir_path,
            patterns=patterns,
            recursive=recursive,
            max_workers=max_workers,
        )

        logger.info(
            f"Synced {result.success_count}/{result.total_files} documents to LangChain"
        )

        if result.failed:
            logger.warning(f"Failed to sync {result.failure_count} documents")


class LangChainLoader:
    """
    Load documents from RAGVersion into LangChain.

    Useful for one-time migrations or rebuilding indexes.
    """

    def __init__(self, tracker: AsyncVersionTracker):
        """
        Initialize LangChain loader.

        Args:
            tracker: AsyncVersionTracker instance
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. Install with: pip install ragversion[langchain]"
            )

        self.tracker = tracker

    async def load_documents(
        self,
        document_ids: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> List[LCDocument]:
        """
        Load documents as LangChain documents.

        Args:
            document_ids: Optional list of document IDs to load
            limit: Maximum number of documents to load

        Returns:
            List of LangChain documents
        """
        lc_documents = []

        # Get documents
        if document_ids:
            # Load specific documents
            from uuid import UUID

            for doc_id in document_ids:
                doc = await self.tracker.get_document(UUID(doc_id))
                if doc:
                    # Get latest version content
                    latest_version = await self.tracker.get_latest_version(doc.id)
                    if latest_version:
                        content = await self.tracker.get_content(latest_version.id)
                        if content:
                            metadata = {
                                "document_id": str(doc.id),
                                "version_id": str(latest_version.id),
                                "version_number": latest_version.version_number,
                                "file_path": doc.file_path,
                                "file_name": doc.file_name,
                            }
                            lc_documents.append(
                                LCDocument(page_content=content, metadata=metadata)
                            )
        else:
            # Load all documents
            documents = await self.tracker.list_documents(limit=limit)

            for doc in documents:
                # Get latest version content
                latest_version = await self.tracker.get_latest_version(doc.id)
                if latest_version:
                    content = await self.tracker.get_content(latest_version.id)
                    if content:
                        metadata = {
                            "document_id": str(doc.id),
                            "version_id": str(latest_version.id),
                            "version_number": latest_version.version_number,
                            "file_path": doc.file_path,
                            "file_name": doc.file_name,
                        }
                        lc_documents.append(
                            LCDocument(page_content=content, metadata=metadata)
                        )

        return lc_documents

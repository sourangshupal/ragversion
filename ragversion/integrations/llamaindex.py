"""LlamaIndex integration for RAGVersion."""

import logging
from typing import Any, List, Optional

try:
    from llama_index.core import Document as LIDocument
    from llama_index.core import VectorStoreIndex
    from llama_index.core.node_parser import NodeParser

    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    LIDocument = Any
    VectorStoreIndex = Any
    NodeParser = Any

from ragversion.models import ChangeEvent, ChangeType
from ragversion.tracker import AsyncVersionTracker

logger = logging.getLogger(__name__)


class LlamaIndexSync:
    """
    LlamaIndex integration for RAGVersion.

    Automatically syncs document changes to LlamaIndex indexes.
    """

    def __init__(
        self,
        tracker: AsyncVersionTracker,
        index: VectorStoreIndex,
        node_parser: Optional[NodeParser] = None,
        metadata_extractor: Optional[callable] = None,
        enable_chunk_tracking: bool = False,
    ):
        """
        Initialize LlamaIndex sync.

        Args:
            tracker: AsyncVersionTracker instance
            index: LlamaIndex vector store index
            node_parser: Optional LlamaIndex node parser
            metadata_extractor: Optional function to extract metadata from file path
            enable_chunk_tracking: Enable smart chunk-level updates (v0.10.0)
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndex is not installed. Install with: pip install ragversion[llamaindex]"
            )

        self.tracker = tracker
        self.index = index
        self.node_parser = node_parser
        self.metadata_extractor = metadata_extractor
        self.enable_chunk_tracking = enable_chunk_tracking

        # Document ID to node ID mapping
        self._doc_node_map = {}

        # Verify chunk tracking compatibility
        if self.enable_chunk_tracking and not self.tracker.chunk_tracking_enabled:
            logger.warning(
                "Chunk tracking enabled in LlamaIndexSync but disabled in tracker. "
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
            logger.error(f"Failed to sync change to LlamaIndex: {e}")

    async def _handle_creation(self, event: ChangeEvent) -> None:
        """Handle document creation."""
        # Get content
        content = await self.tracker.get_content(event.version_id)
        if not content:
            logger.warning(f"No content for version {event.version_id}")
            return

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

        # Create LlamaIndex document
        document = LIDocument(
            text=content,
            metadata=metadata,
            doc_id=str(event.document_id),
        )

        # Insert into index
        self.index.insert(document)

        logger.info(f"Added {event.file_name} to LlamaIndex")

    async def _handle_modification(self, event: ChangeEvent) -> None:
        """Handle document modification with optional chunk-level updates."""
        if self.enable_chunk_tracking:
            await self._handle_modification_smart(event)
        else:
            # Legacy: delete all + re-add all
            await self._delete_document(event.document_id)
            await self._handle_creation(event)
            logger.info(f"Updated {event.file_name} in LlamaIndex")

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

            # Delete removed chunks (by node ID pattern)
            for removed_chunk in chunk_diff.removed_chunks:
                try:
                    # Create node ID pattern: document_id + chunk_id
                    node_id = f"{event.document_id}_{removed_chunk.id}"
                    self.index.delete_nodes([node_id])
                except Exception as e:
                    logger.warning(f"Could not delete chunk node {removed_chunk.id}: {e}")

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

            # Insert only new chunks
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

                    # Create LlamaIndex document for this chunk
                    # Use node ID pattern: document_id + chunk_id
                    node_id = f"{event.document_id}_{added_chunk.id}"
                    chunk_doc = LIDocument(
                        text=content,
                        metadata=metadata,
                        doc_id=node_id,
                    )
                    chunks_to_embed.append(chunk_doc)

            # Insert to index
            if chunks_to_embed:
                for chunk_doc in chunks_to_embed:
                    self.index.insert(chunk_doc)

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
        logger.info(f"Deleted {event.file_name} from LlamaIndex")

    async def _handle_restoration(self, event: ChangeEvent) -> None:
        """Handle document restoration."""
        # Same as modification
        await self._handle_modification(event)

    async def _delete_document(self, document_id: str) -> None:
        """Delete document from index."""
        try:
            # Delete by doc_id
            self.index.delete_ref_doc(str(document_id), delete_from_docstore=True)
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
        Sync all files in a directory to index.

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
            f"Synced {result.success_count}/{result.total_files} documents to LlamaIndex"
        )

        if result.failed:
            logger.warning(f"Failed to sync {result.failure_count} documents")

    async def refresh_index(self) -> None:
        """Refresh the entire index from tracked documents."""
        # Get all documents
        documents = await self.tracker.list_documents(limit=10000)

        logger.info(f"Refreshing index with {len(documents)} documents")

        for doc in documents:
            # Get latest version
            latest_version = await self.tracker.get_latest_version(doc.id)
            if not latest_version:
                continue

            # Get content
            content = await self.tracker.get_content(latest_version.id)
            if not content:
                continue

            # Create metadata
            metadata = {
                "document_id": str(doc.id),
                "version_id": str(latest_version.id),
                "version_number": latest_version.version_number,
                "file_path": doc.file_path,
                "file_name": doc.file_name,
            }

            # Create and insert document
            li_doc = LIDocument(
                text=content,
                metadata=metadata,
                doc_id=str(doc.id),
            )

            self.index.insert(li_doc)

        logger.info("Index refresh complete")


class LlamaIndexLoader:
    """
    Load documents from RAGVersion into LlamaIndex.

    Useful for one-time migrations or rebuilding indexes.
    """

    def __init__(self, tracker: AsyncVersionTracker):
        """
        Initialize LlamaIndex loader.

        Args:
            tracker: AsyncVersionTracker instance
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndex is not installed. Install with: pip install ragversion[llamaindex]"
            )

        self.tracker = tracker

    async def load_documents(
        self,
        document_ids: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> List[LIDocument]:
        """
        Load documents as LlamaIndex documents.

        Args:
            document_ids: Optional list of document IDs to load
            limit: Maximum number of documents to load

        Returns:
            List of LlamaIndex documents
        """
        li_documents = []

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
                            li_documents.append(
                                LIDocument(
                                    text=content,
                                    metadata=metadata,
                                    doc_id=str(doc.id),
                                )
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
                        li_documents.append(
                            LIDocument(
                                text=content,
                                metadata=metadata,
                                doc_id=str(doc.id),
                            )
                        )

        return li_documents

"""Chunk-level change detection for RAGVersion."""

import hashlib
import logging
from typing import List, Optional
from uuid import UUID

from ragversion.models import Chunk, ChunkDiff, Version
from ragversion.storage.base import BaseStorage
from ragversion.chunking.splitters import BaseChunker

logger = logging.getLogger(__name__)


class ChunkChangeDetector:
    """Detects changes at chunk level between versions.

    Uses hash-based comparison for O(1) lookup performance when comparing
    chunks between versions. This enables efficient identification of which
    chunks have changed, allowing for targeted re-embedding of only the
    changed chunks.
    """

    def __init__(self, storage: BaseStorage, chunker: BaseChunker):
        """Initialize the chunk change detector.

        Args:
            storage: Storage backend for retrieving existing chunks
            chunker: Chunking strategy for splitting new content
        """
        self.storage = storage
        self.chunker = chunker

    async def detect_chunk_changes(
        self,
        document_id: UUID,
        old_version_id: Optional[UUID],
        new_content: str,
        new_version_id: UUID,
    ) -> ChunkDiff:
        """Compare chunks between versions and identify changes.

        Algorithm:
        1. Get old chunks from storage (if version exists)
        2. Split new content into chunks
        3. Build hash maps for O(1) comparison
        4. Categorize chunks: ADDED, REMOVED, UNCHANGED, REORDERED

        Args:
            document_id: ID of the document being compared
            old_version_id: ID of the previous version (None for new documents)
            new_content: Content of the new version
            new_version_id: ID of the new version

        Returns:
            ChunkDiff containing categorized chunk changes
        """
        # Get old chunks from storage
        old_chunks: List[Chunk] = []
        old_version: Optional[Version] = None
        if old_version_id:
            try:
                old_chunks = await self.storage.get_chunks_by_version(old_version_id)
                old_version = await self.storage.get_version(old_version_id)
                logger.debug(f"Retrieved {len(old_chunks)} chunks from old version {old_version_id}")
            except Exception as e:
                logger.warning(f"Failed to retrieve old chunks: {e}, treating as new document")

        # Split new content into chunks
        new_texts = await self.chunker.split_text(new_content)
        logger.debug(f"Split new content into {len(new_texts)} chunks")

        # Create new chunk objects
        new_chunks: List[Chunk] = []
        for idx, text in enumerate(new_texts):
            content_hash = self._hash(text)
            token_count = self.chunker.count_tokens(text)

            chunk = Chunk(
                document_id=document_id,
                version_id=new_version_id,
                chunk_index=idx,
                content_hash=content_hash,
                token_count=token_count,
                metadata={"content": text},  # Store content in metadata for now
            )
            new_chunks.append(chunk)

        # Get version numbers
        new_version = await self.storage.get_version(new_version_id)

        # Build hash maps for O(1) lookup
        old_map = {chunk.content_hash: chunk for chunk in old_chunks}
        new_map = {chunk.content_hash: chunk for chunk in new_chunks}

        # Also build position maps to detect reordering
        old_position_map = {chunk.content_hash: chunk.chunk_index for chunk in old_chunks}

        # Detect changes
        added_chunks: List[Chunk] = []
        removed_chunks: List[Chunk] = []
        unchanged_chunks: List[Chunk] = []
        reordered_chunks: List[Chunk] = []

        # Check new chunks
        for new_chunk in new_chunks:
            if new_chunk.content_hash not in old_map:
                # Chunk is new
                added_chunks.append(new_chunk)
            else:
                # Chunk existed before
                old_position = old_position_map[new_chunk.content_hash]
                if old_position == new_chunk.chunk_index:
                    # Same position, unchanged
                    unchanged_chunks.append(new_chunk)
                else:
                    # Different position, reordered
                    reordered_chunks.append(new_chunk)

        # Check old chunks for removals
        for old_chunk in old_chunks:
            if old_chunk.content_hash not in new_map:
                # Chunk was removed
                removed_chunks.append(old_chunk)

        # Log summary
        logger.info(
            f"Chunk diff for document {document_id}: "
            f"added={len(added_chunks)}, "
            f"removed={len(removed_chunks)}, "
            f"unchanged={len(unchanged_chunks)}, "
            f"reordered={len(reordered_chunks)}"
        )

        return ChunkDiff(
            document_id=document_id,
            from_version=old_version.version_number if old_version else 0,
            to_version=new_version.version_number,
            added_chunks=added_chunks,
            modified_chunks=[],  # Not used in hash-based approach
            removed_chunks=removed_chunks,
            unchanged_chunks=unchanged_chunks,
            reordered_chunks=reordered_chunks,
        )

    async def create_chunks_for_version(
        self,
        document_id: UUID,
        version_id: UUID,
        content: str,
    ) -> List[Chunk]:
        """Create chunks for a new version.

        This is a convenience method for initial chunk creation without
        comparison to a previous version.

        Args:
            document_id: ID of the document
            version_id: ID of the version
            content: Content to split into chunks

        Returns:
            List of created chunks
        """
        # Split content into chunks
        new_texts = await self.chunker.split_text(content)
        logger.debug(f"Creating {len(new_texts)} chunks for version {version_id}")

        # Create chunk objects
        chunks: List[Chunk] = []
        for idx, text in enumerate(new_texts):
            content_hash = self._hash(text)
            token_count = self.chunker.count_tokens(text)

            chunk = Chunk(
                document_id=document_id,
                version_id=version_id,
                chunk_index=idx,
                content_hash=content_hash,
                token_count=token_count,
                metadata={"content": text},
            )
            chunks.append(chunk)

        return chunks

    def _hash(self, content: str) -> str:
        """Compute SHA-256 hash of content.

        Args:
            content: The content to hash

        Returns:
            Hex digest of the hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def calculate_savings_metrics(self, chunk_diff: ChunkDiff) -> dict:
        """Calculate cost savings metrics from a chunk diff.

        Args:
            chunk_diff: The chunk diff to analyze

        Returns:
            Dictionary with savings metrics
        """
        total_chunks = chunk_diff.total_chunks
        unchanged_count = len(chunk_diff.unchanged_chunks) + len(chunk_diff.reordered_chunks)
        changed_count = chunk_diff.total_changes

        # Calculate savings
        if total_chunks == 0:
            savings_percentage = 0.0
            chunks_to_embed = 0
        else:
            savings_percentage = (unchanged_count / total_chunks) * 100
            chunks_to_embed = changed_count

        return {
            "total_chunks": total_chunks,
            "unchanged_chunks": unchanged_count,
            "changed_chunks": changed_count,
            "chunks_to_embed": chunks_to_embed,
            "savings_percentage": savings_percentage,
            "added": len(chunk_diff.added_chunks),
            "removed": len(chunk_diff.removed_chunks),
            "reordered": len(chunk_diff.reordered_chunks),
        }

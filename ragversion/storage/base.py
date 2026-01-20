"""Abstract base class for storage backends."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ragversion.models import Document, Version, DiffResult, StorageStatistics, DocumentStatistics, Chunk


class BaseStorage(ABC):
    """Abstract base class for async storage backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend (create tables, run migrations, etc.)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections and cleanup resources."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the storage backend is healthy and accessible."""
        pass

    # Document operations

    async def batch_create_documents(self, documents: List[Document]) -> List[Document]:
        """Create multiple document records (optimized in subclasses).

        Default implementation calls create_document for each document.
        Subclasses should override this for better performance.
        """
        results = []
        for doc in documents:
            results.append(await self.create_document(doc))
        return results

    @abstractmethod
    async def create_document(self, document: Document) -> Document:
        """Create a new document record."""
        pass

    @abstractmethod
    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        pass

    @abstractmethod
    async def get_document_by_path(self, file_path: str) -> Optional[Document]:
        """Get a document by file path."""
        pass

    @abstractmethod
    async def update_document(self, document: Document) -> Document:
        """Update an existing document."""
        pass

    @abstractmethod
    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document and all its versions."""
        pass

    @abstractmethod
    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "updated_at",
    ) -> List[Document]:
        """List documents with pagination."""
        pass

    @abstractmethod
    async def search_documents(
        self,
        metadata_filter: Optional[dict] = None,
        file_type: Optional[str] = None,
    ) -> List[Document]:
        """Search documents by metadata or file type."""
        pass

    # Version operations

    async def batch_create_versions(self, versions: List[Version]) -> List[Version]:
        """Create multiple version records (optimized in subclasses).

        Default implementation calls create_version for each version.
        Subclasses should override this for better performance.
        """
        results = []
        for ver in versions:
            results.append(await self.create_version(ver))
        return results

    @abstractmethod
    async def create_version(self, version: Version) -> Version:
        """Create a new version record."""
        pass

    @abstractmethod
    async def get_version(self, version_id: UUID) -> Optional[Version]:
        """Get a version by ID."""
        pass

    @abstractmethod
    async def get_version_by_number(
        self, document_id: UUID, version_number: int
    ) -> Optional[Version]:
        """Get a specific version of a document."""
        pass

    @abstractmethod
    async def list_versions(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Version]:
        """List all versions of a document."""
        pass

    @abstractmethod
    async def delete_version(self, version_id: UUID) -> None:
        """Delete a specific version."""
        pass

    @abstractmethod
    async def get_latest_version(self, document_id: UUID) -> Optional[Version]:
        """Get the latest version of a document."""
        pass

    # Content operations

    @abstractmethod
    async def store_content(
        self,
        version_id: UUID,
        content: str,
        compress: bool = True,
    ) -> None:
        """Store version content (optionally compressed)."""
        pass

    @abstractmethod
    async def get_content(self, version_id: UUID) -> Optional[str]:
        """Retrieve version content (automatically decompressed)."""
        pass

    @abstractmethod
    async def delete_content(self, version_id: UUID) -> None:
        """Delete stored content for a version."""
        pass

    # Chunk operations (v0.10.0 - Chunk-level versioning)

    async def create_chunks_batch(self, chunks: List[Chunk]) -> List[Chunk]:
        """Create multiple chunks in a batch (optimized in subclasses).

        Default implementation calls create_chunk for each chunk.
        Subclasses should override this for better performance using batch inserts.

        Args:
            chunks: List of chunks to create

        Returns:
            List of created chunks
        """
        results = []
        for chunk in chunks:
            results.append(await self.create_chunk(chunk))
        return results

    @abstractmethod
    async def create_chunk(self, chunk: Chunk) -> Chunk:
        """Create a single chunk record.

        Args:
            chunk: Chunk to create

        Returns:
            Created chunk
        """
        pass

    @abstractmethod
    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get a chunk by its ID.

        Args:
            chunk_id: ID of the chunk

        Returns:
            Chunk if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_chunks_by_version(self, version_id: UUID) -> List[Chunk]:
        """Get all chunks for a specific version.

        Args:
            version_id: ID of the version

        Returns:
            List of chunks, ordered by chunk_index
        """
        pass

    @abstractmethod
    async def store_chunk_content(
        self,
        chunk_id: UUID,
        content: str,
        compress: bool = True,
    ) -> None:
        """Store chunk content separately (optionally compressed).

        Args:
            chunk_id: ID of the chunk
            content: Text content of the chunk
            compress: Whether to compress the content
        """
        pass

    @abstractmethod
    async def get_chunk_content(self, chunk_id: UUID) -> Optional[str]:
        """Retrieve chunk content (automatically decompressed).

        Args:
            chunk_id: ID of the chunk

        Returns:
            Chunk content if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_chunks_by_version(self, version_id: UUID) -> int:
        """Delete all chunks associated with a version.

        Args:
            version_id: ID of the version

        Returns:
            Number of chunks deleted
        """
        pass

    # Diff operations

    @abstractmethod
    async def compute_diff(
        self,
        document_id: UUID,
        from_version: int,
        to_version: int,
    ) -> Optional[DiffResult]:
        """Compute diff between two versions."""
        pass

    # Cleanup operations

    @abstractmethod
    async def cleanup_old_versions(
        self,
        document_id: UUID,
        keep_count: int = 10,
    ) -> int:
        """Delete old versions, keeping only the most recent ones. Returns count deleted."""
        pass

    @abstractmethod
    async def cleanup_by_age(self, days: int) -> int:
        """Delete versions older than specified days. Returns count deleted."""
        pass

    # Statistics operations

    @abstractmethod
    async def get_statistics(self) -> StorageStatistics:
        """Get overall storage statistics."""
        pass

    @abstractmethod
    async def get_document_statistics(self, document_id: UUID) -> DocumentStatistics:
        """Get statistics for a specific document."""
        pass

    @abstractmethod
    async def get_top_documents(
        self,
        limit: int = 10,
        order_by: str = "version_count",
    ) -> List[Document]:
        """Get top documents by version count or other criteria.

        Args:
            limit: Maximum number of documents to return
            order_by: Field to order by (version_count, updated_at, file_size)
        """
        pass

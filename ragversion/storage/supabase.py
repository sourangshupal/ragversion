"""Supabase storage backend implementation."""

import gzip
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from supabase import create_client, Client
from ragversion.exceptions import StorageError, DocumentNotFoundError, VersionNotFoundError
from ragversion.models import Document, Version, DiffResult, StorageStatistics, DocumentStatistics, Chunk
from ragversion.storage.base import BaseStorage


class SupabaseStorage(BaseStorage):
    """Supabase storage backend with async support."""

    def __init__(
        self,
        url: str,
        key: str,
        content_compression: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize Supabase storage.

        Args:
            url: Supabase project URL
            key: Supabase service key
            content_compression: Whether to compress content with gzip
            timeout: Request timeout in seconds
        """
        self.url = url
        self.key = key
        self.content_compression = content_compression
        self.timeout = timeout
        self.client: Optional[Client] = None

    @classmethod
    def from_env(cls) -> "SupabaseStorage":
        """Create SupabaseStorage from environment variables."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")

        if not url or not key:
            raise StorageError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set"
            )

        return cls(url=url, key=key)

    async def initialize(self) -> None:
        """Initialize the Supabase client and ensure tables exist."""
        try:
            self.client = create_client(self.url, self.key)
            # Run migrations to ensure tables exist
            await self._ensure_tables()
        except Exception as e:
            raise StorageError("Failed to initialize Supabase storage", e)

    async def close(self) -> None:
        """Close Supabase client connections."""
        # Supabase Python client doesn't require explicit closing
        self.client = None

    async def health_check(self) -> bool:
        """Check if Supabase is accessible."""
        try:
            if not self.client:
                return False
            # Try a simple query
            self.client.table("documents").select("id").limit(1).execute()
            return True
        except Exception:
            return False

    async def _ensure_tables(self) -> None:
        """Ensure required tables exist. Note: This assumes tables are created via Supabase migrations."""
        # In production, tables should be created via Supabase migrations
        # Required migrations:
        #   - 001_initial_schema.sql: Core documents, versions, and content_snapshots tables
        #   - 002_chunk_versioning.sql: Chunk-level versioning (v0.10.0+)
        # This is a placeholder for checking table existence
        pass

    def _ensure_client(self) -> Client:
        """Ensure client is initialized."""
        if not self.client:
            raise StorageError("Storage not initialized. Call initialize() first.")
        return self.client

    # Document operations

    async def batch_create_documents(self, documents: List[Document]) -> List[Document]:
        """Create multiple document records in a single API call (optimized)."""
        if not documents:
            return []

        try:
            client = self._ensure_client()

            # Prepare batch data
            batch_data = [
                {
                    "id": str(doc.id),
                    "file_path": doc.file_path,
                    "file_name": doc.file_name,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "content_hash": doc.content_hash,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat(),
                    "version_count": doc.version_count,
                    "current_version": doc.current_version,
                    "metadata": json.dumps(doc.metadata),
                }
                for doc in documents
            ]

            # Execute batch insert in single API call
            result = client.table("documents").insert(batch_data).execute()

            if not result.data or len(result.data) != len(documents):
                raise StorageError(f"Failed to create all {len(documents)} documents")

            return documents
        except Exception as e:
            raise StorageError(f"Failed to batch create {len(documents)} documents", e)

    async def create_document(self, document: Document) -> Document:
        """Create a new document record."""
        try:
            client = self._ensure_client()
            data = {
                "id": str(document.id),
                "file_path": document.file_path,
                "file_name": document.file_name,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "content_hash": document.content_hash,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "version_count": document.version_count,
                "current_version": document.current_version,
                "metadata": json.dumps(document.metadata),
            }
            result = client.table("documents").insert(data).execute()
            if not result.data:
                raise StorageError("Failed to create document")
            return document
        except Exception as e:
            raise StorageError(f"Failed to create document: {document.file_path}", e)

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        try:
            client = self._ensure_client()
            result = client.table("documents").select("*").eq("id", str(document_id)).execute()

            if not result.data:
                return None

            data = result.data[0]
            return Document(
                id=UUID(data["id"]),
                file_path=data["file_path"],
                file_name=data["file_name"],
                file_type=data["file_type"],
                file_size=data["file_size"],
                content_hash=data["content_hash"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                version_count=data["version_count"],
                current_version=data["current_version"],
                metadata=json.loads(data["metadata"]) if data.get("metadata") else {},
            )
        except Exception as e:
            raise StorageError(f"Failed to get document: {document_id}", e)

    async def get_document_by_path(self, file_path: str) -> Optional[Document]:
        """Get a document by file path."""
        try:
            client = self._ensure_client()
            result = client.table("documents").select("*").eq("file_path", file_path).execute()

            if not result.data:
                return None

            data = result.data[0]
            return Document(
                id=UUID(data["id"]),
                file_path=data["file_path"],
                file_name=data["file_name"],
                file_type=data["file_type"],
                file_size=data["file_size"],
                content_hash=data["content_hash"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                version_count=data["version_count"],
                current_version=data["current_version"],
                metadata=json.loads(data["metadata"]) if data.get("metadata") else {},
            )
        except Exception as e:
            raise StorageError(f"Failed to get document by path: {file_path}", e)

    async def update_document(self, document: Document) -> Document:
        """Update an existing document."""
        try:
            client = self._ensure_client()
            data = {
                "file_path": document.file_path,
                "file_name": document.file_name,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "content_hash": document.content_hash,
                "updated_at": datetime.utcnow().isoformat(),
                "version_count": document.version_count,
                "current_version": document.current_version,
                "metadata": json.dumps(document.metadata),
            }
            result = (
                client.table("documents").update(data).eq("id", str(document.id)).execute()
            )

            if not result.data:
                raise DocumentNotFoundError(str(document.id))

            return document
        except Exception as e:
            raise StorageError(f"Failed to update document: {document.id}", e)

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document and all its versions."""
        try:
            client = self._ensure_client()
            # Delete all versions first
            client.table("versions").delete().eq("document_id", str(document_id)).execute()
            # Delete content
            client.table("content_snapshots").delete().eq("document_id", str(document_id)).execute()
            # Delete document
            client.table("documents").delete().eq("id", str(document_id)).execute()
        except Exception as e:
            raise StorageError(f"Failed to delete document: {document_id}", e)

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "updated_at",
    ) -> List[Document]:
        """List documents with pagination."""
        try:
            client = self._ensure_client()
            result = (
                client.table("documents")
                .select("*")
                .order(order_by, desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            documents = []
            for data in result.data:
                documents.append(
                    Document(
                        id=UUID(data["id"]),
                        file_path=data["file_path"],
                        file_name=data["file_name"],
                        file_type=data["file_type"],
                        file_size=data["file_size"],
                        content_hash=data["content_hash"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        version_count=data["version_count"],
                        current_version=data["current_version"],
                        metadata=json.loads(data["metadata"]) if data.get("metadata") else {},
                    )
                )
            return documents
        except Exception as e:
            raise StorageError("Failed to list documents", e)

    async def search_documents(
        self,
        metadata_filter: Optional[dict] = None,
        file_type: Optional[str] = None,
    ) -> List[Document]:
        """Search documents by metadata or file type."""
        try:
            client = self._ensure_client()
            query = client.table("documents").select("*")

            if file_type:
                query = query.eq("file_type", file_type)

            # Note: Metadata filtering requires JSONB support in Supabase
            # This is a simplified implementation
            result = query.execute()

            documents = []
            for data in result.data:
                doc_metadata = json.loads(data.get("metadata", "{}"))

                # Filter by metadata if provided
                if metadata_filter:
                    matches = all(
                        doc_metadata.get(k) == v for k, v in metadata_filter.items()
                    )
                    if not matches:
                        continue

                documents.append(
                    Document(
                        id=UUID(data["id"]),
                        file_path=data["file_path"],
                        file_name=data["file_name"],
                        file_type=data["file_type"],
                        file_size=data["file_size"],
                        content_hash=data["content_hash"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        version_count=data["version_count"],
                        current_version=data["current_version"],
                        metadata=doc_metadata,
                    )
                )
            return documents
        except Exception as e:
            raise StorageError("Failed to search documents", e)

    # Version operations

    async def batch_create_versions(self, versions: List[Version]) -> List[Version]:
        """Create multiple version records in a single API call (optimized)."""
        if not versions:
            return []

        try:
            client = self._ensure_client()

            # Prepare batch data for versions
            batch_data = [
                {
                    "id": str(ver.id),
                    "document_id": str(ver.document_id),
                    "version_number": ver.version_number,
                    "content_hash": ver.content_hash,
                    "file_size": ver.file_size,
                    "change_type": ver.change_type.value,
                    "created_at": ver.created_at.isoformat(),
                    "created_by": ver.created_by,
                    "metadata": json.dumps(ver.metadata),
                }
                for ver in versions
            ]

            # Execute batch insert for versions
            result = client.table("versions").insert(batch_data).execute()

            if not result.data or len(result.data) != len(versions):
                raise StorageError(f"Failed to create all {len(versions)} versions")

            # Store content for versions that have it (batch if possible)
            content_batch = []
            for ver in versions:
                if ver.content:
                    content_data = ver.content.encode("utf-8")
                    if self.content_compression:
                        content_data = gzip.compress(content_data)

                    content_batch.append({
                        "version_id": str(ver.id),
                        "content": content_data.hex(),
                        "compressed": self.content_compression,
                        "created_at": datetime.utcnow().isoformat(),
                    })

            # Batch insert content if any
            if content_batch:
                client.table("content_snapshots").insert(content_batch).execute()

            return versions
        except Exception as e:
            raise StorageError(f"Failed to batch create {len(versions)} versions", e)

    async def create_version(self, version: Version) -> Version:
        """Create a new version record."""
        try:
            client = self._ensure_client()
            data = {
                "id": str(version.id),
                "document_id": str(version.document_id),
                "version_number": version.version_number,
                "content_hash": version.content_hash,
                "file_size": version.file_size,
                "change_type": version.change_type.value,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "metadata": json.dumps(version.metadata),
            }
            result = client.table("versions").insert(data).execute()

            if not result.data:
                raise StorageError("Failed to create version")

            # Store content if provided
            if version.content:
                await self.store_content(
                    version.id, version.content, compress=self.content_compression
                )

            return version
        except Exception as e:
            raise StorageError(f"Failed to create version for document {version.document_id}", e)

    async def get_version(self, version_id: UUID) -> Optional[Version]:
        """Get a version by ID."""
        try:
            client = self._ensure_client()
            result = client.table("versions").select("*").eq("id", str(version_id)).execute()

            if not result.data:
                return None

            data = result.data[0]
            return Version(
                id=UUID(data["id"]),
                document_id=UUID(data["document_id"]),
                version_number=data["version_number"],
                content_hash=data["content_hash"],
                file_size=data["file_size"],
                change_type=data["change_type"],
                created_at=datetime.fromisoformat(data["created_at"]),
                created_by=data.get("created_by"),
                metadata=json.loads(data["metadata"]) if data.get("metadata") else {},
            )
        except Exception as e:
            raise StorageError(f"Failed to get version: {version_id}", e)

    async def get_version_by_number(
        self, document_id: UUID, version_number: int
    ) -> Optional[Version]:
        """Get a specific version of a document."""
        try:
            client = self._ensure_client()
            result = (
                client.table("versions")
                .select("*")
                .eq("document_id", str(document_id))
                .eq("version_number", version_number)
                .execute()
            )

            if not result.data:
                return None

            data = result.data[0]
            return Version(
                id=UUID(data["id"]),
                document_id=UUID(data["document_id"]),
                version_number=data["version_number"],
                content_hash=data["content_hash"],
                file_size=data["file_size"],
                change_type=data["change_type"],
                created_at=datetime.fromisoformat(data["created_at"]),
                created_by=data.get("created_by"),
                metadata=json.loads(data["metadata"]) if data.get("metadata") else {},
            )
        except Exception as e:
            raise StorageError(
                f"Failed to get version {version_number} for document {document_id}", e
            )

    async def list_versions(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Version]:
        """List all versions of a document."""
        try:
            client = self._ensure_client()
            result = (
                client.table("versions")
                .select("*")
                .eq("document_id", str(document_id))
                .order("version_number", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            versions = []
            for data in result.data:
                versions.append(
                    Version(
                        id=UUID(data["id"]),
                        document_id=UUID(data["document_id"]),
                        version_number=data["version_number"],
                        content_hash=data["content_hash"],
                        file_size=data["file_size"],
                        change_type=data["change_type"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        created_by=data.get("created_by"),
                        metadata=json.loads(data["metadata"]) if data.get("metadata") else {},
                    )
                )
            return versions
        except Exception as e:
            raise StorageError(f"Failed to list versions for document {document_id}", e)

    async def delete_version(self, version_id: UUID) -> None:
        """Delete a specific version."""
        try:
            client = self._ensure_client()
            # Delete content first
            await self.delete_content(version_id)
            # Delete version
            client.table("versions").delete().eq("id", str(version_id)).execute()
        except Exception as e:
            raise StorageError(f"Failed to delete version: {version_id}", e)

    async def get_latest_version(self, document_id: UUID) -> Optional[Version]:
        """Get the latest version of a document."""
        try:
            client = self._ensure_client()
            result = (
                client.table("versions")
                .select("*")
                .eq("document_id", str(document_id))
                .order("version_number", desc=True)
                .limit(1)
                .execute()
            )

            if not result.data:
                return None

            data = result.data[0]
            return Version(
                id=UUID(data["id"]),
                document_id=UUID(data["document_id"]),
                version_number=data["version_number"],
                content_hash=data["content_hash"],
                file_size=data["file_size"],
                change_type=data["change_type"],
                created_at=datetime.fromisoformat(data["created_at"]),
                created_by=data.get("created_by"),
                metadata=json.loads(data["metadata"]) if data.get("metadata") else {},
            )
        except Exception as e:
            raise StorageError(f"Failed to get latest version for document {document_id}", e)

    # Content operations

    async def store_content(
        self,
        version_id: UUID,
        content: str,
        compress: bool = True,
    ) -> None:
        """Store version content (optionally compressed)."""
        try:
            client = self._ensure_client()

            # Compress content if enabled
            content_data = content.encode("utf-8")
            if compress:
                content_data = gzip.compress(content_data)

            data = {
                "version_id": str(version_id),
                "content": content_data.hex(),  # Store as hex string
                "compressed": compress,
                "created_at": datetime.utcnow().isoformat(),
            }

            client.table("content_snapshots").insert(data).execute()
        except Exception as e:
            raise StorageError(f"Failed to store content for version {version_id}", e)

    async def get_content(self, version_id: UUID) -> Optional[str]:
        """Retrieve version content (automatically decompressed)."""
        try:
            client = self._ensure_client()
            result = (
                client.table("content_snapshots")
                .select("*")
                .eq("version_id", str(version_id))
                .execute()
            )

            if not result.data:
                return None

            data = result.data[0]
            content_data = bytes.fromhex(data["content"])

            # Decompress if needed
            if data.get("compressed", False):
                content_data = gzip.decompress(content_data)

            return content_data.decode("utf-8")
        except Exception as e:
            raise StorageError(f"Failed to get content for version {version_id}", e)

    async def delete_content(self, version_id: UUID) -> None:
        """Delete stored content for a version."""
        try:
            client = self._ensure_client()
            client.table("content_snapshots").delete().eq("version_id", str(version_id)).execute()
        except Exception as e:
            raise StorageError(f"Failed to delete content for version {version_id}", e)

    # Chunk operations (v0.10.0 - Chunk-level versioning)

    async def create_chunks_batch(self, chunks: List[Chunk]) -> List[Chunk]:
        """Create multiple chunks in a batch using Supabase insert."""
        if not chunks:
            return []

        try:
            client = self._ensure_client()

            # Prepare chunk data for batch insert
            chunk_data = [
                {
                    "id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "version_id": str(chunk.version_id),
                    "chunk_index": chunk.chunk_index,
                    "content_hash": chunk.content_hash,
                    "token_count": chunk.token_count,
                    "created_at": chunk.created_at.isoformat(),
                    "metadata": chunk.metadata if chunk.metadata else {},
                }
                for chunk in chunks
            ]

            # Batch insert chunks
            client.table("chunks").insert(chunk_data).execute()

            # Batch store chunk content (if present in metadata)
            content_data = []
            for chunk in chunks:
                if "content" in chunk.metadata:
                    text = chunk.metadata["content"]
                    data = text.encode("utf-8")
                    if self.content_compression:
                        data = gzip.compress(data)
                    content_data.append(
                        {
                            "chunk_id": str(chunk.id),
                            "content": data.hex(),  # Store as hex string
                            "compressed": self.content_compression,
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    )

            if content_data:
                client.table("chunk_content").insert(content_data).execute()

            return chunks
        except Exception as e:
            raise StorageError(f"Failed to batch create {len(chunks)} chunks", e)

    async def create_chunk(self, chunk: Chunk) -> Chunk:
        """Create a single chunk record."""
        try:
            client = self._ensure_client()

            chunk_data = {
                "id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "version_id": str(chunk.version_id),
                "chunk_index": chunk.chunk_index,
                "content_hash": chunk.content_hash,
                "token_count": chunk.token_count,
                "created_at": chunk.created_at.isoformat(),
                "metadata": chunk.metadata if chunk.metadata else {},
            }

            client.table("chunks").insert(chunk_data).execute()

            # Store content if present
            if "content" in chunk.metadata:
                await self.store_chunk_content(
                    chunk.id, chunk.metadata["content"], self.content_compression
                )

            return chunk
        except Exception as e:
            raise StorageError(f"Failed to create chunk {chunk.id}", e)

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get a chunk by its ID."""
        try:
            client = self._ensure_client()

            result = client.table("chunks").select("*").eq("id", str(chunk_id)).execute()

            if not result.data:
                return None

            data = result.data[0]
            return Chunk(
                id=UUID(data["id"]),
                document_id=UUID(data["document_id"]),
                version_id=UUID(data["version_id"]),
                chunk_index=data["chunk_index"],
                content_hash=data["content_hash"],
                token_count=data["token_count"],
                created_at=datetime.fromisoformat(data["created_at"]),
                metadata=data.get("metadata", {}),
            )
        except Exception as e:
            raise StorageError(f"Failed to get chunk {chunk_id}", e)

    async def get_chunks_by_version(self, version_id: UUID) -> List[Chunk]:
        """Get all chunks for a specific version, ordered by chunk_index."""
        try:
            client = self._ensure_client()

            result = (
                client.table("chunks")
                .select("*")
                .eq("version_id", str(version_id))
                .order("chunk_index")
                .execute()
            )

            chunks = []
            for data in result.data:
                chunk = Chunk(
                    id=UUID(data["id"]),
                    document_id=UUID(data["document_id"]),
                    version_id=UUID(data["version_id"]),
                    chunk_index=data["chunk_index"],
                    content_hash=data["content_hash"],
                    token_count=data["token_count"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    metadata=data.get("metadata", {}),
                )
                chunks.append(chunk)

            return chunks
        except Exception as e:
            raise StorageError(f"Failed to get chunks for version {version_id}", e)

    async def store_chunk_content(
        self,
        chunk_id: UUID,
        content: str,
        compress: bool = True,
    ) -> None:
        """Store chunk content separately (optionally compressed)."""
        try:
            client = self._ensure_client()

            # Prepare content
            content_data = content.encode("utf-8")
            if compress:
                content_data = gzip.compress(content_data)

            data = {
                "chunk_id": str(chunk_id),
                "content": content_data.hex(),  # Store as hex string
                "compressed": compress,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Upsert (insert or update)
            client.table("chunk_content").upsert(data).execute()
        except Exception as e:
            raise StorageError(f"Failed to store content for chunk {chunk_id}", e)

    async def get_chunk_content(self, chunk_id: UUID) -> Optional[str]:
        """Retrieve chunk content (automatically decompressed)."""
        try:
            client = self._ensure_client()

            result = (
                client.table("chunk_content")
                .select("content, compressed")
                .eq("chunk_id", str(chunk_id))
                .execute()
            )

            if not result.data:
                return None

            data = result.data[0]
            content_data = bytes.fromhex(data["content"])

            # Decompress if needed
            if data.get("compressed", False):
                content_data = gzip.decompress(content_data)

            return content_data.decode("utf-8")
        except Exception as e:
            raise StorageError(f"Failed to get content for chunk {chunk_id}", e)

    async def delete_chunks_by_version(self, version_id: UUID) -> int:
        """Delete all chunks associated with a version."""
        try:
            client = self._ensure_client()

            # Get count before deletion
            result = (
                client.table("chunks")
                .select("id", count="exact")
                .eq("version_id", str(version_id))
                .execute()
            )
            count = result.count if result.count else 0

            # Delete chunks (cascade will delete chunk_content)
            client.table("chunks").delete().eq("version_id", str(version_id)).execute()

            return count
        except Exception as e:
            raise StorageError(f"Failed to delete chunks for version {version_id}", e)

    # Diff operations

    async def compute_diff(
        self,
        document_id: UUID,
        from_version: int,
        to_version: int,
    ) -> Optional[DiffResult]:
        """Compute diff between two versions."""
        try:
            # Get both versions
            from_ver = await self.get_version_by_number(document_id, from_version)
            to_ver = await self.get_version_by_number(document_id, to_version)

            if not from_ver or not to_ver:
                return None

            # Get content for both versions
            from_content = await self.get_content(from_ver.id)
            to_content = await self.get_content(to_ver.id)

            if not from_content or not to_content:
                return None

            # Simple diff implementation (can be enhanced with difflib)
            from_lines = from_content.splitlines()
            to_lines = to_content.splitlines()

            # Basic line-by-line comparison
            import difflib

            diff = difflib.unified_diff(from_lines, to_lines, lineterm="")
            diff_text = "\n".join(diff)

            # Count additions and deletions
            additions = sum(1 for line in diff_text.split("\n") if line.startswith("+"))
            deletions = sum(1 for line in diff_text.split("\n") if line.startswith("-"))

            return DiffResult(
                document_id=document_id,
                from_version=from_version,
                to_version=to_version,
                diff_text=diff_text,
                additions=additions,
                deletions=deletions,
                from_hash=from_ver.content_hash,
                to_hash=to_ver.content_hash,
            )
        except Exception as e:
            raise StorageError(
                f"Failed to compute diff for document {document_id} versions {from_version} to {to_version}",
                e,
            )

    # Cleanup operations

    async def cleanup_old_versions(
        self,
        document_id: UUID,
        keep_count: int = 10,
    ) -> int:
        """Delete old versions, keeping only the most recent ones."""
        try:
            client = self._ensure_client()

            # Get all versions
            versions = await self.list_versions(document_id, limit=1000)

            if len(versions) <= keep_count:
                return 0

            # Delete oldest versions
            versions_to_delete = versions[keep_count:]
            for version in versions_to_delete:
                await self.delete_version(version.id)

            return len(versions_to_delete)
        except Exception as e:
            raise StorageError(
                f"Failed to cleanup old versions for document {document_id}", e
            )

    async def cleanup_by_age(self, days: int) -> int:
        """Delete versions older than specified days."""
        try:
            client = self._ensure_client()
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get old versions
            result = (
                client.table("versions")
                .select("*")
                .lt("created_at", cutoff_date.isoformat())
                .execute()
            )

            count = 0
            for data in result.data:
                version_id = UUID(data["id"])
                await self.delete_version(version_id)
                count += 1

            return count
        except Exception as e:
            raise StorageError(f"Failed to cleanup versions older than {days} days", e)

    # Statistics operations

    async def get_statistics(self) -> StorageStatistics:
        """Get overall storage statistics."""
        try:
            client = self._ensure_client()

            # Count total documents
            docs_result = client.table("documents").select("id", count="exact").execute()
            total_documents = docs_result.count or 0

            # Count total versions
            versions_result = client.table("versions").select("id", count="exact").execute()
            total_versions = versions_result.count or 0

            # Calculate average versions per document
            average_versions_per_document = (
                total_versions / total_documents if total_documents > 0 else 0.0
            )

            # Get total storage (sum of file sizes from documents)
            docs_data = client.table("documents").select("file_size").execute()
            total_storage_bytes = sum(doc["file_size"] for doc in docs_data.data)

            # Get documents by file type
            docs_with_types = client.table("documents").select("file_type").execute()
            documents_by_file_type: dict = {}
            for doc in docs_with_types.data:
                file_type = doc["file_type"]
                documents_by_file_type[file_type] = documents_by_file_type.get(file_type, 0) + 1

            # Get recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_versions = (
                client.table("versions")
                .select("id", count="exact")
                .gte("created_at", seven_days_ago.isoformat())
                .execute()
            )
            recent_activity_count = recent_versions.count or 0

            # Get oldest and newest document dates
            oldest_doc = (
                client.table("documents")
                .select("created_at")
                .order("created_at", desc=False)
                .limit(1)
                .execute()
            )
            oldest_document_date = (
                datetime.fromisoformat(oldest_doc.data[0]["created_at"])
                if oldest_doc.data
                else None
            )

            newest_doc = (
                client.table("documents")
                .select("created_at")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            newest_document_date = (
                datetime.fromisoformat(newest_doc.data[0]["created_at"])
                if newest_doc.data
                else None
            )

            return StorageStatistics(
                total_documents=total_documents,
                total_versions=total_versions,
                total_storage_bytes=total_storage_bytes,
                average_versions_per_document=average_versions_per_document,
                documents_by_file_type=documents_by_file_type,
                recent_activity_count=recent_activity_count,
                oldest_document_date=oldest_document_date,
                newest_document_date=newest_document_date,
            )
        except Exception as e:
            raise StorageError("Failed to get storage statistics", e)

    async def get_document_statistics(self, document_id: UUID) -> DocumentStatistics:
        """Get statistics for a specific document."""
        try:
            client = self._ensure_client()

            # Get document
            document = await self.get_document(document_id)
            if not document:
                raise DocumentNotFoundError(str(document_id))

            # Get all versions for this document
            versions = await self.list_versions(document_id, limit=10000)
            total_versions = len(versions)

            # Count versions by change type
            versions_by_change_type: dict = {}
            for version in versions:
                change_type = version.change_type.value
                versions_by_change_type[change_type] = (
                    versions_by_change_type.get(change_type, 0) + 1
                )

            # Calculate average days between changes
            average_days_between_changes = 0.0
            if total_versions > 1:
                time_diff = document.updated_at - document.created_at
                days_diff = time_diff.total_seconds() / 86400  # Convert to days
                average_days_between_changes = days_diff / (total_versions - 1)

            # Determine change frequency
            if average_days_between_changes < 1:
                change_frequency = "high"
            elif average_days_between_changes < 7:
                change_frequency = "medium"
            else:
                change_frequency = "low"

            return DocumentStatistics(
                document_id=document.id,
                file_name=document.file_name,
                file_path=document.file_path,
                total_versions=total_versions,
                versions_by_change_type=versions_by_change_type,
                total_size_bytes=document.file_size,
                first_tracked=document.created_at,
                last_updated=document.updated_at,
                average_days_between_changes=average_days_between_changes,
                change_frequency=change_frequency,
            )
        except DocumentNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get document statistics for {document_id}", e)

    async def get_top_documents(
        self,
        limit: int = 10,
        order_by: str = "version_count",
    ) -> List[Document]:
        """Get top documents by version count or other criteria."""
        try:
            client = self._ensure_client()

            # Validate order_by parameter
            valid_order_fields = ["version_count", "updated_at", "file_size"]
            if order_by not in valid_order_fields:
                order_by = "version_count"

            # Query top documents
            result = (
                client.table("documents")
                .select("*")
                .order(order_by, desc=True)
                .limit(limit)
                .execute()
            )

            documents = []
            for data in result.data:
                documents.append(
                    Document(
                        id=UUID(data["id"]),
                        file_path=data["file_path"],
                        file_name=data["file_name"],
                        file_type=data["file_type"],
                        file_size=data["file_size"],
                        content_hash=data["content_hash"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        version_count=data["version_count"],
                        current_version=data["current_version"],
                        metadata=json.loads(data["metadata"]) if data.get("metadata") else {},
                    )
                )
            return documents
        except Exception as e:
            raise StorageError(f"Failed to get top documents by {order_by}", e)

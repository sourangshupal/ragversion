"""Mock storage backend for testing."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from ragversion.exceptions import DocumentNotFoundError, VersionNotFoundError
from ragversion.models import DiffResult, Document, Version
from ragversion.storage.base import BaseStorage


class MockStorage(BaseStorage):
    """In-memory mock storage for testing."""

    def __init__(self):
        """Initialize mock storage."""
        self.documents: Dict[UUID, Document] = {}
        self.versions: Dict[UUID, Version] = {}
        self.content: Dict[UUID, str] = {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize storage."""
        self.initialized = True

    async def close(self) -> None:
        """Close storage."""
        self.initialized = False

    async def health_check(self) -> bool:
        """Health check."""
        return self.initialized

    # Document operations

    async def create_document(self, document: Document) -> Document:
        """Create document."""
        self.documents[document.id] = document
        return document

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document."""
        return self.documents.get(document_id)

    async def get_document_by_path(self, file_path: str) -> Optional[Document]:
        """Get document by path."""
        for doc in self.documents.values():
            if doc.file_path == file_path:
                return doc
        return None

    async def update_document(self, document: Document) -> Document:
        """Update document."""
        if document.id not in self.documents:
            raise DocumentNotFoundError(str(document.id))
        self.documents[document.id] = document
        return document

    async def delete_document(self, document_id: UUID) -> None:
        """Delete document."""
        if document_id in self.documents:
            del self.documents[document_id]

        # Delete associated versions
        to_delete = [v_id for v_id, v in self.versions.items() if v.document_id == document_id]
        for v_id in to_delete:
            del self.versions[v_id]
            if v_id in self.content:
                del self.content[v_id]

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "updated_at",
    ) -> List[Document]:
        """List documents."""
        docs = list(self.documents.values())

        # Sort
        if order_by == "updated_at":
            docs.sort(key=lambda d: d.updated_at, reverse=True)
        elif order_by == "created_at":
            docs.sort(key=lambda d: d.created_at, reverse=True)

        # Paginate
        return docs[offset : offset + limit]

    async def search_documents(
        self,
        metadata_filter: Optional[dict] = None,
        file_type: Optional[str] = None,
    ) -> List[Document]:
        """Search documents."""
        results = []

        for doc in self.documents.values():
            # Filter by file type
            if file_type and doc.file_type != file_type:
                continue

            # Filter by metadata
            if metadata_filter:
                matches = all(doc.metadata.get(k) == v for k, v in metadata_filter.items())
                if not matches:
                    continue

            results.append(doc)

        return results

    # Version operations

    async def create_version(self, version: Version) -> Version:
        """Create version."""
        self.versions[version.id] = version
        if version.content:
            self.content[version.id] = version.content
        return version

    async def get_version(self, version_id: UUID) -> Optional[Version]:
        """Get version."""
        return self.versions.get(version_id)

    async def get_version_by_number(
        self, document_id: UUID, version_number: int
    ) -> Optional[Version]:
        """Get version by number."""
        for version in self.versions.values():
            if (
                version.document_id == document_id
                and version.version_number == version_number
            ):
                return version
        return None

    async def list_versions(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Version]:
        """List versions."""
        versions = [v for v in self.versions.values() if v.document_id == document_id]
        versions.sort(key=lambda v: v.version_number, reverse=True)
        return versions[offset : offset + limit]

    async def delete_version(self, version_id: UUID) -> None:
        """Delete version."""
        if version_id in self.versions:
            del self.versions[version_id]
        if version_id in self.content:
            del self.content[version_id]

    async def get_latest_version(self, document_id: UUID) -> Optional[Version]:
        """Get latest version."""
        versions = [v for v in self.versions.values() if v.document_id == document_id]
        if not versions:
            return None
        return max(versions, key=lambda v: v.version_number)

    # Content operations

    async def store_content(
        self,
        version_id: UUID,
        content: str,
        compress: bool = True,
    ) -> None:
        """Store content."""
        self.content[version_id] = content

    async def get_content(self, version_id: UUID) -> Optional[str]:
        """Get content."""
        return self.content.get(version_id)

    async def delete_content(self, version_id: UUID) -> None:
        """Delete content."""
        if version_id in self.content:
            del self.content[version_id]

    # Diff operations

    async def compute_diff(
        self,
        document_id: UUID,
        from_version: int,
        to_version: int,
    ) -> Optional[DiffResult]:
        """Compute diff."""
        from_ver = await self.get_version_by_number(document_id, from_version)
        to_ver = await self.get_version_by_number(document_id, to_version)

        if not from_ver or not to_ver:
            return None

        from_content = await self.get_content(from_ver.id)
        to_content = await self.get_content(to_ver.id)

        if not from_content or not to_content:
            return None

        # Simple diff
        import difflib

        from_lines = from_content.splitlines()
        to_lines = to_content.splitlines()

        diff = difflib.unified_diff(from_lines, to_lines, lineterm="")
        diff_text = "\n".join(diff)

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

    # Cleanup operations

    async def cleanup_old_versions(
        self,
        document_id: UUID,
        keep_count: int = 10,
    ) -> int:
        """Cleanup old versions."""
        versions = await self.list_versions(document_id, limit=1000)

        if len(versions) <= keep_count:
            return 0

        to_delete = versions[keep_count:]
        for version in to_delete:
            await self.delete_version(version.id)

        return len(to_delete)

    async def cleanup_by_age(self, days: int) -> int:
        """Cleanup by age."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = 0

        to_delete = []
        for version_id, version in self.versions.items():
            if version.created_at < cutoff:
                to_delete.append(version_id)

        for version_id in to_delete:
            await self.delete_version(version_id)
            count += 1

        return count

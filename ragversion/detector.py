"""Change detection engine for RAGVersion."""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID

import aiofiles

from ragversion.exceptions import ParsingError
from ragversion.models import ChangeEvent, ChangeType, Document, Version
from ragversion.parsers import ParserRegistry
from ragversion.storage.base import BaseStorage


class ChangeDetector:
    """Async change detector for document tracking."""

    def __init__(
        self,
        storage: BaseStorage,
        store_content: bool = True,
        max_file_size_mb: int = 50,
        hash_algorithm: str = "sha256",
    ):
        """
        Initialize change detector.

        Args:
            storage: Storage backend
            store_content: Whether to store full content
            max_file_size_mb: Maximum file size to process
            hash_algorithm: Hash algorithm to use (sha256, sha1, md5)
        """
        self.storage = storage
        self.store_content = store_content
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.hash_algorithm = hash_algorithm

    async def detect_change(
        self,
        file_path: str,
        metadata: Optional[dict] = None,
    ) -> Optional[ChangeEvent]:
        """
        Detect if a file has changed and create a change event.

        Args:
            file_path: Path to the file
            metadata: Optional metadata to attach

        Returns:
            ChangeEvent if change detected, None otherwise

        Raises:
            ParsingError: If file parsing fails
        """
        # Normalize to absolute path for consistency
        normalized_path = str(Path(file_path).absolute())

        # Validate file exists
        if not os.path.exists(file_path):
            # Check if it was previously tracked (deletion)
            existing_doc = await self.storage.get_document_by_path(normalized_path)
            if existing_doc:
                return await self._handle_deletion(existing_doc)
            return None

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size_bytes:
            raise ParsingError(
                file_path,
                Exception(
                    f"File size ({file_size} bytes) exceeds maximum ({self.max_file_size_bytes} bytes)"
                ),
            )

        # Parse file content
        content = await self._parse_file(file_path)

        # Compute content hash
        content_hash = self._compute_hash(content)

        # Check if document exists
        existing_doc = await self.storage.get_document_by_path(normalized_path)

        if not existing_doc:
            # New document - CREATE
            return await self._handle_creation(
                normalized_path, content, content_hash, file_size, metadata
            )
        elif existing_doc.content_hash != content_hash:
            # Document changed - MODIFY
            return await self._handle_modification(
                existing_doc, content, content_hash, file_size, metadata
            )
        else:
            # No change detected
            return None

    async def _parse_file(self, file_path: str) -> str:
        """Parse file content using appropriate parser."""
        parser = ParserRegistry.get_parser(file_path)

        if not parser:
            # Fall back to text parser for unknown types
            async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return await f.read()

        return await parser.parse(file_path)

    def _compute_hash(self, content: str) -> str:
        """Compute hash of content."""
        hash_func = hashlib.new(self.hash_algorithm)
        hash_func.update(content.encode("utf-8"))
        return hash_func.hexdigest()

    async def _handle_creation(
        self,
        file_path: str,
        content: str,
        content_hash: str,
        file_size: int,
        metadata: Optional[dict] = None,
    ) -> ChangeEvent:
        """Handle new document creation."""
        path = Path(file_path)

        # Create document
        document = Document(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_type=path.suffix or "unknown",
            file_size=file_size,
            content_hash=content_hash,
            version_count=1,
            current_version=1,
            metadata=metadata or {},
        )

        document = await self.storage.create_document(document)

        # Create first version
        version = Version(
            document_id=document.id,
            version_number=1,
            content_hash=content_hash,
            content=content if self.store_content else None,
            file_size=file_size,
            change_type=ChangeType.CREATED,
            metadata=metadata or {},
        )

        version = await self.storage.create_version(version)

        # Return change event
        return ChangeEvent(
            document_id=document.id,
            version_id=version.id,
            file_path=file_path,
            file_name=path.name,
            change_type=ChangeType.CREATED,
            version_number=1,
            content_hash=content_hash,
            previous_hash=None,
            file_size=file_size,
            metadata=metadata or {},
        )

    async def _handle_modification(
        self,
        existing_doc: Document,
        content: str,
        content_hash: str,
        file_size: int,
        metadata: Optional[dict] = None,
    ) -> ChangeEvent:
        """Handle document modification."""
        # Update document
        new_version_number = existing_doc.current_version + 1
        existing_doc.content_hash = content_hash
        existing_doc.file_size = file_size
        existing_doc.version_count += 1
        existing_doc.current_version = new_version_number
        existing_doc.updated_at = datetime.utcnow()

        if metadata:
            existing_doc.metadata.update(metadata)

        await self.storage.update_document(existing_doc)

        # Create new version
        version = Version(
            document_id=existing_doc.id,
            version_number=new_version_number,
            content_hash=content_hash,
            content=content if self.store_content else None,
            file_size=file_size,
            change_type=ChangeType.MODIFIED,
            metadata=metadata or {},
        )

        version = await self.storage.create_version(version)

        # Return change event
        return ChangeEvent(
            document_id=existing_doc.id,
            version_id=version.id,
            file_path=existing_doc.file_path,
            file_name=existing_doc.file_name,
            change_type=ChangeType.MODIFIED,
            version_number=new_version_number,
            content_hash=content_hash,
            previous_hash=existing_doc.content_hash,
            file_size=file_size,
            metadata=metadata or {},
        )

    async def _handle_deletion(self, existing_doc: Document) -> ChangeEvent:
        """Handle document deletion."""
        # Create deletion version
        new_version_number = existing_doc.current_version + 1

        version = Version(
            document_id=existing_doc.id,
            version_number=new_version_number,
            content_hash=existing_doc.content_hash,
            content=None,
            file_size=0,
            change_type=ChangeType.DELETED,
        )

        version = await self.storage.create_version(version)

        # Update document
        existing_doc.version_count += 1
        existing_doc.current_version = new_version_number
        existing_doc.updated_at = datetime.utcnow()
        await self.storage.update_document(existing_doc)

        # Return change event
        return ChangeEvent(
            document_id=existing_doc.id,
            version_id=version.id,
            file_path=existing_doc.file_path,
            file_name=existing_doc.file_name,
            change_type=ChangeType.DELETED,
            version_number=new_version_number,
            content_hash=existing_doc.content_hash,
            previous_hash=existing_doc.content_hash,
            file_size=0,
        )

    async def restore_version(
        self,
        document_id: UUID,
        version_number: int,
        target_path: Optional[str] = None,
    ) -> Tuple[str, ChangeEvent]:
        """
        Restore a document to a specific version.

        Args:
            document_id: ID of the document
            version_number: Version number to restore
            target_path: Optional path to restore to (default: original path)

        Returns:
            Tuple of (restored_file_path, change_event)

        Raises:
            DocumentNotFoundError: If document not found
            VersionNotFoundError: If version not found
        """
        # Get document and version
        document = await self.storage.get_document(document_id)
        if not document:
            from ragversion.exceptions import DocumentNotFoundError

            raise DocumentNotFoundError(str(document_id))

        version = await self.storage.get_version_by_number(document_id, version_number)
        if not version:
            from ragversion.exceptions import VersionNotFoundError

            raise VersionNotFoundError(str(document_id), version_number)

        # Get content
        content = await self.storage.get_content(version.id)
        if not content:
            raise Exception(f"Content not found for version {version_number}")

        # Determine target path
        restore_path = target_path or document.file_path

        # Write content to file
        async with aiofiles.open(restore_path, "w", encoding="utf-8") as f:
            await f.write(content)

        # Create restoration version
        new_version_number = document.current_version + 1

        restore_version = Version(
            document_id=document.id,
            version_number=new_version_number,
            content_hash=version.content_hash,
            content=content if self.store_content else None,
            file_size=version.file_size,
            change_type=ChangeType.RESTORED,
            metadata={"restored_from_version": version_number},
        )

        restore_version = await self.storage.create_version(restore_version)

        # Update document
        document.content_hash = version.content_hash
        document.file_size = version.file_size
        document.version_count += 1
        document.current_version = new_version_number
        document.updated_at = datetime.utcnow()
        await self.storage.update_document(document)

        # Return change event
        event = ChangeEvent(
            document_id=document.id,
            version_id=restore_version.id,
            file_path=restore_path,
            file_name=document.file_name,
            change_type=ChangeType.RESTORED,
            version_number=new_version_number,
            content_hash=version.content_hash,
            previous_hash=document.content_hash,
            file_size=version.file_size,
            metadata={"restored_from_version": version_number},
        )

        return restore_path, event

"""Core data models for RAGVersion."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ChangeType(str, Enum):
    """Type of change detected in a document."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RESTORED = "restored"


class Document(BaseModel):
    """Represents a tracked document."""

    id: UUID = Field(default_factory=uuid4)
    file_path: str = Field(..., description="Absolute or relative path to the file")
    file_name: str = Field(..., description="Name of the file")
    file_type: str = Field(..., description="MIME type or file extension")
    file_size: int = Field(..., description="File size in bytes")
    content_hash: str = Field(..., description="SHA-256 hash of content")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    version_count: int = Field(default=1, description="Number of versions")
    current_version: int = Field(default=1, description="Current version number")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Ensure file path is not empty."""
        if not v or not v.strip():
            raise ValueError("file_path cannot be empty")
        return v.strip()


class Version(BaseModel):
    """Represents a specific version of a document."""

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID = Field(..., description="ID of the parent document")
    version_number: int = Field(..., description="Version number (1-indexed)")

    content_hash: str = Field(..., description="SHA-256 hash of this version's content")
    content: Optional[str] = Field(None, description="Actual content (optional)")

    file_size: int = Field(..., description="File size in bytes")
    change_type: ChangeType = Field(..., description="Type of change")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User or system that created version")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Version-specific metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ChangeEvent(BaseModel):
    """Event emitted when a document change is detected."""

    document_id: UUID = Field(..., description="ID of the changed document")
    version_id: UUID = Field(..., description="ID of the new version")

    file_path: str = Field(..., description="Path to the file")
    file_name: str = Field(..., description="Name of the file")

    change_type: ChangeType = Field(..., description="Type of change detected")
    version_number: int = Field(..., description="New version number")

    content_hash: str = Field(..., description="Content hash of new version")
    previous_hash: Optional[str] = Field(None, description="Previous content hash")

    file_size: int = Field(..., description="File size in bytes")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class FileProcessingError(BaseModel):
    """Represents an error that occurred while processing a file."""

    file_path: str = Field(..., description="Path to the file that failed")
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error: parsing, storage, unknown")
    exception_type: str = Field(..., description="Python exception type")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class BatchResult(BaseModel):
    """Result of a batch processing operation."""

    successful: List[ChangeEvent] = Field(default_factory=list, description="Successfully processed changes")
    failed: List[FileProcessingError] = Field(default_factory=list, description="Failed file processing attempts")

    total_files: int = Field(..., description="Total number of files processed")
    duration_seconds: float = Field(..., description="Total processing time")

    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @property
    def success_count(self) -> int:
        """Number of successfully processed files."""
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Number of failed files."""
        return len(self.failed)

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.success_count / self.total_files) * 100


class DiffResult(BaseModel):
    """Result of a diff operation between two versions."""

    document_id: UUID = Field(..., description="ID of the document")
    from_version: int = Field(..., description="Source version number")
    to_version: int = Field(..., description="Target version number")

    diff_text: str = Field(..., description="Human-readable diff")
    additions: int = Field(default=0, description="Number of additions")
    deletions: int = Field(default=0, description="Number of deletions")

    from_hash: str = Field(..., description="Content hash of source version")
    to_hash: str = Field(..., description="Content hash of target version")

    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
        }


class StorageStatistics(BaseModel):
    """Overall storage statistics."""

    total_documents: int = Field(..., description="Total number of tracked documents")
    total_versions: int = Field(..., description="Total number of versions across all documents")
    total_storage_bytes: int = Field(..., description="Total storage used in bytes")
    average_versions_per_document: float = Field(..., description="Average number of versions per document")
    documents_by_file_type: Dict[str, int] = Field(default_factory=dict, description="Count of documents by file type")
    recent_activity_count: int = Field(default=0, description="Number of changes in last 7 days")
    oldest_document_date: Optional[datetime] = Field(None, description="Date of oldest tracked document")
    newest_document_date: Optional[datetime] = Field(None, description="Date of newest tracked document")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class DocumentStatistics(BaseModel):
    """Statistics for a specific document."""

    document_id: UUID = Field(..., description="ID of the document")
    file_name: str = Field(..., description="Name of the file")
    file_path: str = Field(..., description="Path to the file")
    total_versions: int = Field(..., description="Total number of versions")
    versions_by_change_type: Dict[str, int] = Field(default_factory=dict, description="Count of versions by change type")
    total_size_bytes: int = Field(..., description="Current file size in bytes")
    first_tracked: datetime = Field(..., description="When the document was first tracked")
    last_updated: datetime = Field(..., description="When the document was last updated")
    average_days_between_changes: float = Field(default=0.0, description="Average days between changes")
    change_frequency: str = Field(default="low", description="Change frequency: high, medium, low")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# Chunk-Level Versioning Models (v0.10.0)
# ============================================================================


class ChunkChangeType(str, Enum):
    """Type of change detected in a chunk."""

    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    UNCHANGED = "unchanged"
    REORDERED = "reordered"


class Chunk(BaseModel):
    """Represents a content chunk within a document version."""

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID = Field(..., description="ID of the parent document")
    version_id: UUID = Field(..., description="ID of the version this chunk belongs to")
    chunk_index: int = Field(..., description="0-indexed position within the document")
    content_hash: str = Field(..., description="SHA-256 hash of chunk content")
    token_count: int = Field(..., description="Number of tokens in this chunk")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata (may include content)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ChunkDiff(BaseModel):
    """Result of comparing chunks between versions."""

    document_id: UUID = Field(..., description="ID of the document")
    from_version: int = Field(..., description="Source version number")
    to_version: int = Field(..., description="Target version number")

    added_chunks: List[Chunk] = Field(default_factory=list, description="Newly added chunks")
    modified_chunks: List[tuple] = Field(default_factory=list, description="Modified chunks (old, new) pairs")
    removed_chunks: List[Chunk] = Field(default_factory=list, description="Removed chunks")
    unchanged_chunks: List[Chunk] = Field(default_factory=list, description="Chunks that remained the same")
    reordered_chunks: List[Chunk] = Field(default_factory=list, description="Chunks that moved position")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

    @property
    def total_changes(self) -> int:
        """Total number of chunks that changed (added + modified)."""
        return len(self.added_chunks) + len(self.modified_chunks)

    @property
    def total_chunks(self) -> int:
        """Total number of chunks in the new version."""
        return (
            len(self.added_chunks)
            + len(self.modified_chunks)
            + len(self.unchanged_chunks)
            + len(self.reordered_chunks)
        )

    @property
    def savings_percentage(self) -> float:
        """Percentage of chunks that don't need re-embedding (unchanged + reordered)."""
        if self.total_chunks == 0:
            return 0.0
        unchanged_count = len(self.unchanged_chunks) + len(self.reordered_chunks)
        return (unchanged_count / self.total_chunks) * 100


class ChunkingConfig(BaseModel):
    """Configuration for chunking strategy."""

    enabled: bool = Field(default=False, description="Enable chunk-level tracking (opt-in)")
    chunk_size: int = Field(default=500, description="Target size per chunk (tokens or characters)")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    splitter_type: str = Field(default="recursive", description="Chunking strategy: recursive, semantic, etc.")
    store_chunk_content: bool = Field(default=True, description="Store chunk content in database")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

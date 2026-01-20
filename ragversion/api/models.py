"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Request models

class TrackFileRequest(BaseModel):
    """Request to track a file."""

    file_path: str = Field(..., description="Path to the file to track")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class TrackDirectoryRequest(BaseModel):
    """Request to track a directory."""

    dir_path: str = Field(..., description="Path to directory")
    patterns: Optional[List[str]] = Field(None, description="File patterns to match")
    recursive: bool = Field(True, description="Recursive search")
    max_workers: int = Field(4, description="Parallel workers")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class RestoreVersionRequest(BaseModel):
    """Request to restore a version."""

    document_id: UUID = Field(..., description="Document ID")
    version_number: int = Field(..., description="Version number to restore")
    target_path: Optional[str] = Field(None, description="Optional target path")


class SearchDocumentsRequest(BaseModel):
    """Request to search documents."""

    file_type: Optional[str] = Field(None, description="Filter by file type")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Filter by metadata")


# Response models

class DocumentResponse(BaseModel):
    """Document response."""

    id: UUID
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    content_hash: str
    created_at: datetime
    updated_at: datetime
    version_count: int
    current_version: int
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class VersionResponse(BaseModel):
    """Version response."""

    id: UUID
    document_id: UUID
    version_number: int
    content_hash: str
    file_size: int
    change_type: str
    created_at: datetime
    created_by: Optional[str]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ChangeEventResponse(BaseModel):
    """Change event response."""

    document_id: UUID
    version_id: UUID
    change_type: str
    file_name: str
    file_path: str
    file_size: int
    content_hash: str
    version_number: int
    previous_hash: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class FileProcessingErrorResponse(BaseModel):
    """File processing error response."""

    file_path: str
    error: str
    error_type: str
    exception_type: str


class BatchResultResponse(BaseModel):
    """Batch operation result response."""

    successful: List[ChangeEventResponse]
    failed: List[FileProcessingErrorResponse]
    total_files: int
    duration_seconds: float
    started_at: datetime
    completed_at: datetime


class DiffResultResponse(BaseModel):
    """Diff result response."""

    document_id: UUID
    from_version: int
    to_version: int
    additions: int
    deletions: int
    changes: int
    diff_text: Optional[str]
    similarity: float


class StorageStatisticsResponse(BaseModel):
    """Storage statistics response."""

    total_documents: int
    total_versions: int
    total_size_bytes: int
    file_types: Dict[str, int]
    recent_changes: int
    oldest_document: Optional[datetime]
    newest_document: Optional[datetime]


class DocumentStatisticsResponse(BaseModel):
    """Document statistics response."""

    document_id: UUID
    total_versions: int
    total_size_bytes: int
    first_version_date: datetime
    latest_version_date: datetime
    change_frequency_days: float
    change_types: Dict[str, int]


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    storage_backend: str = Field(..., description="Storage backend type")
    storage_healthy: bool = Field(..., description="Storage health")
    timestamp: datetime = Field(..., description="Check timestamp")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

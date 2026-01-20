"""Statistics and analytics endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ragversion import AsyncVersionTracker
from ragversion.api.dependencies import get_tracker, verify_api_key
from ragversion.api.models import (
    StorageStatisticsResponse,
    DocumentStatisticsResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get(
    "",
    response_model=StorageStatisticsResponse,
    summary="Get storage statistics",
    description="Get overall storage statistics including document counts, file types, and sizes",
)
async def get_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days for recent changes"),
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get storage statistics."""
    try:
        stats = await tracker.get_statistics(days=days)
        return StorageStatisticsResponse.model_validate(stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/document/{document_id}",
    response_model=DocumentStatisticsResponse,
    summary="Get document statistics",
    description="Get detailed statistics for a specific document",
    responses={404: {"model": ErrorResponse}},
)
async def get_document_statistics(
    document_id: UUID,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get document statistics."""
    try:
        stats = await tracker.get_document_statistics(document_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        return DocumentStatisticsResponse.model_validate(stats)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

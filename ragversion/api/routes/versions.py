"""Version management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ragversion import AsyncVersionTracker
from ragversion.api.dependencies import get_tracker, verify_api_key
from ragversion.api.models import (
    VersionResponse,
    ChangeEventResponse,
    RestoreVersionRequest,
    DiffResultResponse,
    ErrorResponse,
)
from ragversion.exceptions import VersionNotFoundError, DocumentNotFoundError

router = APIRouter(prefix="/versions", tags=["versions"])


@router.get(
    "/{version_id}",
    response_model=VersionResponse,
    summary="Get version by ID",
    description="Retrieve a specific version by its ID",
    responses={404: {"model": ErrorResponse}},
)
async def get_version(
    version_id: UUID,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get version by ID."""
    try:
        version = await tracker.get_version(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        return VersionResponse.model_validate(version)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/document/{document_id}",
    response_model=List[VersionResponse],
    summary="List versions for document",
    description="Get version history for a specific document",
    responses={404: {"model": ErrorResponse}},
)
async def list_versions(
    document_id: UUID,
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """List versions for a document."""
    try:
        versions = await tracker.list_versions(document_id, limit, offset)
        return [VersionResponse.model_validate(ver) for ver in versions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/document/{document_id}/number/{version_number}",
    response_model=VersionResponse,
    summary="Get version by number",
    description="Get a specific version of a document by version number",
    responses={404: {"model": ErrorResponse}},
)
async def get_version_by_number(
    document_id: UUID,
    version_number: int,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get version by number."""
    try:
        version = await tracker.get_version_by_number(document_id, version_number)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} not found for document {document_id}"
            )
        return VersionResponse.model_validate(version)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/document/{document_id}/latest",
    response_model=VersionResponse,
    summary="Get latest version",
    description="Get the most recent version of a document",
    responses={404: {"model": ErrorResponse}},
)
async def get_latest_version(
    document_id: UUID,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get latest version."""
    try:
        version = await tracker.get_latest_version(document_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No versions found for document {document_id}"
            )
        return VersionResponse.model_validate(version)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{version_id}/content",
    response_model=str,
    summary="Get version content",
    description="Get the content of a specific version",
    responses={404: {"model": ErrorResponse}},
)
async def get_content(
    version_id: UUID,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get version content."""
    try:
        content = await tracker.get_content(version_id)
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content not found for version {version_id}"
            )
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/restore",
    response_model=ChangeEventResponse,
    summary="Restore version",
    description="Restore a document to a specific version",
    responses={404: {"model": ErrorResponse}},
)
async def restore_version(
    request: RestoreVersionRequest,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Restore a version."""
    try:
        event = await tracker.restore_version(
            request.document_id,
            request.version_number,
            request.target_path,
        )
        return ChangeEventResponse.model_validate(event)
    except (DocumentNotFoundError, VersionNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/document/{document_id}/diff/{from_version}/{to_version}",
    response_model=DiffResultResponse,
    summary="Get diff between versions",
    description="Compare two versions of a document",
    responses={404: {"model": ErrorResponse}},
)
async def get_diff(
    document_id: UUID,
    from_version: int,
    to_version: int,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get diff between versions."""
    try:
        diff = await tracker.get_diff(document_id, from_version, to_version)
        if not diff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not compute diff for document {document_id}"
            )
        return DiffResultResponse.model_validate(diff)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

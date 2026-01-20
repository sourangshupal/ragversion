"""Tracking endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from ragversion import AsyncVersionTracker
from ragversion.api.dependencies import get_tracker, verify_api_key
from ragversion.api.models import (
    TrackFileRequest,
    TrackDirectoryRequest,
    ChangeEventResponse,
    BatchResultResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/track", tags=["tracking"])


@router.post(
    "/file",
    response_model=ChangeEventResponse,
    summary="Track a file",
    description="Track changes to a single file",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def track_file(
    request: TrackFileRequest,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Track a single file."""
    try:
        event = await tracker.track_file(
            request.file_path,
            metadata=request.metadata,
        )
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found or unchanged: {request.file_path}"
            )
        return ChangeEventResponse.model_validate(event)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {request.file_path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/directory",
    response_model=BatchResultResponse,
    summary="Track directory",
    description="Track all files in a directory with optional pattern matching",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def track_directory(
    request: TrackDirectoryRequest,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Track all files in a directory."""
    try:
        result = await tracker.track_directory(
            request.dir_path,
            patterns=request.patterns,
            recursive=request.recursive,
            max_workers=request.max_workers,
            metadata=request.metadata,
        )
        return BatchResultResponse(
            successful=[ChangeEventResponse.model_validate(e) for e in result.successful],
            failed=result.failed,
            total_files=result.total_files,
            duration_seconds=result.duration_seconds,
            started_at=result.started_at,
            completed_at=result.completed_at,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory not found: {request.dir_path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

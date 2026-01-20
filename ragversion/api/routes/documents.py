"""Document management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ragversion import AsyncVersionTracker
from ragversion.api.dependencies import get_tracker, verify_api_key
from ragversion.api.models import (
    DocumentResponse,
    SearchDocumentsRequest,
    ErrorResponse,
)
from ragversion.exceptions import DocumentNotFoundError

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="List documents",
    description="List all documents with pagination and sorting",
)
async def list_documents(
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    order_by: str = Query("updated_at", description="Sort by field"),
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """List documents with pagination."""
    try:
        documents = await tracker.list_documents(limit, offset, order_by)
        return [DocumentResponse.model_validate(doc) for doc in documents]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document by ID",
    description="Retrieve a specific document by its ID",
    responses={404: {"model": ErrorResponse}},
)
async def get_document(
    document_id: UUID,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get document by ID."""
    try:
        document = await tracker.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        return DocumentResponse.model_validate(document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/path/{file_path:path}",
    response_model=DocumentResponse,
    summary="Get document by file path",
    description="Retrieve a document by its file path",
    responses={404: {"model": ErrorResponse}},
)
async def get_document_by_path(
    file_path: str,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get document by file path."""
    try:
        document = await tracker.get_document_by_path(file_path)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {file_path}"
            )
        return DocumentResponse.model_validate(document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/search",
    response_model=List[DocumentResponse],
    summary="Search documents",
    description="Search documents by file type and metadata filters",
)
async def search_documents(
    request: SearchDocumentsRequest,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Search documents."""
    try:
        documents = await tracker.search_documents(
            metadata_filter=request.metadata_filter,
            file_type=request.file_type,
        )
        return [DocumentResponse.model_validate(doc) for doc in documents]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete a document and all its versions",
    responses={404: {"model": ErrorResponse}},
)
async def delete_document(
    document_id: UUID,
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Delete document."""
    try:
        await tracker.delete_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/top/by-version-count",
    response_model=List[DocumentResponse],
    summary="Get top documents",
    description="Get top documents by version count or other criteria",
)
async def get_top_documents(
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    order_by: str = Query("version_count", description="Sort criteria"),
    tracker: AsyncVersionTracker = Depends(get_tracker),
    _: None = Depends(verify_api_key),
):
    """Get top documents."""
    try:
        documents = await tracker.get_top_documents(limit, order_by)
        return [DocumentResponse.model_validate(doc) for doc in documents]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

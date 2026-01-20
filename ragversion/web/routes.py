"""Web UI routes for RAGVersion."""

from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ragversion import AsyncVersionTracker
from ragversion.api.dependencies import get_tracker

# Setup templates
TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    tracker: AsyncVersionTracker = Depends(get_tracker),
):
    """Dashboard homepage with statistics overview."""
    try:
        # Get overall statistics
        stats = await tracker.get_statistics(days=7)

        # Get top documents
        top_docs = await tracker.get_top_documents(limit=10, order_by="version_count")

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "active_page": "dashboard",
                "stats": stats,
                "top_docs": top_docs,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}",
        )


@router.get("/documents", response_class=HTMLResponse)
async def list_documents(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by filename"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    order_by: str = Query("updated_at", description="Sort field"),
    tracker: AsyncVersionTracker = Depends(get_tracker),
):
    """List all documents with filtering and pagination."""
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Get all documents for filtering
        all_docs = await tracker.list_documents(limit=10000, offset=0, order_by=order_by)

        # Apply filters
        filtered_docs = all_docs

        if search:
            search_lower = search.lower()
            filtered_docs = [
                doc
                for doc in filtered_docs
                if search_lower in doc.file_name.lower() or search_lower in doc.file_path.lower()
            ]

        if file_type:
            filtered_docs = [doc for doc in filtered_docs if doc.file_type == file_type]

        # Pagination
        total_documents = len(filtered_docs)
        total_pages = (total_documents + limit - 1) // limit
        paginated_docs = filtered_docs[offset : offset + limit]

        # Get unique file types for filter dropdown
        file_types = sorted(set(doc.file_type for doc in all_docs))

        return templates.TemplateResponse(
            "documents.html",
            {
                "request": request,
                "active_page": "documents",
                "documents": paginated_docs,
                "total_documents": total_documents,
                "page": page,
                "total_pages": total_pages,
                "search": search,
                "file_type": file_type,
                "file_types": file_types,
                "order_by": order_by,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.get("/documents/{document_id}", response_class=HTMLResponse)
async def document_detail(
    request: Request,
    document_id: UUID,
    tracker: AsyncVersionTracker = Depends(get_tracker),
):
    """Document detail page with version history."""
    try:
        # Get document
        document = await tracker.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        # Get version history
        versions = await tracker.list_versions(document_id, limit=1000)

        # Get document statistics
        doc_stats = await tracker.get_document_statistics(document_id)

        return templates.TemplateResponse(
            "document_detail.html",
            {
                "request": request,
                "active_page": "documents",
                "document": document,
                "versions": versions,
                "doc_stats": doc_stats,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load document: {str(e)}",
        )


@router.get("/documents/{document_id}/diff/{from_version}/{to_version}", response_class=HTMLResponse)
async def version_diff(
    request: Request,
    document_id: UUID,
    from_version: int,
    to_version: int,
    tracker: AsyncVersionTracker = Depends(get_tracker),
):
    """Compare two versions of a document."""
    try:
        # Get diff
        diff = await tracker.get_diff(document_id, from_version, to_version)
        if not diff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not compute diff for document {document_id}",
            )

        return templates.TemplateResponse(
            "diff.html",
            {
                "request": request,
                "active_page": "documents",
                "document_id": document_id,
                "from_version": from_version,
                "to_version": to_version,
                "diff": diff,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute diff: {str(e)}",
        )

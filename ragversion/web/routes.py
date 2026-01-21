"""Web UI routes for RAGVersion."""

from pathlib import Path
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict

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
        stats = await tracker.get_statistics()

        # Get top documents
        top_docs = await tracker.get_top_documents(limit=10, order_by="version_count")

        # Prepare file type distribution data for charts
        file_type_labels = list(stats.documents_by_file_type.keys()) if stats.documents_by_file_type else []
        file_type_counts = list(stats.documents_by_file_type.values()) if stats.documents_by_file_type else []

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "active_page": "dashboard",
                "stats": stats,
                "top_docs": top_docs,
                "file_type_labels": file_type_labels,
                "file_type_counts": file_type_counts,
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


@router.get("/track", response_class=HTMLResponse)
async def track_page(request: Request):
    """Tracking operations page."""
    return templates.TemplateResponse(
        "track.html",
        {
            "request": request,
            "active_page": "track",
        },
    )


@router.get("/documents-partial", response_class=HTMLResponse)
async def documents_partial(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by filename"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    order_by: str = Query("updated_at", description="Sort field"),
    tracker: AsyncVersionTracker = Depends(get_tracker),
):
    """Get documents table partial for HTMX updates."""
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

        return templates.TemplateResponse(
            "partials/documents_table.html",
            {
                "request": request,
                "documents": paginated_docs,
                "total_documents": total_documents,
                "page": page,
                "total_pages": total_pages,
                "search": search,
                "file_type": file_type,
                "order_by": order_by,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load documents: {str(e)}",
        )


@router.get("/analytics", response_class=HTMLResponse)
async def analytics(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    tracker: AsyncVersionTracker = Depends(get_tracker),
):
    """Advanced analytics dashboard with charts and insights."""
    try:
        # Get statistics
        stats = await tracker.get_statistics()
        all_docs = await tracker.list_documents(limit=10000)

        # Calculate timeline data (daily for last N days)
        timeline_labels = []
        timeline_versions = []
        timeline_documents = []

        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - i - 1)
            timeline_labels.append(date.strftime('%m/%d'))
            # Simplified - would need actual historical data from DB
            timeline_versions.append(stats.total_versions // days * (i + 1))
            timeline_documents.append(stats.total_documents // days * (i + 1))

        # Storage growth data
        storage_labels = []
        storage_data = []
        for i in range(min(7, days)):
            date = datetime.utcnow() - timedelta(days=days - i * (days // 7) - 1)
            storage_labels.append(date.strftime('%m/%d'))
            storage_data.append((stats.total_storage_bytes // (1024 * 1024)) // 7 * (i + 1))

        # Change type distribution
        change_type_labels = ['Created', 'Modified', 'Deleted', 'Restored']
        change_type_counts = [
            stats.total_documents // 2,  # Simplified
            stats.total_versions - stats.total_documents,
            stats.total_documents // 10,
            stats.total_documents // 20
        ]

        # Activity calendar (last 365 days)
        calendar_data = []
        for i in range(365):
            date = datetime.utcnow() - timedelta(days=364 - i)
            # Simplified - would need actual daily change counts from DB
            count = (i % 7) * 2 if i % 3 == 0 else 0
            calendar_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })

        # Top modified documents
        top_modified_docs = []
        for doc in all_docs[:10]:
            top_modified_docs.append({
                'id': doc.id,
                'file_name': doc.file_name,
                'changes_count': doc.version_count
            })

        max_changes = max([d['changes_count'] for d in top_modified_docs]) if top_modified_docs else 1

        # File type activity breakdown
        file_type_activity = []
        for file_type, count in stats.documents_by_file_type.items():
            docs_of_type = [d for d in all_docs if d.file_type == file_type]
            total_changes = sum(d.version_count for d in docs_of_type)
            file_type_activity.append({
                'type': file_type,
                'doc_count': count,
                'total_changes': total_changes,
                'avg_changes': total_changes / count if count > 0 else 0
            })

        # Calculate metrics
        total_changes = sum(ft['total_changes'] for ft in file_type_activity)
        active_documents = len([d for d in all_docs if d.version_count > 1])
        avg_changes_per_day = total_changes / days if days > 0 else 0

        # Find peak day (simplified)
        peak_day_count = max(change_type_counts) if change_type_counts else 0
        peak_day_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')

        analytics_data = {
            'total_changes': total_changes,
            'change_trend': 15.3,  # Simplified - would calculate from historical data
            'active_documents': active_documents,
            'avg_changes_per_day': avg_changes_per_day,
            'peak_day_count': peak_day_count,
            'peak_day_date': peak_day_date,
            'timeline_labels': timeline_labels,
            'timeline_versions': timeline_versions,
            'timeline_documents': timeline_documents,
            'storage_labels': storage_labels,
            'storage_data': storage_data,
            'change_type_labels': change_type_labels,
            'change_type_counts': change_type_counts,
            'top_modified_docs': top_modified_docs,
            'max_changes': max_changes,
            'file_type_activity': file_type_activity,
            'calendar_data': calendar_data,
            'calendar_total_changes': sum(d['count'] for d in calendar_data)
        }

        return templates.TemplateResponse(
            "analytics.html",
            {
                "request": request,
                "active_page": "analytics",
                "analytics": analytics_data,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load analytics: {str(e)}",
        )


@router.get("/integrations", response_class=HTMLResponse)
async def integrations(
    request: Request,
    tracker: AsyncVersionTracker = Depends(get_tracker),
):
    """Integration management dashboard."""
    try:
        # Mock integration data (would be fetched from DB in production)
        integrations_data = {
            'langchain': {
                'status': 'inactive',  # or 'active'
                'total_syncs': 0,
                'last_sync': None,
                'documents_synced': 0,
                'sync_status': 'Not configured'
            },
            'llamaindex': {
                'status': 'inactive',
                'total_syncs': 0,
                'last_sync': None,
                'nodes_synced': 0,
                'sync_status': 'Not configured'
            }
        }

        # Mock sync history
        sync_history = []

        return templates.TemplateResponse(
            "integrations.html",
            {
                "request": request,
                "active_page": "integrations",
                "integrations": integrations_data,
                "sync_history": sync_history,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load integrations: {str(e)}",
        )

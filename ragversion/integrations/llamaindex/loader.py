"""LlamaIndex loader for RAGVersion."""

import logging
from typing import Any, List, Optional
from uuid import UUID

try:
    from llama_index.core import Document as LIDocument

    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    LIDocument = Any

from ragversion.tracker import AsyncVersionTracker

logger = logging.getLogger(__name__)


class LlamaIndexLoader:
    """
    Load documents from RAGVersion into LlamaIndex.

    Useful for one-time migrations or rebuilding indexes.
    """

    def __init__(self, tracker: AsyncVersionTracker):
        """
        Initialize LlamaIndex loader.

        Args:
            tracker: AsyncVersionTracker instance
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndex is not installed. Install with: pip install ragversion[llamaindex]"
            )

        self.tracker = tracker

    async def load_documents(
        self,
        document_ids: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> List[LIDocument]:
        """
        Load documents as LlamaIndex documents.

        Args:
            document_ids: Optional list of document IDs to load
            limit: Maximum number of documents to load

        Returns:
            List of LlamaIndex documents
        """
        li_documents = []

        # Get documents
        if document_ids:
            # Load specific documents
            for doc_id in document_ids:
                doc = await self.tracker.get_document(UUID(doc_id))
                if doc:
                    # Get latest version content
                    latest_version = await self.tracker.get_latest_version(doc.id)
                    if latest_version:
                        content = await self.tracker.get_content(latest_version.id)
                        if content:
                            metadata = {
                                "document_id": str(doc.id),
                                "version_id": str(latest_version.id),
                                "version_number": latest_version.version_number,
                                "file_path": doc.file_path,
                                "file_name": doc.file_name,
                            }
                            li_documents.append(
                                LIDocument(
                                    text=content,
                                    metadata=metadata,
                                    doc_id=str(doc.id),
                                )
                            )
        else:
            # Load all documents
            documents = await self.tracker.list_documents(limit=limit)

            for doc in documents:
                # Get latest version content
                latest_version = await self.tracker.get_latest_version(doc.id)
                if latest_version:
                    content = await self.tracker.get_content(latest_version.id)
                    if content:
                        metadata = {
                            "document_id": str(doc.id),
                            "version_id": str(latest_version.id),
                            "version_number": latest_version.version_number,
                            "file_path": doc.file_path,
                            "file_name": doc.file_name,
                        }
                        li_documents.append(
                            LIDocument(
                                text=content,
                                metadata=metadata,
                                doc_id=str(doc.id),
                            )
                        )

        return li_documents

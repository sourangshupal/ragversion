"""LangChain loader for RAGVersion."""

import logging
from typing import Any, List, Optional
from uuid import UUID

try:
    from langchain_core.documents import Document as LCDocument

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LCDocument = Any

from ragversion.tracker import AsyncVersionTracker

logger = logging.getLogger(__name__)


class LangChainLoader:
    """
    Load documents from RAGVersion into LangChain.

    Useful for one-time migrations or rebuilding indexes.
    """

    def __init__(self, tracker: AsyncVersionTracker):
        """
        Initialize LangChain loader.

        Args:
            tracker: AsyncVersionTracker instance
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. Install with: pip install ragversion[langchain]"
            )

        self.tracker = tracker

    async def load_documents(
        self,
        document_ids: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> List[LCDocument]:
        """
        Load documents as LangChain documents.

        Args:
            document_ids: Optional list of document IDs to load
            limit: Maximum number of documents to load

        Returns:
            List of LangChain documents
        """
        lc_documents = []

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
                            lc_documents.append(
                                LCDocument(page_content=content, metadata=metadata)
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
                        lc_documents.append(
                            LCDocument(page_content=content, metadata=metadata)
                        )

        return lc_documents

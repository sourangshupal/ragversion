"""Example: Using RAGVersion REST API with Python.

This example demonstrates how to interact with the RAGVersion REST API
using Python's requests library and httpx for async operations.

Requirements:
    pip install requests httpx

Usage:
    1. Start the API server: ragversion serve
    2. Run this script: python api_client_example.py
"""

import asyncio
from typing import List, Dict, Optional
from uuid import UUID

import requests
import httpx


class RAGVersionClient:
    """Synchronous client for RAGVersion API."""

    def __init__(self, base_url: str = "http://localhost:8000/api", api_key: Optional[str] = None):
        """Initialize client.

        Args:
            base_url: Base URL of the API server
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key

    def track_file(self, file_path: str, metadata: Optional[Dict] = None) -> Dict:
        """Track a single file.

        Args:
            file_path: Path to the file to track
            metadata: Optional metadata dictionary

        Returns:
            ChangeEvent dictionary
        """
        response = requests.post(
            f"{self.base_url}/track/file",
            json={"file_path": file_path, "metadata": metadata or {}},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def track_directory(
        self,
        dir_path: str,
        patterns: Optional[List[str]] = None,
        recursive: bool = True,
        max_workers: int = 4,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Track all files in a directory.

        Args:
            dir_path: Directory path
            patterns: File patterns (e.g., ["*.pdf", "*.docx"])
            recursive: Recursive search
            max_workers: Parallel workers
            metadata: Optional metadata

        Returns:
            BatchResult dictionary
        """
        response = requests.post(
            f"{self.base_url}/track/directory",
            json={
                "dir_path": dir_path,
                "patterns": patterns or ["*"],
                "recursive": recursive,
                "max_workers": max_workers,
                "metadata": metadata or {},
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def list_documents(self, limit: int = 100, offset: int = 0, order_by: str = "updated_at") -> List[Dict]:
        """List tracked documents.

        Args:
            limit: Number of results
            offset: Pagination offset
            order_by: Sort field

        Returns:
            List of Document dictionaries
        """
        response = requests.get(
            f"{self.base_url}/documents",
            params={"limit": limit, "offset": offset, "order_by": order_by},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_document(self, document_id: UUID) -> Dict:
        """Get document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document dictionary
        """
        response = requests.get(
            f"{self.base_url}/documents/{document_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def search_documents(self, file_type: Optional[str] = None, metadata_filter: Optional[Dict] = None) -> List[Dict]:
        """Search documents.

        Args:
            file_type: Filter by file type
            metadata_filter: Filter by metadata

        Returns:
            List of Document dictionaries
        """
        response = requests.post(
            f"{self.base_url}/documents/search",
            json={"file_type": file_type, "metadata_filter": metadata_filter},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def list_versions(self, document_id: UUID, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List versions for a document.

        Args:
            document_id: Document UUID
            limit: Number of results
            offset: Pagination offset

        Returns:
            List of Version dictionaries
        """
        response = requests.get(
            f"{self.base_url}/versions/document/{document_id}",
            params={"limit": limit, "offset": offset},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_latest_version(self, document_id: UUID) -> Dict:
        """Get latest version of a document.

        Args:
            document_id: Document UUID

        Returns:
            Version dictionary
        """
        response = requests.get(
            f"{self.base_url}/versions/document/{document_id}/latest",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_version_content(self, version_id: UUID) -> str:
        """Get version content.

        Args:
            version_id: Version UUID

        Returns:
            Version content as string
        """
        response = requests.get(
            f"{self.base_url}/versions/{version_id}/content",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.text

    def get_diff(self, document_id: UUID, from_version: int, to_version: int) -> Dict:
        """Get diff between two versions.

        Args:
            document_id: Document UUID
            from_version: Starting version number
            to_version: Ending version number

        Returns:
            DiffResult dictionary
        """
        response = requests.get(
            f"{self.base_url}/versions/document/{document_id}/diff/{from_version}/{to_version}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def restore_version(self, document_id: UUID, version_number: int, target_path: Optional[str] = None) -> Dict:
        """Restore a version.

        Args:
            document_id: Document UUID
            version_number: Version number to restore
            target_path: Optional target path

        Returns:
            ChangeEvent dictionary
        """
        response = requests.post(
            f"{self.base_url}/versions/restore",
            json={
                "document_id": str(document_id),
                "version_number": version_number,
                "target_path": target_path,
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_statistics(self, days: int = 30) -> Dict:
        """Get storage statistics.

        Args:
            days: Number of days for recent changes

        Returns:
            StorageStatistics dictionary
        """
        response = requests.get(
            f"{self.base_url}/statistics",
            params={"days": days},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_document_statistics(self, document_id: UUID) -> Dict:
        """Get document statistics.

        Args:
            document_id: Document UUID

        Returns:
            DocumentStatistics dictionary
        """
        response = requests.get(
            f"{self.base_url}/statistics/document/{document_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict:
        """Check API health.

        Returns:
            HealthCheck dictionary
        """
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


class AsyncRAGVersionClient:
    """Asynchronous client for RAGVersion API."""

    def __init__(self, base_url: str = "http://localhost:8000/api", api_key: Optional[str] = None):
        """Initialize async client.

        Args:
            base_url: Base URL of the API server
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key

    async def track_file(self, file_path: str, metadata: Optional[Dict] = None) -> Dict:
        """Track a single file asynchronously."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/track/file",
                json={"file_path": file_path, "metadata": metadata or {}},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List documents asynchronously."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/documents",
                params={"limit": limit, "offset": offset},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_statistics(self, days: int = 30) -> Dict:
        """Get statistics asynchronously."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/statistics",
                params={"days": days},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()


def example_sync():
    """Example using synchronous client."""
    print("=== Synchronous Client Example ===\n")

    # Initialize client
    client = RAGVersionClient(base_url="http://localhost:8000/api")

    # Health check
    print("1. Health Check")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Version: {health['version']}")
    print(f"   Storage: {health['storage_backend']}\n")

    # Track a file
    print("2. Track a File")
    try:
        event = client.track_file(
            file_path="/path/to/document.pdf",
            metadata={"author": "John Doe", "category": "technical"},
        )
        print(f"   Tracked: {event['file_name']}")
        print(f"   Change: {event['change_type']}")
        print(f"   Version: {event['version_number']}\n")
    except Exception as e:
        print(f"   Error: {e}\n")

    # List documents
    print("3. List Documents")
    documents = client.list_documents(limit=5)
    print(f"   Found {len(documents)} documents:")
    for doc in documents[:3]:
        print(f"   - {doc['file_name']}: {doc['version_count']} versions")
    print()

    # Get statistics
    print("4. Get Statistics")
    stats = client.get_statistics(days=7)
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Total versions: {stats['total_versions']}")
    print(f"   Recent changes: {stats['recent_changes']}\n")

    # Search documents
    print("5. Search Documents")
    results = client.search_documents(
        file_type="pdf",
        metadata_filter={"category": "technical"},
    )
    print(f"   Found {len(results)} PDF documents in 'technical' category\n")

    # Version history (if we have documents)
    if documents:
        print("6. Version History")
        doc_id = documents[0]["id"]
        versions = client.list_versions(doc_id, limit=5)
        print(f"   Versions for {documents[0]['file_name']}:")
        for v in versions[:3]:
            print(f"   - v{v['version_number']}: {v['change_type']} ({v['created_at']})")
        print()

        # Get diff
        if len(versions) >= 2:
            print("7. Get Diff")
            diff = client.get_diff(doc_id, 1, versions[0]["version_number"])
            print(f"   Additions: {diff['additions']}")
            print(f"   Deletions: {diff['deletions']}")
            print(f"   Similarity: {diff['similarity']:.2%}\n")


async def example_async():
    """Example using asynchronous client."""
    print("=== Asynchronous Client Example ===\n")

    # Initialize async client
    client = AsyncRAGVersionClient(base_url="http://localhost:8000/api")

    # Concurrent requests
    print("1. Concurrent Requests")
    results = await asyncio.gather(
        client.list_documents(limit=10),
        client.get_statistics(days=7),
    )
    documents, stats = results

    print(f"   Documents: {len(documents)}")
    print(f"   Total versions: {stats['total_versions']}")
    print(f"   Recent changes: {stats['recent_changes']}\n")

    # Track multiple files concurrently
    print("2. Track Multiple Files")
    file_paths = [
        "/path/to/doc1.pdf",
        "/path/to/doc2.pdf",
        "/path/to/doc3.pdf",
    ]

    tasks = [client.track_file(path, metadata={"batch": "example"}) for path in file_paths]

    try:
        events = await asyncio.gather(*tasks, return_exceptions=True)
        successful = [e for e in events if not isinstance(e, Exception)]
        print(f"   Successfully tracked: {len(successful)} files\n")
    except Exception as e:
        print(f"   Error: {e}\n")


def main():
    """Main example runner."""
    print("RAGVersion API Client Examples\n")
    print("Prerequisites:")
    print("1. Start the API server: ragversion serve")
    print("2. Have some documents tracked\n")
    input("Press Enter to continue...")
    print()

    # Run synchronous example
    try:
        example_sync()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server.")
        print("Make sure the server is running: ragversion serve")
        return
    except Exception as e:
        print(f"Error: {e}")

    # Run asynchronous example
    print("\n" + "=" * 50 + "\n")
    try:
        asyncio.run(example_async())
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

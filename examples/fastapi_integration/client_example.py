import httpx
import asyncio
import json
from datetime import datetime

class RAGVersionClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def get_stats(self):
        response = await self.client.get(f"{self.base_url}/api/stats")
        return response.json()
    
    async def get_changes(self, limit: int = 20, file_type: str = None):
        params = {"limit": limit}
        if file_type:
            params["file_type"] = file_type
        response = await self.client.get(f"{self.base_url}/api/changes", params=params)
        return response.json()
    
    async def list_documents(self, limit: int = 50, file_type: str = None):
        params = {"limit": limit}
        if file_type:
            params["file_type"] = file_type
        response = await self.client.get(f"{self.base_url}/api/documents", params=params)
        return response.json()
    
    async def get_document(self, file_path: str):
        encoded_path = file_path.replace("/", "%2F")
        response = await self.client.get(f"{self.base_url}/api/documents/{encoded_path}")
        return response.json()
    
    async def get_version(self, file_path: str, version_number: int):
        encoded_path = file_path.replace("/", "%2F")
        response = await self.client.get(
            f"{self.base_url}/api/documents/{encoded_path}/versions/{version_number}"
        )
        return response.json()
    
    async def get_chunks(self, file_path: str):
        encoded_path = file_path.replace("/", "%2F")
        response = await self.client.get(f"{self.base_url}/api/documents/{encoded_path}/chunks")
        return response.json()
    
    async def sync_all(self):
        response = await self.client.post(f"{self.base_url}/api/sync")
        return response.json()
    
    async def sync_file(self, file_path: str):
        encoded_path = file_path.replace("/", "%2F")
        response = await self.client.post(f"{self.base_url}/api/sync/{encoded_path}")
        return response.json()
    
    async def compare_versions(self, file_path: str, v1: int, v2: int):
        encoded_path = file_path.replace("/", "%2F")
        params = {"v1": v1, "v2": v2}
        response = await self.client.get(
            f"{self.base_url}/api/compare/{encoded_path}",
            params=params
        )
        return response.json()
    
    async def delete_document(self, file_path: str):
        encoded_path = file_path.replace("/", "%2F")
        response = await self.client.delete(f"{self.base_url}/api/documents/{encoded_path}")
        return response.json()

async def main():
    client = RAGVersionClient()
    
    try:
        print("=" * 60)
        print("RAGVersion API Client Example")
        print("=" * 60)
        
        # Get statistics
        print("\n1. Getting system statistics...")
        stats = await client.get_stats()
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Monitor active: {stats['monitor_active']}")
        print(f"   Monitor interval: {stats['monitor_interval_seconds']}s")
        
        # List documents
        print("\n2. Listing all documents...")
        documents = await client.list_documents()
        print(f"   Found {len(documents)} documents")
        
        if documents:
            doc = documents[0]
            file_path = doc['file_path']
            
            print(f"   Example document: {file_path}")
            print(f"   Current version: {doc['current_version']}")
            print(f"   File size: {doc['file_size']} bytes")
            
            # Get document details
            print("\n3. Getting document details...")
            details = await client.get_document(file_path)
            print(f"   Total versions: {details['total_versions']}")
            
            # Get chunks
            print("\n4. Getting document chunks...")
            chunks = await client.get_chunks(file_path)
            print(f"   Total chunks: {chunks['total_chunks']}")
            print(f"   First chunk preview: {chunks['chunks'][0]['content_preview'][:100]}...")
            
            # Compare versions if multiple versions exist
            if details['total_versions'] >= 2:
                print("\n5. Comparing versions...")
                comparison = await client.compare_versions(file_path, 1, 2)
                print(f"   Content length diff: {comparison['difference']['content_length_diff']:+d}")
                print(f"   New chunks: {comparison['difference']['new_chunks_count']}")
                print(f"   Removed chunks: {comparison['difference']['removed_chunks_count']}")
        
        # Get recent changes
        print("\n6. Getting recent changes...")
        changes = await client.get_changes(limit=5)
        print(f"   Recent changes: {len(changes)}")
        for change in changes:
            print(f"   - {change['file_path']}: {change['change_type']} (v{change['current_version']})")
        
        # Sync all documents
        print("\n7. Syncing all documents...")
        sync_result = await client.sync_all()
        print(f"   Synced files: {sync_result['synced_files']}")
        print(f"   Duration: {sync_result['duration_ms']}ms")
        
        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)
        
    except httpx.HTTPError as e:
        print(f"\nError: {e}")
        print("Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())

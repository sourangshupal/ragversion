"""
LlamaIndex integration example.

This example shows how to integrate RAGVersion with LlamaIndex
to automatically sync document changes to an index.
"""

import asyncio
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding

from ragversion import AsyncVersionTracker
from ragversion.integrations.llamaindex import LlamaIndexSync
from ragversion.storage import SupabaseStorage


async def main():
    """LlamaIndex integration example."""

    # Initialize RAGVersion
    storage = SupabaseStorage.from_env()
    tracker = AsyncVersionTracker(storage=storage, store_content=True)
    await tracker.initialize()

    # Initialize LlamaIndex components
    node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)

    embeddings = OpenAIEmbedding()

    # Create a new index
    index = VectorStoreIndex.from_documents(
        [],
        embed_model=embeddings,
    )

    # Create LlamaIndex sync
    sync = LlamaIndexSync(
        tracker=tracker,
        index=index,
        node_parser=node_parser,
    )

    print("=== Syncing documents to LlamaIndex ===")

    # Sync all documents in a directory
    # This will:
    # 1. Track all files for changes
    # 2. Automatically parse and index new/modified documents
    # 3. Update the vector index
    await sync.sync_directory(
        "./documents",
        patterns=["*.pdf", "*.md", "*.txt"],
        recursive=True,
    )

    print("\n=== Documents synced! ===")

    # Query the index
    query_engine = index.as_query_engine()
    response = query_engine.query("What is this document about?")
    print(f"\nQuery response: {response}")

    # Refresh entire index from tracked documents
    print("\n=== Refreshing index ===")
    await sync.refresh_index()
    print("Index refreshed!")

    # Close
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())

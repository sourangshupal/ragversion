"""
LangChain integration example.

This example shows how to integrate RAGVersion with LangChain
to automatically sync document changes to a vector store.
"""

import asyncio
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

from ragversion import AsyncVersionTracker
from ragversion.integrations.langchain import LangChainSync
from ragversion.storage import SupabaseStorage


async def main():
    """LangChain integration example."""

    # Initialize RAGVersion
    storage = SupabaseStorage.from_env()
    tracker = AsyncVersionTracker(storage=storage, store_content=True)
    await tracker.initialize()

    # Initialize LangChain components
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    embeddings = OpenAIEmbeddings()

    # Initialize Qdrant vector store
    qdrant_client = QdrantClient(":memory:")  # Use in-memory for demo
    vectorstore = Qdrant(
        client=qdrant_client,
        collection_name="documents",
        embeddings=embeddings,
    )

    # Create LangChain sync
    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore,
    )

    print("=== Syncing documents to LangChain ===")

    # Sync all documents in a directory
    # This will:
    # 1. Track all files for changes
    # 2. Automatically chunk and embed new/modified documents
    # 3. Update the vector store
    await sync.sync_directory(
        "./documents",
        patterns=["*.pdf", "*.md", "*.txt"],
        recursive=True,
    )

    print("\n=== Documents synced! ===")

    # Now any future changes will automatically be synced
    # because we registered callbacks in LangChainSync

    # Example: Track a new file
    print("\n=== Tracking new file ===")
    await tracker.track("./new_document.pdf")
    print("New document automatically synced to vector store!")

    # Close
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())

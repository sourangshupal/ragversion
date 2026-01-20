"""Quick Start Example: LangChain Integration with RAGVersion.

This example demonstrates how to use the quick_start function to set up
LangChain integration with just 3 lines of code instead of 35+ lines.

Before: 35+ lines of boilerplate
After: 3 lines with quick_start()

Requirements:
- pip install ragversion[langchain]
- Set OPENAI_API_KEY environment variable
- Optionally set SUPABASE_URL and SUPABASE_SERVICE_KEY for Supabase storage
"""

import asyncio
import os


# ============================================================================
# BEFORE: Traditional Setup (35+ lines)
# ============================================================================

async def before_quick_start():
    """Traditional setup - requires 35+ lines of code."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS

    from ragversion import AsyncVersionTracker
    from ragversion.storage import SupabaseStorage, SQLiteStorage
    from ragversion.integrations.langchain import LangChainSync

    # Storage setup (4 lines)
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"):
        storage = SupabaseStorage.from_env()
    else:
        storage = SQLiteStorage()

    # Tracker setup (3 lines)
    tracker = AsyncVersionTracker(
        storage=storage,
        store_content=True,
    )
    await tracker.initialize()

    # LangChain components setup (15 lines)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    embeddings = OpenAIEmbeddings()

    vectorstore = FAISS.from_texts(
        ["placeholder"],
        embeddings
    )

    # Integration setup (8 lines)
    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore,
    )

    # Sync directory (4 lines)
    await sync.sync_directory(
        "./documents",
        patterns=["*.txt", "*.md", "*.pdf"],
    )

    print("✓ Traditional setup complete (35+ lines)")
    return sync


# ============================================================================
# AFTER: Quick Start Setup (3 lines!)
# ============================================================================

async def after_quick_start():
    """Quick start - only 3 lines of code!"""
    from ragversion.integrations.langchain import quick_start

    # That's it! Just 3 lines 🚀
    sync = await quick_start("./documents")

    print("✓ Quick start complete (3 lines)")
    return sync


# ============================================================================
# Customization Examples
# ============================================================================

async def quick_start_with_custom_options():
    """Quick start with custom configuration options."""
    from ragversion.integrations.langchain import quick_start

    sync = await quick_start(
        directory="./documents",
        vectorstore_type="faiss",           # or "chroma"
        vectorstore_path="./my_vectorstore", # Save FAISS index here
        storage_backend="sqlite",           # or "supabase", "auto"
        chunk_size=500,                     # Smaller chunks
        chunk_overlap=100,                  # Custom overlap
        enable_chunk_tracking=True,         # Smart chunk-level updates (default)
    )

    print("✓ Custom quick start complete")
    return sync


async def quick_start_with_chroma():
    """Quick start with Chroma (persistent) vectorstore."""
    from ragversion.integrations.langchain import quick_start

    sync = await quick_start(
        directory="./documents",
        vectorstore_type="chroma",
        vectorstore_path="./chroma_db",  # Persistent Chroma database
    )

    print("✓ Chroma quick start complete")
    return sync


async def quick_start_with_custom_embeddings():
    """Quick start with custom embeddings model."""
    from langchain_openai import OpenAIEmbeddings
    from ragversion.integrations.langchain import quick_start

    # Use custom embeddings configuration
    custom_embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        dimensions=1536,
    )

    sync = await quick_start(
        directory="./documents",
        embeddings=custom_embeddings,
    )

    print("✓ Custom embeddings quick start complete")
    return sync


# ============================================================================
# Using the Integration After Setup
# ============================================================================

async def use_integration():
    """After setup, use the integration normally."""
    from ragversion.integrations.langchain import quick_start

    # Setup (3 lines)
    sync = await quick_start("./documents")

    # Now the vectorstore is ready to use!
    query = "What are the main features?"
    results = await sync.vectorstore.asimilarity_search(query, k=5)

    print(f"\nQuery: {query}")
    print(f"Found {len(results)} results:")
    for i, doc in enumerate(results, 1):
        print(f"\n{i}. {doc.metadata.get('file_name', 'Unknown')}")
        print(f"   {doc.page_content[:200]}...")

    # Track new files automatically
    await sync.tracker.track("./new_document.pdf")
    # The vectorstore is automatically updated!

    # Cleanup
    await sync.tracker.close()


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run examples."""
    print("=" * 80)
    print("RAGVersion + LangChain: Quick Start Examples")
    print("=" * 80)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set. Please set it to run these examples.")
        print("   export OPENAI_API_KEY=your-api-key")
        return

    # Create sample directory
    os.makedirs("./documents", exist_ok=True)
    with open("./documents/sample.txt", "w") as f:
        f.write("This is a sample document for RAGVersion quick start demo.")

    print("\n" + "=" * 80)
    print("Comparison: Before vs After")
    print("=" * 80)

    # Uncomment to see traditional setup (35+ lines)
    # print("\n[BEFORE] Traditional setup...")
    # sync_before = await before_quick_start()
    # await sync_before.tracker.close()

    print("\n[AFTER] Quick start setup...")
    sync_after = await after_quick_start()

    print("\n" + "=" * 80)
    print("Result: 91% code reduction (35 lines → 3 lines)")
    print("=" * 80)

    # Cleanup
    await sync_after.tracker.close()

    print("\n✓ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())

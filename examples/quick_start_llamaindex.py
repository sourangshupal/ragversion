"""Quick Start Example: LlamaIndex Integration with RAGVersion.

This example demonstrates how to use the quick_start function to set up
LlamaIndex integration with just 3 lines of code instead of 20+ lines.

Before: 20+ lines of boilerplate
After: 3 lines with quick_start()

Requirements:
- pip install ragversion[llamaindex]
- Set OPENAI_API_KEY environment variable
- Optionally set SUPABASE_URL and SUPABASE_SERVICE_KEY for Supabase storage
"""

import asyncio
import os


# ============================================================================
# BEFORE: Traditional Setup (20+ lines)
# ============================================================================

async def before_quick_start():
    """Traditional setup - requires 20+ lines of code."""
    from llama_index.core import VectorStoreIndex
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.openai import OpenAIEmbedding

    from ragversion import AsyncVersionTracker
    from ragversion.storage import SupabaseStorage, SQLiteStorage
    from ragversion.integrations.llamaindex import LlamaIndexSync

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

    # LlamaIndex components setup (8 lines)
    embeddings = OpenAIEmbedding()

    node_parser = SentenceSplitter(
        chunk_size=1024,
        chunk_overlap=20,
    )

    index = VectorStoreIndex.from_documents([], embed_model=embeddings)

    # Integration setup (6 lines)
    sync = LlamaIndexSync(
        tracker=tracker,
        index=index,
        node_parser=node_parser,
    )

    # Sync directory (4 lines)
    await sync.sync_directory(
        "./documents",
        patterns=["*.txt", "*.md", "*.pdf"],
    )

    print("✓ Traditional setup complete (20+ lines)")
    return sync


# ============================================================================
# AFTER: Quick Start Setup (3 lines!)
# ============================================================================

async def after_quick_start():
    """Quick start - only 3 lines of code!"""
    from ragversion.integrations.llamaindex import quick_start

    # That's it! Just 3 lines 🚀
    sync = await quick_start("./documents")

    print("✓ Quick start complete (3 lines)")
    return sync


# ============================================================================
# Customization Examples
# ============================================================================

async def quick_start_with_custom_options():
    """Quick start with custom configuration options."""
    from ragversion.integrations.llamaindex import quick_start

    sync = await quick_start(
        directory="./documents",
        storage_backend="sqlite",      # or "supabase", "auto"
        chunk_size=2048,               # Larger chunks for long documents
        chunk_overlap=200,             # Custom overlap
        enable_chunk_tracking=True,    # Smart chunk-level updates (default)
    )

    print("✓ Custom quick start complete")
    return sync


async def quick_start_with_custom_embeddings():
    """Quick start with custom embeddings model."""
    from llama_index.embeddings.openai import OpenAIEmbedding
    from ragversion.integrations.llamaindex import quick_start

    # Use custom embeddings configuration
    custom_embeddings = OpenAIEmbedding(
        model="text-embedding-3-small",
        dimensions=1536,
    )

    sync = await quick_start(
        directory="./documents",
        embeddings=custom_embeddings,
    )

    print("✓ Custom embeddings quick start complete")
    return sync


async def quick_start_disable_chunk_tracking():
    """Quick start with chunk tracking disabled (full re-embedding on updates)."""
    from ragversion.integrations.llamaindex import quick_start

    sync = await quick_start(
        directory="./documents",
        enable_chunk_tracking=False,  # Disable smart chunk updates
    )

    print("✓ Quick start without chunk tracking complete")
    return sync


# ============================================================================
# Using the Integration After Setup
# ============================================================================

async def use_integration():
    """After setup, use the integration normally."""
    from ragversion.integrations.llamaindex import quick_start

    # Setup (3 lines)
    sync = await quick_start("./documents")

    # Now the index is ready to use!
    query_engine = sync.index.as_query_engine()
    response = query_engine.query("What are the main features?")

    print(f"\nQuery: What are the main features?")
    print(f"Response: {response}")

    # Track new files automatically
    await sync.tracker.track("./new_document.pdf")
    # The index is automatically updated!

    # You can also use as retriever
    retriever = sync.index.as_retriever(similarity_top_k=5)
    nodes = retriever.retrieve("sample query")

    print(f"\nRetrieved {len(nodes)} nodes")
    for i, node in enumerate(nodes, 1):
        print(f"\n{i}. Score: {node.score:.4f}")
        print(f"   {node.text[:200]}...")

    # Cleanup
    await sync.tracker.close()


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run examples."""
    print("=" * 80)
    print("RAGVersion + LlamaIndex: Quick Start Examples")
    print("=" * 80)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set. Please set it to run these examples.")
        print("   export OPENAI_API_KEY=your-api-key")
        return

    # Create sample directory
    os.makedirs("./documents", exist_ok=True)
    with open("./documents/sample.txt", "w") as f:
        f.write("This is a sample document for RAGVersion quick start demo with LlamaIndex.")

    print("\n" + "=" * 80)
    print("Comparison: Before vs After")
    print("=" * 80)

    # Uncomment to see traditional setup (20+ lines)
    # print("\n[BEFORE] Traditional setup...")
    # sync_before = await before_quick_start()
    # await sync_before.tracker.close()

    print("\n[AFTER] Quick start setup...")
    sync_after = await after_quick_start()

    print("\n" + "=" * 80)
    print("Result: 85% code reduction (20 lines → 3 lines)")
    print("=" * 80)

    # Cleanup
    await sync_after.tracker.close()

    print("\n✓ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())

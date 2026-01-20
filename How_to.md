# How to Use RAGVersion: Developer Integration Guide

**Complete guide for integrating RAGVersion into your LangChain or LlamaIndex RAG applications**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [LangChain Integration](#langchain-integration)
4. [LlamaIndex Integration](#llamaindex-integration)
5. [Chunk-Level Versioning (Cost Optimization)](#chunk-level-versioning)
6. [Common Use Cases](#common-use-cases)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

RAGVersion helps you **track document changes** and **automatically sync** your vector stores, reducing embedding costs by up to **99%** (document-level) and **80-95%** (chunk-level).

### 30-Second Overview

```python
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage

# 1. Initialize tracker
storage = SQLiteStorage("ragversion.db")
tracker = AsyncVersionTracker(storage=storage)
await tracker.initialize()

# 2. Track changes
event = await tracker.track("document.pdf")
if event:
    print(f"Change detected: {event.change_type}")
    # Automatically sync with your vector store via callbacks!
```

---

## Installation

### Basic Installation

```bash
# Core functionality
pip install ragversion

# With LangChain
pip install "ragversion[langchain]"

# With LlamaIndex
pip install "ragversion[llamaindex]"

# With document parsers (PDF, DOCX, etc.)
pip install "ragversion[parsers]"

# Everything (recommended)
pip install "ragversion[all]"
```

### Verify Installation

```python
import ragversion
print(f"RAGVersion version: {ragversion.__version__}")
# Output: RAGVersion version: 0.10.0
```

---

## LangChain Integration

### Example 1: Basic LangChain Sync (Document-Level)

**Use Case**: Automatically sync changed documents to your LangChain vector store.

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.integrations.langchain import LangChainSync

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

async def main():
    # 1. Setup RAGVersion tracker
    storage = SQLiteStorage("ragversion.db")
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # 2. Setup LangChain components
    embeddings = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    vectorstore = Chroma(
        collection_name="my_documents",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )

    # 3. Create LangChain sync
    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore
    )

    # 4. Sync a directory (only changed documents are re-embedded)
    await sync.sync_directory("./docs", patterns=["*.md", "*.txt"])

    print("✅ Documents synced!")

asyncio.run(main())
```

**What happens**:
1. RAGVersion detects which documents changed
2. Only changed documents are re-embedded
3. Old versions are automatically removed from vector store
4. **Cost savings**: Up to 99% vs re-embedding everything

---

### Example 2: LangChain with Chunk-Level Versioning (80-95% Cost Savings!)

**Use Case**: Track changes at the **chunk level** for maximum cost optimization.

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.models import ChunkingConfig
from ragversion.integrations.langchain import LangChainSync

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

async def main():
    # 1. Configure chunk tracking (NEW in v0.10.0!)
    chunk_config = ChunkingConfig(
        enabled=True,           # Enable chunk-level tracking
        chunk_size=500,         # Tokens per chunk
        chunk_overlap=50,       # Overlap between chunks
        splitter_type="recursive"  # or "character"
    )

    # 2. Setup tracker with chunk tracking enabled
    storage = SQLiteStorage("ragversion.db")
    tracker = AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config
    )
    await tracker.initialize()

    # 3. Setup LangChain components
    embeddings = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    vectorstore = Chroma(
        collection_name="my_documents",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )

    # 4. Create sync with chunk tracking enabled
    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore,
        enable_chunk_tracking=True  # Smart chunk updates!
    )

    # 5. Sync directory - only changed chunks are re-embedded!
    await sync.sync_directory("./docs")

    print("✅ Smart chunk-level sync complete!")
    print("💰 Saved 80-95% on embedding costs!")

asyncio.run(main())
```

**Cost Savings Example**:
- **100-page document** with 1 paragraph changed
- Without chunk tracking: Re-embed all 500 chunks → $2.50
- With chunk tracking: Re-embed only 2 chunks → $0.01
- **Savings: 99.6%!**

---

### Example 3: LangChain with Custom Metadata

**Use Case**: Add custom metadata to tracked documents.

```python
from pathlib import Path

async def extract_metadata(file_path: str):
    """Extract custom metadata from file path."""
    path = Path(file_path)
    return {
        "category": path.parent.name,
        "author": "team",
        "tags": ["documentation", "important"]
    }

# Create sync with metadata extractor
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    metadata_extractor=extract_metadata  # Custom metadata!
)

await sync.sync_directory("./docs")
```

Now you can filter by custom metadata in your searches:

```python
# Query with metadata filter
results = vectorstore.similarity_search(
    "How do I install?",
    filter={"category": "getting-started"}
)
```

---

### Example 4: LangChain with Real-Time Watching

**Use Case**: Automatically sync when documents change on disk.

```python
import asyncio
from ragversion import AsyncVersionTracker, FileWatcher
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.integrations.langchain import LangChainSync

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

async def main():
    # Setup tracker
    storage = SQLiteStorage("ragversion.db")
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # Setup LangChain sync
    embeddings = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
    vectorstore = Chroma(
        collection_name="my_documents",
        embedding_function=embeddings
    )

    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore
    )

    # Initial sync
    await sync.sync_directory("./docs")
    print("✅ Initial sync complete")

    # Watch for changes (file watcher)
    watcher = FileWatcher(
        tracker=tracker,
        watch_paths=["./docs"],
        patterns=["*.md", "*.txt"],
        recursive=True
    )

    print("👀 Watching for changes... Press Ctrl+C to stop")
    await watcher.start()

    try:
        # Keep running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await watcher.stop()
        print("✅ Stopped watching")

asyncio.run(main())
```

**What happens**:
1. Initial sync of all documents
2. File watcher monitors `./docs` directory
3. When files change, tracker automatically detects it
4. LangChain callback automatically syncs to vector store
5. **Zero manual intervention needed!**

---

## LlamaIndex Integration

### Example 1: Basic LlamaIndex Sync

**Use Case**: Automatically sync changed documents to LlamaIndex.

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.integrations.llamaindex import LlamaIndexSync

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding

async def main():
    # 1. Setup RAGVersion tracker
    storage = SQLiteStorage("ragversion.db")
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # 2. Setup LlamaIndex components
    embed_model = OpenAIEmbedding()
    node_parser = SimpleNodeParser.from_defaults(
        chunk_size=1024,
        chunk_overlap=20
    )

    # Create index (or load existing)
    index = VectorStoreIndex(
        [],
        embed_model=embed_model
    )

    # 3. Create LlamaIndex sync
    sync = LlamaIndexSync(
        tracker=tracker,
        index=index,
        node_parser=node_parser
    )

    # 4. Sync directory
    await sync.sync_directory("./docs", patterns=["*.md", "*.txt"])

    print("✅ Documents synced to LlamaIndex!")

    # 5. Query the index
    query_engine = index.as_query_engine()
    response = query_engine.query("How do I install?")
    print(response)

asyncio.run(main())
```

---

### Example 2: LlamaIndex with Chunk-Level Versioning

**Use Case**: Maximum cost optimization with chunk-level tracking.

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.models import ChunkingConfig
from ragversion.integrations.llamaindex import LlamaIndexSync

from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding

async def main():
    # 1. Configure chunk tracking
    chunk_config = ChunkingConfig(
        enabled=True,
        chunk_size=512,
        chunk_overlap=50,
        splitter_type="recursive"
    )

    # 2. Setup tracker with chunks
    storage = SQLiteStorage("ragversion.db")
    tracker = AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config
    )
    await tracker.initialize()

    # 3. Setup LlamaIndex
    embed_model = OpenAIEmbedding()
    index = VectorStoreIndex([], embed_model=embed_model)

    # 4. Create sync with chunk tracking
    sync = LlamaIndexSync(
        tracker=tracker,
        index=index,
        enable_chunk_tracking=True  # Smart chunk updates!
    )

    # 5. Sync with chunk-level optimization
    await sync.sync_directory("./docs")

    print("✅ Smart chunk-level sync complete!")
    print("💰 Saved 80-95% on embedding costs!")

asyncio.run(main())
```

---

### Example 3: LlamaIndex with Persistent Storage

**Use Case**: Use persistent vector store (e.g., Pinecone, Weaviate).

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.integrations.llamaindex import LlamaIndexSync

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import pinecone

async def main():
    # 1. Setup Pinecone
    pinecone.init(api_key="YOUR_API_KEY", environment="us-east1-gcp")
    pinecone_index = pinecone.Index("my-index")
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

    # 2. Setup RAGVersion
    storage = SQLiteStorage("ragversion.db")
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # 3. Create LlamaIndex with Pinecone
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )
    embed_model = OpenAIEmbedding()
    index = VectorStoreIndex(
        [],
        storage_context=storage_context,
        embed_model=embed_model
    )

    # 4. Create sync
    sync = LlamaIndexSync(
        tracker=tracker,
        index=index
    )

    # 5. Sync to Pinecone
    await sync.sync_directory("./docs")

    print("✅ Synced to Pinecone!")

asyncio.run(main())
```

---

## Chunk-Level Versioning

### What is Chunk-Level Versioning?

Instead of re-embedding **entire documents** when they change, RAGVersion v0.10.0+ tracks changes at the **chunk level** and only re-embeds the chunks that actually changed.

**Result**: **80-95% cost reduction** on embedding operations!

### How It Works

```python
# Without chunk tracking (OLD)
Document changes → Delete ALL chunks → Re-embed ALL chunks → $$$

# With chunk tracking (NEW in v0.10.0)
Document changes → Detect changed chunks → Re-embed ONLY changed chunks → $
```

### Configuration Options

```python
from ragversion.models import ChunkingConfig

# Configuration
chunk_config = ChunkingConfig(
    enabled=True,                # Enable chunk tracking
    chunk_size=500,              # Tokens per chunk (default: 500)
    chunk_overlap=50,            # Overlap between chunks (default: 50)
    splitter_type="recursive",   # "recursive" or "character"
    store_chunk_content=True     # Store chunk content (for debugging)
)
```

### Example: Track with Chunks

```python
from ragversion import AsyncVersionTracker
from ragversion.models import ChunkingConfig

# Setup with chunks
chunk_config = ChunkingConfig(enabled=True)
tracker = AsyncVersionTracker(
    storage=storage,
    chunk_tracking_enabled=True,
    chunk_config=chunk_config
)
await tracker.initialize()

# Track file
event, chunk_diff = await tracker.track_with_chunks("document.md")

if chunk_diff:
    print(f"Total chunks: {chunk_diff.total_chunks}")
    print(f"Added: {len(chunk_diff.added_chunks)}")
    print(f"Removed: {len(chunk_diff.removed_chunks)}")
    print(f"Unchanged: {len(chunk_diff.unchanged_chunks)}")
    print(f"💰 Savings: {chunk_diff.savings_percentage:.1f}%")
```

**Output Example**:
```
Total chunks: 50
Added: 3
Removed: 2
Unchanged: 47
💰 Savings: 94.0%
```

### Getting Chunk Diff Between Versions

```python
from uuid import UUID

# Get chunk diff between two versions
chunk_diff = await tracker.get_chunk_diff(
    document_id=UUID("..."),
    from_version=1,
    to_version=2
)

if chunk_diff:
    # See exactly what changed
    for chunk in chunk_diff.added_chunks:
        print(f"Added chunk {chunk.chunk_index}: {chunk.content_hash}")

    for chunk in chunk_diff.removed_chunks:
        print(f"Removed chunk {chunk.chunk_index}: {chunk.content_hash}")
```

---

## Common Use Cases

### Use Case 1: Documentation Site

**Scenario**: Keep your RAG chatbot synced with documentation changes.

```python
import asyncio
from ragversion import AsyncVersionTracker, FileWatcher
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.integrations.langchain import LangChainSync
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import MarkdownTextSplitter

async def sync_documentation():
    # Setup
    storage = SQLiteStorage("docs.db")
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    embeddings = OpenAIEmbeddings()
    text_splitter = MarkdownTextSplitter(chunk_size=1000)
    vectorstore = Chroma(
        collection_name="documentation",
        embedding_function=embeddings,
        persist_directory="./chroma_docs"
    )

    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore
    )

    # Initial sync
    await sync.sync_directory("./docs", patterns=["*.md"], recursive=True)

    # Watch for changes
    watcher = FileWatcher(
        tracker=tracker,
        watch_paths=["./docs"],
        patterns=["*.md"],
        recursive=True
    )

    await watcher.start()

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await watcher.stop()

asyncio.run(sync_documentation())
```

---

### Use Case 2: Customer Support Knowledge Base

**Scenario**: Track changes to support articles and sync to vector store.

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.models import ChunkingConfig
from ragversion.integrations.langchain import LangChainSync
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

async def sync_knowledge_base():
    # Chunk-level tracking for cost optimization
    chunk_config = ChunkingConfig(
        enabled=True,
        chunk_size=500,
        chunk_overlap=50
    )

    storage = SQLiteStorage("knowledge_base.db")
    tracker = AsyncVersionTracker(
        storage=storage,
        chunk_tracking_enabled=True,
        chunk_config=chunk_config
    )
    await tracker.initialize()

    # Setup Pinecone
    embeddings = OpenAIEmbeddings()
    vectorstore = PineconeVectorStore(
        index_name="support-kb",
        embedding=embeddings
    )

    # Custom metadata extractor
    def extract_metadata(file_path: str):
        from pathlib import Path
        path = Path(file_path)
        return {
            "category": path.parent.name,
            "product": "main_product",
            "last_updated": path.stat().st_mtime
        }

    sync = LangChainSync(
        tracker=tracker,
        embeddings=embeddings,
        vectorstore=vectorstore,
        metadata_extractor=extract_metadata,
        enable_chunk_tracking=True
    )

    # Sync knowledge base
    await sync.sync_directory("./knowledge_base")

    print("✅ Knowledge base synced with chunk-level optimization!")

asyncio.run(sync_knowledge_base())
```

---

### Use Case 3: Research Paper Repository

**Scenario**: Track PDF research papers and maintain embeddings.

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.integrations.llamaindex import LlamaIndexSync
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding

async def sync_research_papers():
    # Setup
    storage = SQLiteStorage("research.db")
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # LlamaIndex setup
    embed_model = OpenAIEmbedding()
    index = VectorStoreIndex([], embed_model=embed_model)

    sync = LlamaIndexSync(
        tracker=tracker,
        index=index
    )

    # Sync PDF papers
    await sync.sync_directory(
        "./papers",
        patterns=["*.pdf"],
        recursive=True
    )

    print("✅ Research papers indexed!")

    # Query
    query_engine = index.as_query_engine()
    response = query_engine.query(
        "What are the latest findings on transformer architectures?"
    )
    print(response)

asyncio.run(sync_research_papers())
```

---

### Use Case 4: Multi-Tenant Application

**Scenario**: Track documents per tenant with isolated storage.

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.integrations.langchain import LangChainSync
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

async def sync_tenant_documents(tenant_id: str):
    # Separate database per tenant
    storage = SQLiteStorage(f"tenant_{tenant_id}.db")
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # Separate collection per tenant
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        collection_name=f"tenant_{tenant_id}",
        embedding_function=embeddings,
        persist_directory=f"./chroma_tenant_{tenant_id}"
    )

    sync = LangChainSync(
        tracker=tracker,
        embeddings=embeddings,
        vectorstore=vectorstore
    )

    # Sync tenant's documents
    await sync.sync_directory(f"./tenants/{tenant_id}/documents")

    print(f"✅ Synced documents for tenant {tenant_id}")

# Sync multiple tenants
async def main():
    tenants = ["acme_corp", "globex", "initech"]
    await asyncio.gather(*[
        sync_tenant_documents(tenant_id)
        for tenant_id in tenants
    ])

asyncio.run(main())
```

---

## Best Practices

### 1. Use Chunk-Level Versioning for Cost Optimization

```python
# ✅ GOOD: Enable chunks for maximum savings
chunk_config = ChunkingConfig(enabled=True)
tracker = AsyncVersionTracker(
    storage=storage,
    chunk_tracking_enabled=True,
    chunk_config=chunk_config
)
```

### 2. Match Chunk Sizes Between RAGVersion and Your Splitter

```python
# ✅ GOOD: Consistent chunk sizes
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# RAGVersion config
chunk_config = ChunkingConfig(
    enabled=True,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)

# LangChain splitter (same sizes!)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)
```

### 3. Use SQLite for Development, Supabase for Production

```python
# Development
from ragversion.storage.sqlite import SQLiteStorage
storage = SQLiteStorage("dev.db")

# Production
from ragversion.storage.supabase import SupabaseStorage
storage = SupabaseStorage.from_env()  # Uses SUPABASE_URL and SUPABASE_SERVICE_KEY
```

### 4. Add Custom Metadata for Better Filtering

```python
def extract_metadata(file_path: str):
    """Extract meaningful metadata."""
    from pathlib import Path
    import re

    path = Path(file_path)

    # Extract category from path
    category = path.parent.name

    # Extract date from filename (if present)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', path.name)
    date = date_match.group(1) if date_match else None

    return {
        "category": category,
        "date": date,
        "filename": path.name,
        "extension": path.suffix
    }

sync = LangChainSync(
    tracker=tracker,
    # ...
    metadata_extractor=extract_metadata
)
```

### 5. Use File Watching for Real-Time Sync

```python
# ✅ GOOD: Automatic syncing
watcher = FileWatcher(
    tracker=tracker,
    watch_paths=["./docs"],
    patterns=["*.md", "*.txt"],
    recursive=True
)
await watcher.start()
```

### 6. Handle Errors Gracefully

```python
from ragversion.exceptions import RAGVersionError, StorageError

try:
    await sync.sync_directory("./docs")
except StorageError as e:
    print(f"Storage error: {e}")
    # Handle storage issues
except RAGVersionError as e:
    print(f"RAGVersion error: {e}")
    # Handle other errors
```

### 7. Monitor Savings

```python
# Track savings over time
result = await tracker.track_with_chunks("document.md")
event, chunk_diff = result

if chunk_diff:
    # Log savings metrics
    print(f"Document: {event.file_name}")
    print(f"Savings: {chunk_diff.savings_percentage:.1f}%")
    print(f"Chunks re-embedded: {len(chunk_diff.added_chunks)}/{chunk_diff.total_chunks}")
```

---

## Troubleshooting

### Issue 1: "No module named 'langchain'"

**Problem**: LangChain not installed.

**Solution**:
```bash
pip install "ragversion[langchain]"
```

---

### Issue 2: Chunk tracking not working

**Problem**: Chunks enabled but not tracking.

**Solution**: Verify both tracker and integration have chunk tracking enabled:

```python
# ✅ Enable in BOTH places
tracker = AsyncVersionTracker(
    storage=storage,
    chunk_tracking_enabled=True,  # Here
    chunk_config=ChunkingConfig(enabled=True)
)

sync = LangChainSync(
    tracker=tracker,
    # ...
    enable_chunk_tracking=True  # And here
)
```

---

### Issue 3: "Database is locked" error

**Problem**: SQLite database locked (multiple processes).

**Solution**: Use Supabase for production or ensure only one process accesses SQLite:

```python
# For production
from ragversion.storage.supabase import SupabaseStorage
storage = SupabaseStorage.from_env()
```

---

### Issue 4: High memory usage with large documents

**Problem**: Large documents causing memory issues.

**Solution**: Use larger chunk sizes to reduce chunk count:

```python
# ✅ Larger chunks for large documents
chunk_config = ChunkingConfig(
    enabled=True,
    chunk_size=1000,  # Larger chunks
    chunk_overlap=100,
    store_chunk_content=False  # Don't store content if not needed
)
```

---

### Issue 5: Documents not syncing automatically

**Problem**: File watcher not detecting changes.

**Solution**: Check file watcher configuration:

```python
# ✅ Ensure correct patterns and paths
watcher = FileWatcher(
    tracker=tracker,
    watch_paths=["./docs"],  # Absolute or relative paths
    patterns=["*.md", "*.txt"],  # File extensions
    recursive=True,  # Watch subdirectories
    debounce_seconds=1.0  # Adjust if needed
)
```

---

### Issue 6: Vector store not updating

**Problem**: Changes tracked but vector store not synced.

**Solution**: Ensure callback is registered:

```python
# The LangChainSync constructor automatically registers callback
sync = LangChainSync(tracker=tracker, ...)

# Or manually register
tracker.on_change(your_callback_function)
```

---

## Environment Variables

### For Supabase Storage

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### For Chunk Tracking

```bash
# .env file
RAGVERSION_CHUNK_ENABLED=true
RAGVERSION_CHUNK_CHUNK_SIZE=500
RAGVERSION_CHUNK_CHUNK_OVERLAP=50
RAGVERSION_CHUNK_SPLITTER_TYPE=recursive
```

### For OpenAI (LangChain/LlamaIndex)

```bash
# .env file
OPENAI_API_KEY=sk-...
```

---

## Complete Example: Production-Ready Setup

Here's a complete, production-ready example combining all best practices:

```python
import asyncio
import logging
from pathlib import Path
from ragversion import AsyncVersionTracker, FileWatcher
from ragversion.storage.supabase import SupabaseStorage
from ragversion.models import ChunkingConfig
from ragversion.integrations.langchain import LangChainSync
from ragversion.exceptions import RAGVersionError

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

async def main():
    try:
        # 1. Setup storage (Supabase for production)
        storage = SupabaseStorage.from_env()

        # 2. Configure chunk tracking
        chunk_config = ChunkingConfig(
            enabled=True,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            splitter_type="recursive"
        )

        # 3. Initialize tracker
        tracker = AsyncVersionTracker(
            storage=storage,
            chunk_tracking_enabled=True,
            chunk_config=chunk_config
        )
        await tracker.initialize()
        logger.info("✅ Tracker initialized")

        # 4. Setup LangChain components
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        vectorstore = PineconeVectorStore(
            index_name="production-index",
            embedding=embeddings
        )

        # 5. Custom metadata extractor
        def extract_metadata(file_path: str):
            path = Path(file_path)
            return {
                "category": path.parent.name,
                "environment": "production",
                "source": "docs"
            }

        # 6. Create sync
        sync = LangChainSync(
            tracker=tracker,
            text_splitter=text_splitter,
            embeddings=embeddings,
            vectorstore=vectorstore,
            metadata_extractor=extract_metadata,
            enable_chunk_tracking=True
        )

        # 7. Initial sync
        logger.info("Starting initial sync...")
        await sync.sync_directory(
            "./docs",
            patterns=["*.md", "*.txt"],
            recursive=True
        )
        logger.info("✅ Initial sync complete")

        # 8. Setup file watcher
        watcher = FileWatcher(
            tracker=tracker,
            watch_paths=["./docs"],
            patterns=["*.md", "*.txt"],
            recursive=True,
            debounce_seconds=2.0
        )

        logger.info("👀 Starting file watcher...")
        await watcher.start()

        # 9. Keep running
        logger.info("✅ System running. Press Ctrl+C to stop.")
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await watcher.stop()
        await tracker.close()
        logger.info("✅ Shutdown complete")

    except RAGVersionError as e:
        logger.error(f"RAGVersion error: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Next Steps

### Learn More

- **[Chunk Versioning Guide](docs/CHUNK_VERSIONING.md)** - Deep dive into chunk-level optimization
- **[API Reference](docs/API_GUIDE.md)** - Complete API documentation
- **[GitHub Repository](https://github.com/sourangshupal/ragversion)** - Source code and examples

### Get Help

- **GitHub Issues**: https://github.com/sourangshupal/ragversion/issues
- **Discussions**: https://github.com/sourangshupal/ragversion/discussions
- **PyPI**: https://pypi.org/project/ragversion/

---

## Summary

**RAGVersion** makes it incredibly easy to:

1. ✅ Track document changes automatically
2. ✅ Sync only what changed (99% cost savings)
3. ✅ Optimize at chunk-level (80-95% cost savings)
4. ✅ Integrate with LangChain or LlamaIndex in minutes
5. ✅ Watch files and sync in real-time
6. ✅ Add custom metadata for better filtering

**Get started in 3 steps**:

```bash
# 1. Install
pip install "ragversion[all]"

# 2. Create script (see examples above)
# 3. Run!
python your_script.py
```

**Result**: Massive cost savings and always-fresh vector stores! 🎉

---

**Happy building!** 🚀

For questions or issues, visit: https://github.com/sourangshupal/ragversion

# RAGVersion Quick Start Guide

This guide shows you how to get started with RAGVersion in minutes, not hours.

## Table of Contents

- [Installation](#installation)
- [LangChain Integration](#langchain-integration)
- [LlamaIndex Integration](#llamaindex-integration)
- [Customization](#customization)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Basic Installation

```bash
# Install with LangChain support
pip install ragversion[langchain]

# Install with LlamaIndex support
pip install ragversion[llamaindex]

# Install with both (recommended)
pip install ragversion[all]
```

### Environment Setup

Set your OpenAI API key (required for embeddings):

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Optional: Set Supabase credentials for cloud storage:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

---

## LangChain Integration

### Simplest Possible Setup (3 lines!)

```python
from ragversion.integrations.langchain import quick_start

# That's it! Documents are tracked and synced to vector store
sync = await quick_start("./documents")
```

**What just happened?**
1. ✅ Created RAGVersion tracker with SQLite storage
2. ✅ Initialized FAISS vector store
3. ✅ Set up OpenAI embeddings
4. ✅ Created text splitter (1000 char chunks, 200 overlap)
5. ✅ Tracked all documents in `./documents`
6. ✅ Embedded documents into vector store
7. ✅ Enabled smart chunk-level tracking for future updates

### Using the Integration

```python
from ragversion.integrations.langchain import quick_start

# Setup
sync = await quick_start("./documents")

# Query the vector store
results = await sync.vectorstore.asimilarity_search("What are the features?", k=5)
for doc in results:
    print(doc.page_content)
    print(doc.metadata)

# Track new files (automatically updates vector store)
await sync.tracker.track("./new_document.pdf")

# Cleanup
await sync.tracker.close()
```

### Complete Example

```python
import asyncio
from ragversion.integrations.langchain import quick_start

async def main():
    # Quick start with default settings
    sync = await quick_start("./documents")

    print(f"✓ Tracker initialized")
    print(f"✓ Vector store ready")
    print(f"✓ Documents synced")

    # Use the vector store
    query = "Tell me about RAGVersion"
    results = await sync.vectorstore.asimilarity_search(query, k=3)

    print(f"\nQuery: {query}")
    print(f"Found {len(results)} results:\n")

    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc.metadata.get('file_name', 'Unknown')}")
        print(f"   {doc.page_content[:200]}...\n")

    # Cleanup
    await sync.tracker.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## LlamaIndex Integration

### Simplest Possible Setup (3 lines!)

```python
from ragversion.integrations.llamaindex import quick_start

# That's it! Documents are tracked and indexed
sync = await quick_start("./documents")
```

**What just happened?**
1. ✅ Created RAGVersion tracker with SQLite storage
2. ✅ Initialized VectorStoreIndex
3. ✅ Set up OpenAI embeddings
4. ✅ Created node parser (1024 char chunks, 20 overlap)
5. ✅ Tracked all documents in `./documents`
6. ✅ Indexed documents
7. ✅ Enabled smart chunk-level tracking for future updates

### Using the Integration

```python
from ragversion.integrations.llamaindex import quick_start

# Setup
sync = await quick_start("./documents")

# Query the index
query_engine = sync.index.as_query_engine()
response = query_engine.query("What are the features?")
print(response)

# Use as retriever
retriever = sync.index.as_retriever(similarity_top_k=5)
nodes = retriever.retrieve("sample query")
for node in nodes:
    print(f"Score: {node.score:.4f}")
    print(f"Text: {node.text[:200]}...")

# Track new files (automatically updates index)
await sync.tracker.track("./new_document.pdf")

# Cleanup
await sync.tracker.close()
```

### Complete Example

```python
import asyncio
from ragversion.integrations.llamaindex import quick_start

async def main():
    # Quick start with default settings
    sync = await quick_start("./documents")

    print(f"✓ Tracker initialized")
    print(f"✓ Index ready")
    print(f"✓ Documents indexed")

    # Query the index
    query_engine = sync.index.as_query_engine()
    response = query_engine.query("Tell me about RAGVersion features")

    print(f"\nQuery: Tell me about RAGVersion features")
    print(f"Response: {response}\n")

    # Retrieve similar documents
    retriever = sync.index.as_retriever(similarity_top_k=3)
    nodes = retriever.retrieve("document tracking")

    print(f"Retrieved {len(nodes)} nodes:")
    for i, node in enumerate(nodes, 1):
        print(f"\n{i}. Score: {node.score:.4f}")
        print(f"   {node.text[:200]}...")

    # Cleanup
    await sync.tracker.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Customization

### Vector Store Options (LangChain)

#### FAISS (In-Memory, Fast)

```python
sync = await quick_start(
    directory="./documents",
    vectorstore_type="faiss",
)

# Save FAISS index for later
sync.vectorstore.save_local("./my_vectorstore")

# Load existing index
sync = await quick_start(
    directory="./documents",
    vectorstore_type="faiss",
    vectorstore_path="./my_vectorstore",  # Load from here
)
```

#### Chroma (Persistent)

```python
sync = await quick_start(
    directory="./documents",
    vectorstore_type="chroma",
    vectorstore_path="./chroma_db",  # Persistent storage
)
```

### Storage Backend Options

#### SQLite (Default, Local)

```python
sync = await quick_start(
    directory="./documents",
    storage_backend="sqlite",  # Uses ragversion.db
)
```

#### Supabase (Cloud, Collaborative)

```python
# Requires SUPABASE_URL and SUPABASE_SERVICE_KEY env vars
sync = await quick_start(
    directory="./documents",
    storage_backend="supabase",
)
```

#### Auto-Detection

```python
# Automatically uses Supabase if env vars are set, otherwise SQLite
sync = await quick_start(
    directory="./documents",
    storage_backend="auto",  # Default
)
```

### Chunk Size Configuration

#### LangChain

```python
sync = await quick_start(
    directory="./documents",
    chunk_size=500,        # Smaller chunks
    chunk_overlap=100,     # Less overlap
)

# Or larger chunks for long documents
sync = await quick_start(
    directory="./documents",
    chunk_size=2000,       # Larger chunks
    chunk_overlap=400,     # More overlap
)
```

#### LlamaIndex

```python
sync = await quick_start(
    directory="./documents",
    chunk_size=2048,       # Larger chunks for long docs
    chunk_overlap=200,     # More overlap
)
```

### Custom Embeddings

#### LangChain

```python
from langchain_openai import OpenAIEmbeddings

custom_embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=1536,
)

sync = await quick_start(
    directory="./documents",
    embeddings=custom_embeddings,
)
```

#### LlamaIndex

```python
from llama_index.embeddings.openai import OpenAIEmbedding

custom_embeddings = OpenAIEmbedding(
    model="text-embedding-3-small",
    dimensions=1536,
)

sync = await quick_start(
    directory="./documents",
    embeddings=custom_embeddings,
)
```

### Disable Chunk Tracking

By default, chunk tracking is enabled for 80-95% cost savings on updates. To disable:

```python
sync = await quick_start(
    directory="./documents",
    enable_chunk_tracking=False,  # Full re-embedding on updates
)
```

---

## Common Patterns

### Pattern 1: Development with SQLite, Production with Supabase

```python
import os
from ragversion.integrations.langchain import quick_start

async def setup():
    # Auto-detects: Supabase in production, SQLite in development
    sync = await quick_start(
        directory="./documents",
        storage_backend="auto",
    )
    return sync
```

### Pattern 2: Persistent FAISS Index

```python
from pathlib import Path
from ragversion.integrations.langchain import quick_start

async def setup():
    index_path = "./my_vectorstore"

    # Create or load existing
    sync = await quick_start(
        directory="./documents",
        vectorstore_type="faiss",
        vectorstore_path=index_path if Path(index_path).exists() else None,
    )

    # Save after updates
    sync.vectorstore.save_local(index_path)

    return sync
```

### Pattern 3: Multiple Document Types

```python
sync = await quick_start(
    directory="./documents",
    file_patterns=["*.pdf", "*.docx", "*.txt", "*.md"],  # Customize patterns
)
```

### Pattern 4: Monitoring Changes

```python
from ragversion.integrations.langchain import quick_start

# Setup
sync = await quick_start("./documents")

# Register custom callback
def on_document_change(event):
    print(f"Document {event.file_name} was {event.change_type}")
    print(f"Version: {event.version_number}")

sync.tracker.on_change(on_document_change)

# Now track new files
await sync.tracker.track("./new_doc.pdf")
# → Callback will be triggered!
```

---

## Troubleshooting

### Issue: "OpenAI API key not found"

**Solution:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or pass custom embeddings:
```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(api_key="your-key")
sync = await quick_start("./documents", embeddings=embeddings)
```

### Issue: "LangChain not installed"

**Solution:**
```bash
pip install ragversion[langchain]
# or
pip install ragversion[all]
```

### Issue: "Supabase credentials not found"

**Solution:**
Either set environment variables:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

Or use SQLite explicitly:
```python
sync = await quick_start("./documents", storage_backend="sqlite")
```

### Issue: "Database locked" (SQLite)

**Cause:** Multiple processes accessing the same SQLite database.

**Solution:** Use Supabase for multi-process scenarios:
```python
sync = await quick_start("./documents", storage_backend="supabase")
```

### Issue: "Memory error with large documents"

**Solution:** Use smaller chunk sizes:
```python
sync = await quick_start(
    directory="./documents",
    chunk_size=500,  # Smaller chunks
)
```

### Issue: "Slow initial sync"

**Cause:** Processing many documents takes time.

**Solution:** This is normal. Monitor progress:
```python
import logging
logging.basicConfig(level=logging.INFO)

sync = await quick_start("./documents")
# You'll see progress logs
```

---

## Next Steps

- 📖 [Read the complete How-to Guide](../How_to.md) for advanced features
- 📚 [Check out the Integration Guide](../INTEGRATION_GUIDE.md) for detailed patterns
- 💡 [Browse examples](../examples/) for more use cases
- 🔧 [Configure advanced settings](../DOCUMENTATION.md) for production

---

## Before vs After Comparison

### LangChain: 35 lines → 3 lines (91% reduction)

**Before:**
```python
from langchain.text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage
from ragversion.integrations.langchain import LangChainSync

# Storage setup (4 lines)
storage = SupabaseStorage.from_env()

# Tracker setup (3 lines)
tracker = AsyncVersionTracker(storage=storage, store_content=True)
await tracker.initialize()

# LangChain components (15 lines)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(["placeholder"], embeddings)

# Integration (8 lines)
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
)

# Sync (4 lines)
await sync.sync_directory("./documents", patterns=["*.txt", "*.md", "*.pdf"])
```

**After:**
```python
from ragversion.integrations.langchain import quick_start

sync = await quick_start("./documents")
```

### LlamaIndex: 20 lines → 3 lines (85% reduction)

**Before:**
```python
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage
from ragversion.integrations.llamaindex import LlamaIndexSync

# Storage setup (4 lines)
storage = SQLiteStorage()

# Tracker setup (3 lines)
tracker = AsyncVersionTracker(storage=storage, store_content=True)
await tracker.initialize()

# LlamaIndex components (8 lines)
embeddings = OpenAIEmbedding()
node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
index = VectorStoreIndex.from_documents([], embed_model=embeddings)

# Integration (6 lines)
sync = LlamaIndexSync(tracker=tracker, index=index, node_parser=node_parser)

# Sync (4 lines)
await sync.sync_directory("./documents", patterns=["*.txt", "*.md", "*.pdf"])
```

**After:**
```python
from ragversion.integrations.llamaindex import quick_start

sync = await quick_start("./documents")
```

---

**Questions or issues?** Open an issue on [GitHub](https://github.com/sourangshupal/ragversion/issues)

# Migration Guide

This guide helps you adopt RAGVersion in existing projects and migrate between different configurations.

## Table of Contents

- [Migrating to RAGVersion](#migrating-to-ragversion)
  - [From Manual File Tracking](#from-manual-file-tracking)
  - [From LangChain Without RAGVersion](#from-langchain-without-ragversion)
  - [From LlamaIndex Without RAGVersion](#from-llamaindex-without-ragversion)
- [Migrating Between Storage Backends](#migrating-between-storage-backends)
  - [SQLite to Supabase](#sqlite-to-supabase)
  - [Supabase to SQLite](#supabase-to-sqlite)
- [Backfilling Version History](#backfilling-version-history)
- [Upgrading RAGVersion](#upgrading-ragversion)

---

## Migrating to RAGVersion

### From Manual File Tracking

If you're currently tracking files manually with hashes or timestamps, RAGVersion can replace your custom solution.

**Before: Custom file tracking**
```python
import hashlib
import os
import json

# Your existing code
tracked_files = {}

for file in os.listdir("docs"):
    file_path = os.path.join("docs", file)
    with open(file_path, 'rb') as f:
        content = f.read()
        hash = hashlib.sha256(content).hexdigest()

    if file not in tracked_files or tracked_files[file] != hash:
        # Handle change
        print(f"Changed: {file}")
        tracked_files[file] = hash

# Save state
with open("tracked_files.json", "w") as f:
    json.dump(tracked_files, f)
```

**After: RAGVersion**
```python
import asyncio
from ragversion import AsyncVersionTracker

async def main():
    async with await AsyncVersionTracker.create() as tracker:
        # Automatically detects changes and versions
        result = await tracker.track_directory("docs")
        print(f"Tracked {result.success_count} files")

asyncio.run(main())
```

**Benefits:**
- ✅ Automatic change detection
- ✅ Version history stored in database
- ✅ Content diffing between versions
- ✅ Async/await for better performance
- ✅ No manual state management

---

### From LangChain Without RAGVersion

If you're using LangChain and manually re-indexing documents, RAGVersion can automate updates.

**Before: Manual re-indexing**
```python
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Re-index everything on every run (slow!)
loader = DirectoryLoader("docs")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
chunks = text_splitter.split_documents(docs)

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embeddings)
# This re-embeds ALL documents every time
```

**After: Smart incremental updates**
```python
from ragversion.integrations.langchain import quick_start

# Only updates changed files (fast!)
sync = await quick_start("docs")
# Automatically tracks changes and updates only what changed
```

**Benefits:**
- ✅ Only re-embed changed documents
- ✅ 80-95% cost savings on embeddings (with chunk tracking)
- ✅ Automatic version tracking
- ✅ 3-line setup instead of 35+ lines

**Migration steps:**

1. Install RAGVersion:
   ```bash
   pip install ragversion[langchain]
   ```

2. Replace your existing code with quick_start:
   ```python
   from ragversion.integrations.langchain import quick_start

   async def main():
       # One-time setup
       sync = await quick_start("./docs")

       # Your vectorstore is ready
       results = await sync.vectorstore.asimilarity_search("query")

   asyncio.run(main())
   ```

3. (Optional) Migrate existing embeddings:
   ```python
   # If you have existing FAISS index, you can keep using it
   sync = await quick_start(
       directory="./docs",
       vectorstore=your_existing_vectorstore  # Pass your existing store
   )
   ```

---

### From LlamaIndex Without RAGVersion

Similar to LangChain, RAGVersion automates document updates for LlamaIndex.

**Before: Manual re-indexing**
```python
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding

# Re-index everything every time
documents = SimpleDirectoryReader("docs").load_data()
embeddings = OpenAIEmbedding()
index = VectorStoreIndex.from_documents(documents, embed_model=embeddings)
```

**After: Smart incremental updates**
```python
from ragversion.integrations.llamaindex import quick_start

# Only updates changed documents
sync = await quick_start("docs")
query_engine = sync.index.as_query_engine()
```

**Migration steps:**

1. Install RAGVersion:
   ```bash
   pip install ragversion[llamaindex]
   ```

2. Replace indexing code:
   ```python
   from ragversion.integrations.llamaindex import quick_start

   async def main():
       sync = await quick_start("./docs")

       # Query as normal
       query_engine = sync.index.as_query_engine()
       response = query_engine.query("What is...?")

   asyncio.run(main())
   ```

---

## Migrating Between Storage Backends

### SQLite to Supabase

When moving from local development (SQLite) to production (Supabase):

**Step 1: Set up Supabase**
```bash
# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"

# Run migrations
ragversion migrate
```

**Step 2: Export from SQLite**

Currently, you'll need to re-track documents. Direct migration support is coming soon.

```python
# Re-track with Supabase
async with await AsyncVersionTracker.create("supabase") as tracker:
    result = await tracker.track_directory("./docs")
    print(f"Migrated {result.success_count} files")
```

**Step 3: Update your code**
```python
# Before (SQLite)
tracker = await AsyncVersionTracker.create()

# After (Supabase)
tracker = await AsyncVersionTracker.create("supabase")
```

---

### Supabase to SQLite

When moving from Supabase back to SQLite (e.g., for local development):

**Step 1: Re-track locally**
```python
# Use SQLite
async with await AsyncVersionTracker.create("sqlite") as tracker:
    result = await tracker.track_directory("./docs")
```

**Step 2: Update your code**
```python
# Before (Supabase)
tracker = await AsyncVersionTracker.create("supabase")

# After (SQLite)
tracker = await AsyncVersionTracker.create()  # SQLite is default
```

---

## Backfilling Version History

If you have existing files you want to track:

### Initial Baseline

```python
async def establish_baseline():
    """Track all existing files to establish version 1."""
    async with await AsyncVersionTracker.create() as tracker:
        result = await tracker.track_directory(
            "./documents",
            patterns=["*.pdf", "*.docx", "*.txt"],
            recursive=True
        )

        print(f"✓ Baseline: {result.success_count} files at version 1")
        print(f"✗ Failed: {result.failure_count} files")

        if result.failed:
            print("\nFailed files:")
            for error in result.failed:
                print(f"  - {error.file_path}: {error.error_type}")

asyncio.run(establish_baseline())
```

### Batch Processing Large Collections

For very large document collections:

```python
async def batch_track_large_collection():
    """Track large collections in batches."""
    import os
    from pathlib import Path

    async with await AsyncVersionTracker.create(
        max_file_size_mb=100  # Increase if needed
    ) as tracker:

        # Get all files
        all_files = list(Path("./documents").rglob("*"))
        total = len(all_files)

        print(f"Found {total} files to track")

        # Process in batches
        batch_size = 100
        for i in range(0, total, batch_size):
            batch = all_files[i:i+batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}...")

            for file_path in batch:
                if file_path.is_file():
                    try:
                        result = await tracker.track(str(file_path))
                        if result.changed:
                            print(f"  ✓ {file_path.name}")
                    except Exception as e:
                        print(f"  ✗ {file_path.name}: {e}")

        print(f"\n✓ Batch processing complete")

asyncio.run(batch_track_large_collection())
```

---

## Upgrading RAGVersion

### From v0.10.x to v0.11.x

**Key changes:**
- Added `quick_start()` functions for LangChain/LlamaIndex
- Added factory method `AsyncVersionTracker.create()`
- Added `TrackResult` return type

**Update your code:**

```python
# Before v0.11.0
from ragversion.storage import SQLiteStorage

storage = SQLiteStorage()
tracker = AsyncVersionTracker(storage=storage)
await tracker.initialize()

event = await tracker.track("file.pdf")
if event:  # Could be None
    print(event.change_type)

# After v0.11.0 (recommended)
tracker = await AsyncVersionTracker.create()  # Factory method

result = await tracker.track("file.pdf")
if result.changed:  # Always returns result
    print(result.change_type)
```

**Breaking changes:** None - v0.11.0 is fully backward compatible

---

### From v0.9.x to v0.10.x

**Key changes:**
- Added chunk-level tracking
- Added change frequency analytics

**Update your code:**

```python
# Enable chunk tracking (new in v0.10.0)
from ragversion.models import ChunkingConfig

tracker = await AsyncVersionTracker.create(
    chunk_tracking_enabled=True,
    chunk_config=ChunkingConfig(
        chunk_size=1000,
        chunk_overlap=200
    )
)
```

---

## Common Migration Scenarios

### Scenario 1: Adding RAGVersion to Existing RAG Application

**You have:** LangChain/LlamaIndex app with manual document loading

**Goal:** Add automatic change tracking

**Steps:**
1. Install: `pip install ragversion[langchain]` or `ragversion[llamaindex]`
2. Replace loader with `quick_start()`
3. Run initial sync to establish baseline
4. Enjoy automatic updates!

---

### Scenario 2: Moving from Development to Production

**You have:** Working RAGVersion setup with SQLite

**Goal:** Deploy to production with Supabase

**Steps:**
1. Set up Supabase project
2. Run migrations in Supabase
3. Update code to use `create("supabase")`
4. Re-track documents (or wait for migration tool)
5. Update deployment config

---

### Scenario 3: Multi-Environment Setup

**You have:** Development and production environments

**Goal:** Use SQLite locally, Supabase in production

**Steps:**

```python
import os

# Environment-aware tracker creation
async def get_tracker():
    if os.getenv("ENVIRONMENT") == "production":
        return await AsyncVersionTracker.create("supabase")
    else:
        return await AsyncVersionTracker.create("sqlite")

# Use in your app
async with await get_tracker() as tracker:
    result = await tracker.track_directory("./docs")
```

---

## Need Help?

- **Questions?** [GitHub Discussions](https://github.com/sourangshupal/ragversion/discussions)
- **Issues?** [GitHub Issues](https://github.com/sourangshupal/ragversion/issues)
- **Documentation:** [README](../README.md) | [Tutorial](5-MINUTE-TUTORIAL.md)

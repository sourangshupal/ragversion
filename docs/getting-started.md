# Getting Started with RAGVersion

This guide will help you get started with RAGVersion, the async-first version tracking system for RAG applications.

## Installation

Install RAGVersion with pip:

```bash
# Basic installation
pip install ragversion

# With all parsers (PDF, DOCX, etc.)
pip install ragversion[parsers]

# With LangChain integration
pip install ragversion[langchain]

# With LlamaIndex integration
pip install ragversion[llamaindex]

# Everything
pip install ragversion[all]
```

## Setup

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Get your project URL and service key from Settings > API
3. Set environment variables:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

### 2. Run Database Migrations

Initialize the database schema:

```bash
ragversion init
ragversion migrate
```

This will show you the SQL to run in your Supabase SQL Editor.

### 3. Create Configuration File

Create a `ragversion.yaml` file:

```yaml
storage:
  backend: supabase
  supabase:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_SERVICE_KEY}

tracking:
  store_content: true
  max_file_size_mb: 50

  batch:
    max_workers: 4
    on_error: continue

  content:
    compression: gzip
    ttl_days: 365
```

## Basic Usage

### Track a Single File

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage

async def main():
    # Initialize
    storage = SupabaseStorage.from_env()
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # Track a file
    event = await tracker.track("document.pdf")

    if event:
        print(f"Change detected: {event.change_type}")
        print(f"Version: {event.version_number}")

    await tracker.close()

asyncio.run(main())
```

### Track a Directory (Batch Processing)

```python
async def main():
    storage = SupabaseStorage.from_env()
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # Track all PDFs and DOCX files
    result = await tracker.track_directory(
        "./documents",
        patterns=["*.pdf", "*.docx"],
        recursive=True,
    )

    print(f"Changes: {result.success_count}")
    print(f"Errors: {result.failure_count}")
    print(f"Success rate: {result.success_rate:.1f}%")

    await tracker.close()

asyncio.run(main())
```

### Handle Change Events

```python
async def main():
    storage = SupabaseStorage.from_env()
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # Register callback
    def on_change(event):
        print(f"File changed: {event.file_name}")
        print(f"Change type: {event.change_type}")

    tracker.on_change(on_change)

    # Track files - callback will be called for each change
    await tracker.track_directory("./documents")

    await tracker.close()

asyncio.run(main())
```

### Async Callbacks

```python
async def on_change_async(event):
    """Async callback example."""
    # Do async work
    await some_async_operation(event)

tracker.on_change(on_change_async)
```

## Using the CLI

### Initialize Project

```bash
ragversion init
```

### Track Files

```bash
# Track a single file
ragversion track document.pdf

# Track a directory
ragversion track ./documents

# Track with specific patterns
ragversion track ./documents -p "*.pdf" -p "*.docx"

# Track non-recursively
ragversion track ./documents --no-recursive
```

### List Documents

```bash
ragversion list
```

### View Version History

```bash
ragversion history <document-id>
```

### View Diff

```bash
ragversion diff <document-id> --from-version 1 --to-version 2
```

### Health Check

```bash
ragversion health
```

## Context Manager Usage

Use the context manager for automatic resource cleanup:

```python
async with AsyncVersionTracker(storage=storage) as tracker:
    event = await tracker.track("document.pdf")
    # tracker is automatically closed when exiting
```

## Error Handling

RAGVersion uses a resilient continue-on-error approach for batch operations:

```python
result = await tracker.track_directory("./documents")

# Check for failures
if result.failed:
    for error in result.failed:
        print(f"Failed: {error.file_path}")
        print(f"Error: {error.error}")
        print(f"Type: {error.error_type}")  # "parsing" | "storage" | "unknown"
```

## Next Steps

- [LangChain Integration](integrations/langchain.md)
- [LlamaIndex Integration](integrations/llamaindex.md)
- [API Reference](api-reference.md)
- [Examples](../examples/)

# Quick Start

Get started with RAGVersion in 5 minutes.

## Your First Document Tracking

Let's track a single document and detect changes.

### Step 1: Create a Tracker

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage

async def main():
    # Create tracker
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env()
    )

    # Initialize storage connection
    await tracker.initialize()

    # Your code here...

    # Clean up
    await tracker.close()

asyncio.run(main())
```

### Step 2: Track a Document

```python
# Track a single file
change = await tracker.track("./docs/readme.pdf")

if change:
    print(f"Change detected: {change.change_type}")
    print(f"Version: {change.version_number}")
    print(f"Hash: {change.content_hash}")
else:
    print("No changes detected")
```

### Step 3: Track Multiple Documents

```python
# Track all PDFs in a directory
result = await tracker.track_directory(
    "./docs",
    patterns=["*.pdf"],
    recursive=True
)

print(f"Total files: {result.total_files}")
print(f"Changes detected: {result.success_count}")
print(f"Failures: {result.failure_count}")
print(f"Duration: {result.duration_seconds:.2f}s")
```

## Complete Example

Here's a complete working example:

```python
import asyncio
from pathlib import Path
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage

async def sync_documents(directory: str):
    """Sync all documents in a directory."""

    # Initialize tracker
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env(),
        store_content=True,  # Store document content
        max_file_size_mb=50  # Skip files > 50MB
    )

    await tracker.initialize()

    try:
        # Track all documents
        result = await tracker.track_directory(
            directory,
            patterns=["*.pdf", "*.docx", "*.txt", "*.md"],
            recursive=True,
            max_workers=4
        )

        # Report results
        print(f"\n📊 Sync Results:")
        print(f"   Total files: {result.total_files}")
        print(f"   Changes detected: {result.success_count}")
        print(f"   Errors: {result.failure_count}")
        print(f"   Duration: {result.duration_seconds:.2f}s")

        # Show changes
        if result.successful:
            print(f"\n✨ Changes:")
            for event in result.successful:
                icon = "🆕" if event.change_type.value == "created" else "📝"
                print(f"   {icon} {event.file_name} (v{event.version_number})")

        return result

    finally:
        await tracker.close()

# Run the sync
if __name__ == "__main__":
    asyncio.run(sync_documents("./my_documents"))
```

## Using the CLI

RAGVersion also provides a command-line interface:

### Initialize Project

```bash
ragversion init
```

### Track Files

```bash
# Track single file
ragversion track document.pdf

# Track directory
ragversion track ./documents

# Track with patterns
ragversion track ./documents --patterns "*.pdf" --patterns "*.docx"
```

### List Documents

```bash
ragversion list
```

### View History

```bash
ragversion history <document-id>
```

### Compare Versions

```bash
ragversion diff <document-id> --from-version 1 --to-version 2
```

## Common Patterns

### Pattern 1: Track and Respond to Changes

```python
async def on_change(event):
    print(f"Document {event.file_name} was {event.change_type}")
    # Trigger re-indexing, send notification, etc.

tracker.on_change(on_change)
await tracker.track_directory("./docs")
```

### Pattern 2: Check What Changed

```python
result = await tracker.track_directory("./docs")

for event in result.successful:
    if event.change_type == "modified":
        print(f"Modified: {event.file_name}")
```

### Pattern 3: Get Version History

```python
# List all documents
documents = await tracker.list_documents()

# Get versions for a document
versions = await tracker.list_versions(documents[0].id)

for version in versions:
    print(f"v{version.version_number}: {version.change_type}")
```

### Pattern 4: Compare Versions

```python
# Get diff between versions
diff = await tracker.get_diff(
    document_id,
    from_version=1,
    to_version=2
)

print(f"Additions: {diff.additions}")
print(f"Deletions: {diff.deletions}")
print(f"Changes:\n{diff.diff_text}")
```

## Next Steps

- [Configuration](configuration.md) - Configure RAGVersion for your needs
- [Core Concepts](../guide/core-concepts.md) - Understand key concepts
- [Tracking Documents](../guide/tracking.md) - Advanced tracking techniques
- [LangChain Integration](../integrations/langchain.md) - Integrate with LangChain
- [LlamaIndex Integration](../integrations/llamaindex.md) - Integrate with LlamaIndex

## Need Help?

- Check the [Troubleshooting Guide](../advanced/troubleshooting.md)
- Browse [Examples](../examples/basic.md)
- Ask questions in [GitHub Discussions](https://github.com/sourangshupal/ragversion/discussions)

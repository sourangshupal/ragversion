# 5-Minute RAGVersion Tutorial

Get started with RAGVersion in 5 minutes or less.

## What You'll Learn

By the end of this tutorial, you'll know how to:
1. Install RAGVersion
2. Track your first file
3. Track a directory
4. View version history
5. Handle file changes

**Time**: 5 minutes
**Prerequisites**: Python 3.9+

---

## Step 1: Install (30 seconds)

```bash
pip install ragversion
```

That's it! RAGVersion uses SQLite by default (no setup required).

---

## Step 2: Track Your First File (1 minute)

Create a file called `first_track.py`:

```python
import asyncio
from ragversion import AsyncVersionTracker


async def main():
    # Create tracker (zero configuration!)
    async with await AsyncVersionTracker.create() as tracker:

        # Track a file
        result = await tracker.track("README.md")

        if result.changed:
            print(f"✓ Tracked! Version {result.version_number}")
        else:
            print("No changes since last track")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python first_track.py
```

Output:
```
✓ Tracked! Version 1
```

**What happened?**
- RAGVersion created a database (`ragversion.db`)
- Tracked README.md as version 1
- Stored the content and metadata

---

## Step 3: Make a Change and Track Again (1 minute)

Edit README.md (add a line, change text, anything).

Run the script again:
```bash
python first_track.py
```

Output:
```
✓ Tracked! Version 2
```

**What happened?**
- RAGVersion detected the file changed
- Created version 2 with the new content
- You can now access version history

---

## Step 4: View Version History (1 minute)

Add this to your script:

```python
async def main():
    async with await AsyncVersionTracker.create() as tracker:
        result = await tracker.track("README.md")

        # NEW: Get document info
        doc = await tracker.storage.get_document_by_path(
            str(Path("README.md").absolute())
        )

        if doc:
            print(f"\nVersion history for README.md:")
            print(f"  Total versions: {doc.version_count}")
            print(f"  Current version: {doc.current_version}")
            print(f"  Last updated: {doc.updated_at}")

            # Get all versions
            versions = await tracker.storage.list_versions(doc.id)
            for version in versions:
                print(f"  v{version.version_number}: {version.change_type.value} "
                      f"at {version.created_at}")
```

Add the import at the top:
```python
from pathlib import Path
```

Run it:
```bash
python first_track.py
```

Output:
```
Version history for README.md:
  Total versions: 2
  Current version: 2
  Last updated: 2024-01-20 10:35:00
  v1: created at 2024-01-20 10:30:00
  v2: modified at 2024-01-20 10:35:00
```

---

## Step 5: Track a Directory (1 minute)

Track multiple files at once:

```python
async def main():
    async with await AsyncVersionTracker.create() as tracker:

        # Track entire directory
        result = await tracker.track_directory("./docs")

        print(f"✓ Tracked {result.success_count} files")

        if result.failure_count > 0:
            print(f"⚠ Failed: {result.failure_count} files")
```

Run it:
```bash
python first_track.py
```

Output:
```
✓ Tracked 15 files
```

---

## Step 6: Track Specific File Types (30 seconds)

Only track certain files:

```python
# Track only PDFs
result = await tracker.track_directory("./docs", patterns=["*.pdf"])

# Track markdown and text files
result = await tracker.track_directory(
    "./docs",
    patterns=["*.md", "*.txt"]
)

# Track recursively in subdirectories
result = await tracker.track_directory(
    "./docs",
    patterns=["**/*.pdf"],  # ** for recursive
    recursive=True
)
```

---

## 🎉 You're Done!

In 5 minutes, you've learned:
- ✅ How to install RAGVersion
- ✅ How to track files with zero configuration
- ✅ How to view version history
- ✅ How to track directories
- ✅ How to filter by file type

## Next Steps

**Level Up:**
- [Integrate with LangChain](../README.md#framework-integration-langchainllamaindex)
- [Integrate with LlamaIndex](../README.md#framework-integration-langchainllamaindex)
- [Watch files for real-time changes](../examples/file_watching.py)
- [Use the REST API](../README.md#web-server--rest-api)

**Go Deeper:**
- [Complete Documentation](DOCUMENTATION.md)
- [API Reference](API.md)
- [All Examples](../examples/)
- [How-to Guide](../How_to.md)

**Need Help?**
- [GitHub Issues](https://github.com/sourangshupal/ragversion/issues)
- [Examples Directory](../examples/)

---

## Common Next Questions

### How do I use Supabase instead of SQLite?

```python
# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"

# Use in code
tracker = await AsyncVersionTracker.create("supabase")
```

### How do I get differences between versions?

```python
# Get diff between versions
diff_result = await tracker.get_diff(document_id, from_version=1, to_version=2)

print(f"Additions: {diff_result.additions}")
print(f"Deletions: {diff_result.deletions}")
print(diff_result.diff_text)
```

### How do I restore a previous version?

```python
# Restore to version 1
event = await tracker.restore_version(document_id, version_number=1)
print(f"Restored to version {event.version_number}")
```

### How do I use callbacks for change notifications?

```python
def on_change(event):
    print(f"File changed: {event.file_name}")
    print(f"Change type: {event.change_type}")

async with await AsyncVersionTracker.create() as tracker:
    tracker.on_change(on_change)

    # Now all changes trigger the callback
    result = await tracker.track_directory("./docs")
```

### How do I integrate with my RAG application?

See the [LangChain Quick Start](../examples/quick_start_langchain.py) or [LlamaIndex Quick Start](../examples/quick_start_llamaindex.py) - both are just 3 lines of code!

```python
from ragversion.integrations.langchain import quick_start

# That's it!
sync = await quick_start("./documents")
```

# Troubleshooting Guide

Common issues and solutions for RAGVersion.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
- [Performance Issues](#performance-issues)
- [Integration Issues](#integration-issues)
- [Database Issues](#database-issues)
- [File Tracking Issues](#file-tracking-issues)

---

## Installation Issues

### "No module named ragversion"

**Error:**
```
ModuleNotFoundError: No module named 'ragversion'
```

**Cause:** Package not installed

**Solutions:**
```bash
# Install basic package
pip install ragversion

# Or with all features
pip install ragversion[all]

# Verify installation
python -c "import ragversion; print(ragversion.__version__)"
```

---

### "Failed to install pypdf"

**Error:**
```
ERROR: Failed building wheel for pypdf
```

**Cause:** Missing optional dependencies or system libraries

**Solutions:**

**Option 1: Install all parsers**
```bash
pip install ragversion[parsers]
```

**Option 2: Install specific parser**
```bash
# For PDF only
pip install pypdf

# For DOCX only
pip install python-docx

# For Excel only
pip install openpyxl
```

**Option 3: Use without parsers** (text files only)
```bash
pip install ragversion  # Basic installation
```

---

### "Microsoft Visual C++ required" (Windows)

**Error:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Cause:** Missing C++ build tools on Windows

**Solutions:**

1. Install Microsoft C++ Build Tools:
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++" workload

2. Or use pre-built wheels:
   ```bash
   pip install --only-binary :all: ragversion[parsers]
   ```

---

## Runtime Errors

### "Tracker not initialized"

**Error:**
```
RAGVersionError: Tracker not initialized. Call initialize() first.
```

**Cause:** Forgot to initialize tracker

**Solutions:**

**Option 1: Use factory method (recommended)**
```python
# This auto-initializes
tracker = await AsyncVersionTracker.create()
```

**Option 2: Use context manager**
```python
async with await AsyncVersionTracker.create() as tracker:
    result = await tracker.track("file.pdf")
```

**Option 3: Call initialize() manually**
```python
tracker = AsyncVersionTracker(storage=storage)
await tracker.initialize()  # Don't forget this!
```

---

### "File not found"

**Error:**
```
FileNotFoundError: File not found: document.pdf

Troubleshooting:
  • Check file path is correct
  • Use absolute path: /full/path/to/document.pdf
```

**Cause:** File doesn't exist or incorrect path

**Solutions:**

1. Check file exists:
   ```python
   from pathlib import Path
   file = Path("document.pdf")
   print(f"Exists: {file.exists()}")
   print(f"Absolute: {file.absolute()}")
   ```

2. Use absolute paths:
   ```python
   import os
   file_path = os.path.abspath("document.pdf")
   result = await tracker.track(file_path)
   ```

3. Check working directory:
   ```python
   import os
   print(f"Working directory: {os.getcwd()}")
   ```

---

### "Storage connection failed"

**Error (SQLite):**
```
StorageError: Storage error: unable to open database file

Troubleshooting:
  • Check file path and permissions
```

**Solutions:**

1. Check permissions:
   ```bash
   ls -la ragversion.db
   chmod 644 ragversion.db
   ```

2. Check directory exists:
   ```bash
   mkdir -p ./data
   ```

3. Use absolute path:
   ```python
   tracker = await AsyncVersionTracker.create(
       db_path="/full/path/to/ragversion.db"
   )
   ```

**Error (Supabase):**
```
StorageError: Storage error: connection refused

Troubleshooting:
  • Check database connection and credentials
  • Verify SUPABASE_URL and SUPABASE_SERVICE_KEY
```

**Solutions:**

1. Verify environment variables:
   ```python
   import os
   print(f"URL: {os.getenv('SUPABASE_URL')}")
   print(f"Key: {'set' if os.getenv('SUPABASE_SERVICE_KEY') else 'NOT SET'}")
   ```

2. Test connection manually:
   ```python
   from supabase import create_client

   url = os.getenv("SUPABASE_URL")
   key = os.getenv("SUPABASE_SERVICE_KEY")
   client = create_client(url, key)

   # Test query
   result = client.table("documents").select("*").limit(1).execute()
   print(f"Connection works: {bool(result.data)}")
   ```

3. Check network:
   ```bash
   ping your-project.supabase.co
   curl https://your-project.supabase.co
   ```

---

### "Table not found" (Supabase)

**Error:**
```
StorageError: Storage error: relation "documents" does not exist

Troubleshooting:
  • Run database migrations
  • Verify tables exist: documents, versions, version_content
```

**Cause:** Migrations not run

**Solutions:**

1. Run migrations:
   ```bash
   ragversion migrate
   ```

2. Manually run SQL in Supabase console:
   - Go to: https://supabase.com/dashboard/project/_/sql
   - Copy SQL from: `ragversion/storage/migrations/001_initial_schema.sql`
   - Run the script

3. Verify tables exist:
   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public';
   ```

---

## Performance Issues

### "track_directory() is very slow"

**Symptoms:**
- Taking minutes to process hundreds of files
- High CPU/memory usage
- Slow embedding API calls

**Causes & Solutions:**

**1. Too many files**
```python
# Solution: Use file patterns to limit scope
result = await tracker.track_directory(
    "docs",
    patterns=["*.md", "*.txt"]  # Only track specific types
)
```

**2. Low concurrency**
```python
# Solution: Increase max_workers
result = await tracker.track_directory(
    "docs",
    max_workers=8  # Default is 4, increase for more parallelism
)
```

**3. Large files**
```python
# Solution: Increase file size limit or filter
tracker = await AsyncVersionTracker.create(
    max_file_size_mb=100  # Increase from default 50MB
)

# Or skip large files
result = await tracker.track_directory(
    "docs",
    patterns=["*.md"]  # Exclude large PDFs/videos
)
```

**4. Network latency (Supabase)**
```python
# Solution: Use SQLite for development
tracker = await AsyncVersionTracker.create("sqlite")  # Faster locally
```

**5. Embeddings API rate limits**
```python
# Solution: Add delays between API calls (for integrations)
from ragversion.integrations.langchain import quick_start

sync = await quick_start(
    "docs",
    max_workers=2  # Reduce concurrency to avoid rate limits
)
```

---

### "High memory usage"

**Symptoms:**
- Python process using 1GB+ memory
- Out of memory errors on large directories

**Causes & Solutions:**

**1. Storing content in memory**
```python
# Solution: Disable content storage
tracker = await AsyncVersionTracker.create(
    store_content=False  # Only track hashes
)
```

**2. Large files**
```python
# Solution: Reduce max file size
tracker = await AsyncVersionTracker.create(
    max_file_size_mb=10  # Limit to 10MB files
)
```

**3. Too many files processed at once**
```python
# Solution: Reduce concurrency
result = await tracker.track_directory(
    "docs",
    max_workers=2  # Lower concurrency = less memory
)
```

---

## Integration Issues

### "LangChain integration not working"

**Error:**
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
```bash
pip install ragversion[langchain]
```

---

### "Embeddings API rate limit"

**Error:**
```
openai.error.RateLimitError: Rate limit exceeded
```

**Solutions:**

**1. Add delays**
```python
import asyncio

async def track_with_delays():
    async with await AsyncVersionTracker.create() as tracker:
        files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

        for file in files:
            result = await tracker.track(file)
            await asyncio.sleep(1)  # Wait 1 second between files
```

**2. Reduce concurrency**
```python
result = await tracker.track_directory(
    "docs",
    max_workers=1  # Process one file at a time
)
```

**3. Use chunk tracking** (80-95% fewer embeddings)
```python
sync = await quick_start(
    "docs",
    enable_chunk_tracking=True  # Default, but make sure it's enabled
)
```

---

### "Vector store out of sync"

**Symptoms:**
- Query returns outdated results
- Deleted documents still appear

**Solutions:**

**1. Resync from scratch**
```python
# Clear and rebuild
sync.vectorstore.delete(delete_all=True)
await sync.sync_directory("./docs")
```

**2. Check callbacks are registered**
```python
# Ensure auto-sync is enabled
def verify_callbacks():
    print(f"Callbacks registered: {len(tracker._callbacks)}")

    if not tracker._callbacks:
        print("WARNING: No callbacks registered!")
        tracker.on_change(sync.on_change)
```

---

## Database Issues

### "SQLite database locked"

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes accessing same database

**Solutions:**

1. **Use Supabase for multi-process scenarios:**
   ```python
   tracker = await AsyncVersionTracker.create("supabase")
   ```

2. **Ensure only one process at a time:**
   ```python
   # Use file-based locking
   import filelock

   lock = filelock.FileLock("ragversion.lock")
   with lock:
       async with await AsyncVersionTracker.create() as tracker:
           result = await tracker.track_directory("docs")
   ```

3. **Increase timeout:**
   ```python
   from ragversion.storage import SQLiteStorage

   storage = SQLiteStorage(timeout=60)  # Default is 30s
   tracker = AsyncVersionTracker(storage=storage)
   ```

---

### "Supabase quota exceeded"

**Error:**
```
StorageError: Database quota exceeded
```

**Solutions:**

1. Check your plan limits in Supabase dashboard

2. Clean up old versions:
   ```python
   # Keep only last 10 versions per document
   for doc in await tracker.list_documents():
       deleted = await tracker.cleanup_old_versions(doc.id, keep_count=10)
       print(f"Deleted {deleted} old versions for {doc.file_name}")
   ```

3. Disable content storage:
   ```python
   tracker = await AsyncVersionTracker.create(
       store_content=False  # Only store hashes
   )
   ```

---

## File Tracking Issues

### "No changes detected" when file changed

**Symptoms:**
- File changed but `track()` returns `changed=False`
- Expected MODIFIED but got nothing

**Causes & Solutions:**

**1. Content hasn't changed** (only metadata/timestamp)
```python
# RAGVersion tracks content, not timestamps
# If only the file modified time changed, no new version is created
```

**2. File is being parsed differently**
```python
# Check what content is being parsed
result = await tracker.track("file.pdf")

if not result.changed:
    # Get current content hash
    doc = await tracker.storage.get_document_by_path(str(Path("file.pdf").absolute()))
    print(f"Current hash: {doc.content_hash}")

    # Compare with parsed content
    from ragversion.parsers import ParserRegistry
    parser = ParserRegistry.get_parser("file.pdf")
    content = await parser.parse("file.pdf")
    import hashlib
    new_hash = hashlib.sha256(content.encode()).hexdigest()
    print(f"New hash: {new_hash}")
    print(f"Match: {doc.content_hash == new_hash}")
```

---

### "Changes detected too frequently"

**Symptoms:**
- New version created on every run
- FileWatcher creates duplicate events

**Causes & Solutions:**

**1. Debouncing not working (FileWatcher)**
```python
# FileWatcher has built-in 1-second debounce
# If still seeing duplicates, increase it:

from ragversion.watcher import DocumentEventHandler

handler = DocumentEventHandler()
handler._debounce_seconds = 2.0  # Increase to 2 seconds
```

**2. Temp files being tracked**
```python
# Solution: Add to ignore patterns
watcher = FileWatcher(
    tracker,
    paths=["./docs"],
    ignore_patterns=[
        "*.tmp",
        "*.swp",
        "*~",
        ".git/*",
        "__pycache__/*"
    ]
)
```

---

## Getting More Help

Still stuck? Here's how to get help:

1. **Check examples**: [examples/](../examples/)
2. **Read the tutorial**: [5-Minute Tutorial](5-MINUTE-TUTORIAL.md)
3. **Search issues**: [GitHub Issues](https://github.com/sourangshupal/ragversion/issues)
4. **Ask a question**: [GitHub Discussions](https://github.com/sourangshupal/ragversion/discussions)
5. **Report a bug**: [New Issue](https://github.com/sourangshupal/ragversion/issues/new)

When reporting issues, please include:
- RAGVersion version: `python -c "import ragversion; print(ragversion.__version__)"`
- Python version: `python --version`
- Operating system
- Full error traceback
- Minimal code to reproduce

# SQLite Storage Backend

RAGVersion's SQLite backend provides zero-configuration local storage for your document tracking needs. It's perfect for development, testing, and small to medium-scale deployments.

## Overview

The SQLite backend offers:
- ✅ **Zero configuration** - Works out of the box, no setup required
- ✅ **Local storage** - All data stored in a single file
- ✅ **Fast performance** - Optimized for local operations
- ✅ **Portable** - Easy to backup, copy, or version control
- ✅ **No dependencies** - No external services or accounts needed

## When to Use SQLite

### ✅ Great For:
- **Development & testing** - Quick setup, easy debugging
- **Small to medium projects** - Up to 10,000+ documents
- **Single-machine deployments** - Desktop apps, scripts, local pipelines
- **CI/CD pipelines** - Isolated test environments
- **Offline usage** - No internet connection required
- **Personal projects** - No cloud account needed

### ⚠️ Consider Supabase Instead For:
- **Team collaboration** - Multiple users accessing same database
- **Large-scale deployments** - 100,000+ documents
- **Multi-machine setups** - Distributed systems
- **Cloud-native applications** - Already using cloud infrastructure

## Quick Start

### Installation

```bash
pip install ragversion
```

SQLite support is included in the base package via `aiosqlite`.

### Basic Usage

#### CLI (Simplest)

```bash
# Start tracking - that's it!
ragversion track ./documents

# Database created automatically at ./ragversion.db
```

#### Python API

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage

async def main():
    # Default: creates ragversion.db in current directory
    storage = SQLiteStorage()

    async with AsyncVersionTracker(storage=storage) as tracker:
        # Track files
        result = await tracker.track_directory("./documents")
        print(f"Tracked {len(result.successful)} files")

asyncio.run(main())
```

## Configuration

### Default Configuration

No configuration needed! SQLite uses sensible defaults:

```python
SQLiteStorage(
    db_path="ragversion.db",      # Database file location
    content_compression=True,      # Compress stored content
    timeout=30                     # Database timeout (seconds)
)
```

### Custom Configuration

#### Via Configuration File

Create `ragversion.yaml`:

```yaml
storage:
  backend: sqlite
  sqlite:
    db_path: ./data/my_database.db
    content_compression: true
    timeout_seconds: 30
```

#### Via Python

```python
storage = SQLiteStorage(
    db_path="./my_custom_location/ragversion.db",
    content_compression=True,
    timeout=60
)
```

#### Via Environment Variables

```bash
export RAGVERSION_STORAGE_BACKEND=sqlite
export SQLITE_DB_PATH=./data/ragversion.db
export SQLITE_CONTENT_COMPRESSION=true
export SQLITE_TIMEOUT_SECONDS=30
```

## Database Location

### Default Location

By default, the database is created at `./ragversion.db` (current working directory).

### Custom Locations

```python
# Absolute path
storage = SQLiteStorage(db_path="/var/data/ragversion.db")

# Relative path
storage = SQLiteStorage(db_path="./data/ragversion.db")

# User home directory
from pathlib import Path
storage = SQLiteStorage(db_path=str(Path.home() / "ragversion.db"))

# In-memory database (testing only - data lost on close)
storage = SQLiteStorage(db_path=":memory:")
```

### Best Practices

1. **Development**: Use default `./ragversion.db` in project root
2. **Production**: Use absolute path in dedicated data directory
3. **Testing**: Use in-memory database (`:memory:`)
4. **CI/CD**: Use temp directory or in-memory

```python
import os
import tempfile

# Production
if os.getenv("ENV") == "production":
    db_path = "/var/lib/ragversion/ragversion.db"
# Testing
elif os.getenv("ENV") == "test":
    db_path = ":memory:"
# Development
else:
    db_path = "./ragversion.db"

storage = SQLiteStorage(db_path=db_path)
```

## Features

### Automatic Schema Management

SQLite backend automatically creates all required tables on initialization:

```python
async with AsyncVersionTracker(storage=storage) as tracker:
    # Tables created automatically on first use
    await tracker.track("document.pdf")
```

No manual migrations needed!

### Content Compression

By default, document content is compressed with gzip to save space:

```python
# Enabled by default (recommended)
storage = SQLiteStorage(content_compression=True)

# Disable for faster access (larger database)
storage = SQLiteStorage(content_compression=False)
```

**Compression savings:** Typically 60-80% for text documents.

### WAL Mode (Write-Ahead Logging)

SQLite backend uses WAL mode for better concurrency:
- Multiple readers can access database simultaneously
- Writers don't block readers
- Better performance for concurrent operations

This is configured automatically - no action needed.

### Indexes

All tables have optimized indexes for fast queries:
- Document lookups by file path
- Version history by document ID
- Content retrieval by version ID
- Statistics queries

## Performance

### Benchmarks

Typical performance on modern hardware:

| Operation | Documents | Time | Rate |
|-----------|-----------|------|------|
| Track documents | 1,000 | ~5s | 200/sec |
| List documents | 10,000 | ~50ms | - |
| Get version history | 100 versions | ~10ms | - |
| Compute diff | 2 versions | ~20ms | - |

### Optimization Tips

#### 1. Batch Processing

```python
# Good: Batch track directory
result = await tracker.track_directory("./docs", workers=4)

# Avoid: Individual file tracking in loop
for file in files:
    await tracker.track(file)  # Slower
```

#### 2. Connection Pooling

Reuse tracker instance instead of creating new ones:

```python
# Good: Reuse tracker
async with AsyncVersionTracker(storage=storage) as tracker:
    for batch in file_batches:
        await tracker.track_directory(batch)

# Avoid: New tracker per batch
for batch in file_batches:
    async with AsyncVersionTracker(storage=storage) as tracker:
        await tracker.track_directory(batch)  # Reconnects each time
```

#### 3. Disable Content Storage (if not needed)

```python
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=False  # Only store hashes, not content
)
```

#### 4. Increase Workers

```python
# For large batches
result = await tracker.track_directory(
    "./docs",
    max_workers=8  # Default: 4
)
```

## Backup & Migration

### Backup Database

SQLite databases are single files - easy to backup:

```bash
# Simple copy
cp ragversion.db ragversion.db.backup

# With timestamp
cp ragversion.db "ragversion.db.$(date +%Y%m%d_%H%M%S)"

# Automated backup (cron)
0 2 * * * cp /path/to/ragversion.db /backups/ragversion.db.$(date +\%Y\%m\%d)
```

### Restore Database

```bash
cp ragversion.db.backup ragversion.db
```

### Export to JSON

```bash
# Export all statistics
ragversion stats --format json > stats.json

# Can be imported later or analyzed
```

### Migrate to Supabase

When you outgrow SQLite, migrate to Supabase:

```python
import asyncio
from ragversion.storage import SQLiteStorage, SupabaseStorage

async def migrate():
    # Source: SQLite
    sqlite = SQLiteStorage(db_path="ragversion.db")
    await sqlite.initialize()

    # Destination: Supabase
    supabase = SupabaseStorage.from_env()
    await supabase.initialize()

    # Get all documents
    docs = await sqlite.list_documents(limit=10000)

    for doc in docs:
        # Copy document
        await supabase.create_document(doc)

        # Copy versions
        versions = await sqlite.list_versions(doc.id, limit=1000)
        for version in versions:
            # Get content
            content = await sqlite.get_content(version.id)
            if content:
                version.content = content

            # Create in Supabase
            await supabase.create_version(version)

    await sqlite.close()
    await supabase.close()
    print("Migration complete!")

asyncio.run(migrate())
```

## Troubleshooting

### Database Locked Error

**Cause:** Multiple processes trying to write simultaneously.

**Solution:**
1. Increase timeout:
   ```python
   storage = SQLiteStorage(timeout=60)  # Default: 30
   ```

2. Use single writer process for concurrent operations
3. Consider WAL mode (already enabled by default)

### Database File Not Found

**Cause:** Relative path issues or missing parent directory.

**Solution:**
```python
from pathlib import Path

# Ensure parent directory exists
db_path = Path("./data/ragversion.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

storage = SQLiteStorage(db_path=str(db_path))
```

### Database Too Large

**Symptoms:** Slow queries, large file size.

**Solutions:**

1. **Enable compression** (if disabled):
   ```python
   storage = SQLiteStorage(content_compression=True)
   ```

2. **Disable content storage**:
   ```python
   tracker = AsyncVersionTracker(
       storage=storage,
       store_content=False
   )
   ```

3. **Clean old versions**:
   ```python
   # Keep only last 10 versions per document
   await storage.cleanup_old_versions(document_id, keep_count=10)

   # Delete versions older than 90 days
   await storage.cleanup_by_age(days=90)
   ```

4. **Vacuum database** (reclaim space):
   ```bash
   sqlite3 ragversion.db "VACUUM;"
   ```

5. **Migrate to Supabase** for large-scale needs

### Permission Denied

**Cause:** Insufficient permissions to create/write database file.

**Solution:**
```bash
# Ensure write permissions
chmod 644 ragversion.db
chmod 755 $(dirname ragversion.db)

# Or use location with write access
```

```python
# Use user home directory
from pathlib import Path
storage = SQLiteStorage(db_path=str(Path.home() / ".ragversion" / "ragversion.db"))
```

## Security

### File Permissions

Secure your database file:

```bash
# Recommended: User read/write only
chmod 600 ragversion.db

# Ensure directory is also secured
chmod 700 $(dirname ragversion.db)
```

### Encryption

SQLite doesn't have built-in encryption. For sensitive data:

1. **Use filesystem encryption** (recommended):
   - macOS: FileVault
   - Linux: LUKS, ecryptfs
   - Windows: BitLocker

2. **Use SQLCipher extension** (advanced):
   ```bash
   pip install sqlcipher3
   ```
   Note: Requires code modifications.

3. **Migrate to Supabase** with RLS (Row Level Security)

### Access Control

SQLite is file-based - use OS-level permissions:

```bash
# Create dedicated group
sudo groupadd ragversion
sudo chgrp ragversion ragversion.db
sudo chmod 660 ragversion.db

# Add users to group
sudo usermod -a -G ragversion username
```

## Advanced Topics

### Custom Connection Settings

```python
import aiosqlite

# Access underlying aiosqlite connection
storage = SQLiteStorage()
await storage.initialize()

# Connection is at storage.db
# Already configured with:
# - PRAGMA foreign_keys = ON
# - PRAGMA journal_mode = WAL
```

### Programmatic Schema Access

```python
# Get table schema
async with storage.db.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='documents'"
) as cursor:
    schema = await cursor.fetchone()
    print(schema[0])

# List all tables
async with storage.db.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
) as cursor:
    tables = await cursor.fetchall()
    print(tables)
```

### Direct SQL Queries

```python
# Execute custom queries (advanced users only)
async with storage.db.execute(
    "SELECT COUNT(*) FROM documents WHERE file_type = ?",
    ("application/pdf",)
) as cursor:
    count = await cursor.fetchone()
    print(f"PDF documents: {count[0]}")
```

**Warning:** Direct SQL can break abstractions. Use storage methods when possible.

## Comparison: SQLite vs Supabase

| Feature | SQLite | Supabase |
|---------|--------|----------|
| **Setup Time** | 0 seconds | 5-10 minutes |
| **Configuration** | None | API keys, migrations |
| **Cost** | Free | Free tier + paid |
| **Scalability** | 10K-100K docs | Unlimited |
| **Multi-user** | Read-only | Full concurrent |
| **Backup** | File copy | Automated |
| **Hosting** | Local file | Cloud |
| **Latency** | <1ms (local) | 50-200ms (network) |
| **Best For** | Dev, small projects | Production, teams |

## Examples

### Complete CLI Workflow

```bash
# Initialize project
pip install ragversion[all]

# Track documents (creates ragversion.db automatically)
ragversion track ./documents

# View tracked documents
ragversion list

# Get statistics
ragversion stats

# View version history for a document
ragversion history <document-id>

# Compare versions
ragversion diff <document-id> --from-version 1 --to-version 2
```

### Complete Python Workflow

```python
import asyncio
from pathlib import Path
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage

async def complete_workflow():
    # Setup
    storage = SQLiteStorage(db_path="./data/ragversion.db")
    Path("./data").mkdir(exist_ok=True)

    async with AsyncVersionTracker(storage=storage) as tracker:
        # Track directory
        print("Tracking documents...")
        result = await tracker.track_directory(
            "./documents",
            patterns=["*.pdf", "*.docx"],
            recursive=True,
            max_workers=4
        )
        print(f"✅ Tracked: {len(result.successful)} files")
        print(f"❌ Failed: {len(result.failed)} files")

        # List documents
        print("\nDocuments:")
        docs = await tracker.list_documents(limit=10)
        for doc in docs:
            print(f"  - {doc.file_name} (v{doc.current_version})")

        # Get statistics
        print("\nStatistics:")
        stats = await tracker.get_statistics()
        print(f"  Total documents: {stats.total_documents}")
        print(f"  Total versions: {stats.total_versions}")
        print(f"  Storage used: {stats.total_storage_bytes / 1024 / 1024:.2f} MB")

        # Track changes (run again to detect modifications)
        print("\nChecking for changes...")
        result = await tracker.track_directory("./documents")

        if result.successful:
            for event in result.successful:
                print(f"  {event.change_type.value}: {event.file_name}")
        else:
            print("  No changes detected")

asyncio.run(complete_workflow())
```

### Testing Example

```python
import pytest
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage

@pytest.fixture
async def tracker():
    # Use in-memory database for tests
    storage = SQLiteStorage(db_path=":memory:")
    async with AsyncVersionTracker(storage=storage) as t:
        yield t

@pytest.mark.asyncio
async def test_track_document(tracker, tmp_path):
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")

    # Track it
    change = await tracker.track(str(test_file))

    # Verify
    assert change is not None
    assert change.change_type.value == "created"
    assert change.file_name == "test.txt"
```

## Conclusion

SQLite backend is the recommended starting point for RAGVersion:
- ✅ Zero configuration
- ✅ Fast local performance
- ✅ Easy to backup and migrate
- ✅ Perfect for development and small projects

When you need multi-user access or cloud deployment, migrate to Supabase seamlessly.

**Next Steps:**
- [Read the full documentation](../DOCUMENTATION.md)
- [Explore integrations](../README.md#integrations)
- [View the roadmap](../future-enhancements.md)

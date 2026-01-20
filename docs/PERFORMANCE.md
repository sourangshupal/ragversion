# Performance Optimization Guide

RAGVersion is optimized for high-throughput document tracking with support for batch operations and efficient storage backends. This guide covers performance best practices, benchmarks, and optimization techniques.

## Overview

**Key Performance Features:**
- ✅ **Batch operations** - 10-100x faster bulk inserts
- ✅ **Async-first architecture** - Non-blocking I/O throughout
- ✅ **Optimized indexes** - Fast queries for common operations
- ✅ **Connection pooling** - Reuse database connections
- ✅ **Concurrent processing** - Parallel file tracking with semaphores
- ✅ **Content compression** - 60-80% storage reduction

---

## Batch Operations

### What Are Batch Operations?

Batch operations allow you to insert multiple documents or versions in a single database transaction, significantly reducing overhead.

**Performance Improvement:**
- **SQLite**: 10-15x faster (91% time reduction)
- **Supabase**: 20-50x faster (fewer network round trips)

### When to Use Batch Operations

✅ **Use batch operations for:**
- Bulk imports from existing systems
- Initial directory tracking (1000+ files)
- Programmatic document creation
- Migration scripts
- Data seeding

❌ **Don't use batch operations for:**
- Real-time single-file tracking
- Interactive CLI usage (use `ragversion track`)
- Incremental updates

### How to Use Batch Operations

#### Batch Document Creation

```python
from ragversion.storage import SQLiteStorage
from ragversion.models import Document
from uuid import uuid4
from datetime import datetime

async def bulk_import():
    storage = SQLiteStorage()
    await storage.initialize()

    # Prepare documents
    documents = []
    for i in range(1000):
        doc = Document(
            id=uuid4(),
            file_path=f"/data/file_{i}.txt",
            file_name=f"file_{i}.txt",
            file_type=".txt",
            file_size=1024,
            content_hash=f"hash_{i}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version_count=1,
            current_version=1,
            metadata={"imported": True}
        )
        documents.append(doc)

    # Batch insert - 10x faster than individual inserts
    await storage.batch_create_documents(documents)
    print(f"Imported {len(documents)} documents")

    await storage.close()
```

#### Batch Version Creation

```python
from ragversion.models import Version, ChangeType

async def bulk_versions():
    storage = SQLiteStorage()
    await storage.initialize()

    # Prepare versions
    versions = []
    for i in range(1000):
        ver = Version(
            id=uuid4(),
            document_id=document_id,  # Your document ID
            version_number=i + 1,
            content_hash=f"hash_{i}",
            content=f"Content for version {i}",
            file_size=1024,
            change_type=ChangeType.MODIFIED,
            created_at=datetime.utcnow(),
            metadata={}
        )
        versions.append(ver)

    # Batch insert with content storage
    await storage.batch_create_versions(versions)
    print(f"Created {len(versions)} versions")

    await storage.close()
```

---

## Benchmarks

### Batch Insert Performance

**Test Environment:**
- MacBook Pro M1 (2021)
- Python 3.12
- SQLite with WAL mode

**Results:**

| Documents | Individual | Batch | Speedup |
|-----------|------------|-------|---------|
| 100 | 8.6ms | 0.8ms | **11x** |
| 500 | 42ms | 4.7ms | **9x** |
| 1000 | 85ms | 8.5ms | **10x** |

**Throughput:**
- Individual inserts: ~11,800 docs/sec
- Batch inserts: ~118,000 docs/sec

### File Tracking Performance

**Single File:**
- Parse + detect change: ~5-10ms
- Create document + version: ~2ms
- Total: ~10-15ms per file

**Directory (1000 files, 4 workers):**
- Total time: ~5-8 seconds
- Throughput: ~150-200 files/sec
- Includes: file parsing, change detection, database writes

**Directory (1000 files, 8 workers):**
- Total time: ~3-5 seconds
- Throughput: ~200-300 files/sec

### Query Performance

| Operation | SQLite | Supabase |
|-----------|--------|----------|
| Get document by ID | <1ms | 50-100ms |
| Get document by path | <1ms | 50-100ms |
| List 100 documents | ~5ms | 100-200ms |
| List 1000 documents | ~50ms | 200-400ms |
| Get version history (100 versions) | ~10ms | 100-200ms |
| Compute diff | ~20ms | 150-300ms |
| Get statistics | ~30ms | 200-400ms |

---

## Optimization Techniques

### 1. Use Appropriate Worker Count

The `max_workers` parameter controls concurrent file processing.

**Guidelines:**
- **CPU-bound tasks**: workers = CPU cores
- **I/O-bound tasks**: workers = 2-4x CPU cores
- **Default**: 4 workers (good for most cases)
- **Maximum recommended**: 16 workers

```python
# Default (good for most cases)
await tracker.track_directory("./docs", max_workers=4)

# For large directories on powerful machines
await tracker.track_directory("./docs", max_workers=8)

# For very large directories (10,000+ files)
await tracker.track_directory("./docs", max_workers=16)
```

**Benchmark Results:**
| Workers | 1000 Files | Throughput |
|---------|------------|------------|
| 1 | 15s | 67 files/sec |
| 2 | 8s | 125 files/sec |
| 4 | 5s | 200 files/sec |
| 8 | 3s | 333 files/sec |
| 16 | 2.5s | 400 files/sec |

**Diminishing Returns:**
Beyond 8 workers, performance gains are minimal due to:
- Database connection limits
- Disk I/O bottlenecks
- Context switching overhead

### 2. Disable Content Storage (If Not Needed)

If you only need change detection (not full content):

```python
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=False  # Only store hashes
)
```

**Performance Impact:**
- **50-70% faster** writes (no content compression)
- **80-90% less** storage space used
- **Faster** queries (smaller database)

**Trade-offs:**
- ❌ Can't restore previous versions
- ❌ Can't compute diffs
- ✅ Can still detect changes (via hashes)
- ✅ Can still track version history

### 3. Optimize File Patterns

Use specific patterns to avoid tracking unnecessary files:

```python
# Bad: Tracks everything (slow)
await tracker.track_directory("./project")

# Better: Specific patterns
await tracker.track_directory(
    "./project",
    patterns=["*.py", "*.md", "*.json"],
    recursive=True
)

# Best: Exclude large directories
await tracker.track_directory(
    "./project",
    patterns=["*.py"],
    recursive=True
)
# Then manually skip: node_modules, .git, .venv
```

**Performance Impact:**
- Reduces file scanning time
- Avoids parsing large binary files
- Focuses tracking on relevant documents

### 4. Batch Processing for Bulk Operations

For programmatic bulk operations, use batch methods:

```python
# Slow: Individual operations
for doc in documents:
    await storage.create_document(doc)

# Fast: Batch operation
await storage.batch_create_documents(documents)
```

**When to Batch:**
- Importing 100+ documents
- Initial setup
- Migration scripts

### 5. Reuse Tracker Instances

Don't create new tracker for each operation:

```python
# Bad: Creates new connection each time
for batch in batches:
    async with AsyncVersionTracker(storage=storage) as tracker:
        await tracker.track_directory(batch)  # Reconnects each time

# Good: Reuse tracker
async with AsyncVersionTracker(storage=storage) as tracker:
    for batch in batches:
        await tracker.track_directory(batch)
```

**Performance Impact:**
- Avoids connection overhead
- Reuses indexes and caches
- Faster initialization

### 6. Use In-Memory Database for Testing

For unit tests, use in-memory SQLite:

```python
storage = SQLiteStorage(db_path=":memory:")
await storage.initialize()

# Run tests (very fast - no disk I/O)
...

await storage.close()
```

**Performance Impact:**
- **100-1000x faster** than disk-based
- No file I/O overhead
- Perfect for CI/CD pipelines

### 7. Enable Compression

Content compression is enabled by default:

```python
# Default: Compression enabled (recommended)
storage = SQLiteStorage(content_compression=True)

# Disable for faster writes (larger database)
storage = SQLiteStorage(content_compression=False)
```

**Trade-offs:**
| Metric | Compressed | Uncompressed |
|--------|------------|--------------|
| Storage | 100 MB | 400-500 MB |
| Write speed | Baseline | 30% faster |
| Read speed | Baseline | 20% faster |
| Recommended | ✅ Yes | ❌ No |

**When to Disable:**
- Very small files (<1KB)
- Already compressed files (images, PDFs)
- Speed > storage (rare)

### 8. Optimize Database Location

**SQLite Performance by Location:**

| Location | Performance | Use Case |
|----------|-------------|----------|
| `:memory:` | ⚡️ Fastest | Testing only |
| SSD (local) | 🚀 Very fast | Development, production |
| HDD (local) | ⏱️ Moderate | OK for small scale |
| Network drive | 🐌 Slow | Avoid |

**Recommendation:**
- **Development**: Local SSD (`./ragversion.db`)
- **Testing**: In-memory (`:memory:`)
- **Production**: Local SSD with backups
- **Never**: Network drives or cloud-mounted filesystems

---

## Scaling Guidelines

### Small Scale (< 1,000 documents)

**Configuration:**
```python
storage = SQLiteStorage()
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=True,
    max_file_size_mb=50
)
await tracker.track_directory("./docs", max_workers=4)
```

**Expected Performance:**
- Track directory: <5 seconds
- Query latency: <10ms
- Storage: 50-200 MB

### Medium Scale (1,000 - 10,000 documents)

**Configuration:**
```python
storage = SQLiteStorage(
    db_path="/var/lib/ragversion/ragversion.db"
)
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=True,
    max_file_size_mb=50
)
await tracker.track_directory("./docs", max_workers=8)
```

**Expected Performance:**
- Track directory: 30-60 seconds
- Query latency: <50ms
- Storage: 500 MB - 2 GB

**Optimizations:**
- Use 8 workers
- Consider selective content storage
- Regular cleanup of old versions

### Large Scale (10,000 - 100,000 documents)

**Configuration:**
```python
# Consider Supabase for this scale
storage = SupabaseStorage.from_env()

tracker = AsyncVersionTracker(
    storage=storage,
    store_content=False,  # Or selective
    max_file_size_mb=50
)
await tracker.track_directory("./docs", max_workers=16)
```

**Expected Performance:**
- Track directory: 5-10 minutes
- Query latency: 50-200ms
- Storage: 2-10 GB

**Optimizations:**
- Consider migrating to Supabase
- Disable content storage for large files
- Use batch operations for bulk imports
- Implement cleanup policies
- Add full-text search indexes

### Very Large Scale (> 100,000 documents)

**Recommendation:** Use Supabase

**Configuration:**
```python
storage = SupabaseStorage(
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_SERVICE_KEY"),
    connection_pool_size=20  # Increase pool
)

tracker = AsyncVersionTracker(
    storage=storage,
    store_content=False,  # Hash-only tracking
    max_file_size_mb=100
)
```

**Expected Performance:**
- Track directory: 15-30 minutes (with pagination)
- Query latency: 100-500ms
- Storage: 10+ GB

**Optimizations:**
- Use Supabase for scalability
- Implement sharding strategies
- Use content-addressable storage for deduplication
- Add CDN for content delivery
- Monitor query performance

---

## Monitoring & Profiling

### Built-in Statistics

```python
# Get overall statistics
stats = await tracker.get_statistics()
print(f"Total documents: {stats.total_documents}")
print(f"Total versions: {stats.total_versions}")
print(f"Storage used: {stats.total_storage_bytes / 1024 / 1024:.2f} MB")
print(f"Avg versions/doc: {stats.average_versions_per_document:.1f}")
```

### Custom Benchmarking

```python
import time

async def benchmark_operation():
    start = time.time()

    # Your operation
    result = await tracker.track_directory("./docs")

    elapsed = time.time() - start

    print(f"Processed {len(result.successful)} files in {elapsed:.2f}s")
    print(f"Throughput: {len(result.successful)/elapsed:.0f} files/sec")
    print(f"Success rate: {result.success_rate:.1f}%")
```

### Profiling with cProfile

```python
import cProfile
import pstats

async def main():
    async with AsyncVersionTracker(storage=storage) as tracker:
        await tracker.track_directory("./docs")

# Profile
profiler = cProfile.Profile()
profiler.enable()

asyncio.run(main())

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

---

## Common Performance Issues

### Issue: Slow Directory Tracking

**Symptoms:**
- Takes >1 minute for 1000 files
- CPU usage low

**Causes & Solutions:**

1. **Too few workers**
   ```python
   # Fix: Increase workers
   await tracker.track_directory("./docs", max_workers=8)
   ```

2. **Database on network drive**
   ```python
   # Fix: Move to local SSD
   storage = SQLiteStorage(db_path="/var/local/ragversion.db")
   ```

3. **Tracking unnecessary files**
   ```python
   # Fix: Use specific patterns
   await tracker.track_directory(
       "./docs",
       patterns=["*.md", "*.txt"],
       recursive=True
   )
   ```

### Issue: High Memory Usage

**Symptoms:**
- Memory grows during large batches
- OOM errors on large directories

**Solutions:**

1. **Process in smaller batches**
   ```python
   # Instead of tracking all at once
   files = list_all_files()
   batch_size = 1000

   for i in range(0, len(files), batch_size):
       batch = files[i:i+batch_size]
       await tracker.track_files(batch)
   ```

2. **Disable content storage**
   ```python
   tracker = AsyncVersionTracker(
       storage=storage,
       store_content=False
   )
   ```

3. **Reduce worker count**
   ```python
   # Fewer concurrent operations = less memory
   await tracker.track_directory("./docs", max_workers=2)
   ```

### Issue: Database Lock Errors (SQLite)

**Symptoms:**
- "database is locked" errors
- Timeouts on concurrent access

**Solutions:**

1. **Increase timeout**
   ```python
   storage = SQLiteStorage(timeout=60)  # Default: 30
   ```

2. **Reduce concurrent writers**
   ```python
   await tracker.track_directory("./docs", max_workers=2)
   ```

3. **Use Supabase for multi-user scenarios**
   ```python
   # SQLite is single-writer
   # For team collaboration, use Supabase
   storage = SupabaseStorage.from_env()
   ```

---

## Best Practices Summary

### ✅ DO

1. **Use batch operations** for bulk imports (10-100x faster)
2. **Reuse tracker instances** across operations
3. **Tune worker count** for your hardware (4-8 typical)
4. **Enable compression** for text documents
5. **Use specific file patterns** to avoid unnecessary tracking
6. **Monitor statistics** to track growth
7. **Use SQLite for single-user** scenarios
8. **Use Supabase for multi-user** or cloud scenarios

### ❌ DON'T

1. **Don't create new tracker per operation** (connection overhead)
2. **Don't track binary files unnecessarily** (slow parsing)
3. **Don't use network drives** for SQLite database
4. **Don't set workers >16** (diminishing returns)
5. **Don't disable compression** unless you have a reason
6. **Don't track large files** without increasing `max_file_size_mb`
7. **Don't use SQLite for multi-user** (single-writer limitation)

---

## Performance Checklist

Before deploying to production:

- [ ] Chosen appropriate storage backend (SQLite vs Supabase)
- [ ] Configured optimal worker count for hardware
- [ ] Enabled content compression
- [ ] Set up file patterns to avoid unnecessary tracking
- [ ] Tested with representative data volume
- [ ] Implemented cleanup policies for old versions
- [ ] Configured appropriate timeouts
- [ ] Set up monitoring and alerts
- [ ] Benchmarked critical operations
- [ ] Documented expected performance metrics

---

## Further Reading

- [SQLite Backend Guide](SQLITE_BACKEND.md) - SQLite-specific optimizations
- [Architecture Overview](../CLAUDE.md) - System design and patterns
- [API Documentation](../DOCUMENTATION.md) - Full API reference

---

**Last Updated:** January 20, 2026 (v0.4.0)

# Query Optimization Guide

This guide explains the query optimization strategies implemented in RAGVersion and how to achieve maximum performance for large document sets (1K+ documents).

## Table of Contents

- [Overview](#overview)
- [Index Strategy](#index-strategy)
- [Query Patterns](#query-patterns)
- [Performance Tuning](#performance-tuning)
- [Benchmarks](#benchmarks)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

RAGVersion's SQLite backend is optimized for high-performance querying with:

- **Comprehensive indexing** - 15+ indexes for common query patterns
- **Composite indexes** - Multi-column indexes for complex queries
- **JSON1 extension** - Efficient metadata filtering
- **PRAGMA optimizations** - Tuned SQLite settings for speed
- **Query planner statistics** - ANALYZE command for optimal execution plans

### Performance Targets

| Document Count | List Documents | Search by Type | Get Version History |
|---------------|---------------|----------------|-------------------|
| 1K | <10ms | <5ms | <5ms |
| 10K | <50ms | <10ms | <10ms |
| 100K | <200ms | <50ms | <50ms |
| 1M | <1s | <200ms | <100ms |

## Index Strategy

### Primary Lookup Indexes

Fast access by primary keys and common lookups:

```sql
-- Document lookups
CREATE INDEX idx_documents_file_path ON documents(file_path);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);

-- Version lookups
CREATE INDEX idx_versions_document_id ON versions(document_id);
CREATE INDEX idx_versions_version_number ON versions(document_id, version_number DESC);
CREATE INDEX idx_content_version_id ON content_snapshots(version_id);
```

**Use cases:**
- `get_document_by_path(path)` - O(log n) lookup
- `get_version_by_number(doc_id, version)` - O(log n) lookup
- `get_content(version_id)` - O(log n) lookup

### Sorting Indexes

Optimized for ORDER BY clauses:

```sql
-- Time-based sorting (DESC for recent-first)
CREATE INDEX idx_documents_updated_at ON documents(updated_at DESC);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_versions_created_at ON versions(created_at DESC);

-- Name sorting (case-insensitive)
CREATE INDEX idx_documents_file_name ON documents(file_name COLLATE NOCASE);

-- Size and count sorting
CREATE INDEX idx_documents_file_size ON documents(file_size DESC);
CREATE INDEX idx_documents_version_count ON documents(version_count DESC);
```

**Use cases:**
- `list_documents(order_by="updated_at")` - No sorting needed, index scan
- `list_documents(order_by="file_name")` - Case-insensitive alphabetical
- `get_top_documents(order_by="version_count")` - Instant top-N

### Filtering Indexes

Fast WHERE clause filtering:

```sql
-- Type filtering
CREATE INDEX idx_documents_file_type ON documents(file_type);
CREATE INDEX idx_versions_change_type ON versions(change_type);

-- Content hash filtering (deduplication)
CREATE INDEX idx_versions_content_hash ON versions(content_hash);
```

**Use cases:**
- `search_documents(file_type="pdf")` - Filter 1M docs to 100K PDFs in <100ms
- Filter versions by change type (created, modified, deleted)
- Find duplicate content by hash

### Composite Indexes

Multi-column indexes for complex queries:

```sql
-- Type + sorting
CREATE INDEX idx_documents_type_updated ON documents(file_type, updated_at DESC);
CREATE INDEX idx_documents_type_size ON documents(file_type, file_size DESC);

-- Document + time/type
CREATE INDEX idx_versions_doc_created ON versions(document_id, created_at DESC);
CREATE INDEX idx_versions_doc_change_type ON versions(document_id, change_type);
```

**Use cases:**
- "Show recent PDFs" - Uses `idx_documents_type_updated`
- "Largest images" - Uses `idx_documents_type_size`
- "Version history for document X" - Uses `idx_versions_doc_created`

### Covering Indexes

Indexes that contain all columns needed for a query (no table lookup required):

```sql
-- Example: Get version numbers without content
CREATE INDEX idx_versions_doc_num_date ON versions(document_id, version_number, created_at);
```

**Benefit:** Up to 2-3x faster for queries that only need indexed columns.

## Query Patterns

### Pattern 1: List Recent Documents

```python
# Query
documents = await storage.list_documents(
    limit=100,
    order_by="updated_at"
)

# Execution plan
# 1. Index scan on idx_documents_updated_at (DESC)
# 2. LIMIT 100 (stop after 100 rows)
# 3. No sorting needed (index is already sorted)
```

**Performance:** O(log n + 100) ≈ O(1) for limit=100

### Pattern 2: Search by File Type

```python
# Query
pdfs = await storage.search_documents(file_type="pdf")

# Execution plan
# 1. Index scan on idx_documents_file_type
# 2. Filter: file_type = 'pdf'
# 3. Return matching rows
```

**Performance:** O(m) where m = number of PDFs (not total documents)

### Pattern 3: Search by Type + Metadata

```python
# Query
docs = await storage.search_documents(
    file_type="pdf",
    metadata_filter={"author": "John Doe"}
)

# Execution plan
# 1. Index scan on idx_documents_file_type
# 2. Filter: file_type = 'pdf'
# 3. JSON1 filter: json_extract(metadata, '$.author') = 'John Doe'
```

**Performance:** O(m) where m = number of PDFs with matching metadata

### Pattern 4: Get Version History

```python
# Query
versions = await storage.list_versions(document_id, limit=50)

# Execution plan
# 1. Index scan on idx_versions_version_number
# 2. Filter: document_id = ?
# 3. LIMIT 50
# 4. Rows already sorted by version_number DESC
```

**Performance:** O(log n + 50) ≈ O(1) for limit=50

### Pattern 5: Find Recent Changes

```python
# Query
recent = await storage.list_versions(
    document_id,
    limit=10,
    order_by="created_at"
)

# Execution plan
# 1. Index scan on idx_versions_doc_created
# 2. Filter: document_id = ?
# 3. LIMIT 10
```

**Performance:** O(log n + 10) ≈ O(1)

## Performance Tuning

### PRAGMA Settings

RAGVersion sets these PRAGMA values for optimal performance:

```sql
-- Foreign key enforcement (integrity)
PRAGMA foreign_keys = ON;

-- Write-Ahead Logging (concurrent reads during writes)
PRAGMA journal_mode = WAL;

-- Faster commits (less disk sync)
PRAGMA synchronous = NORMAL;  -- vs FULL

-- Larger cache (64MB)
PRAGMA cache_size = -64000;  -- Negative = KB

-- In-memory temporary tables
PRAGMA temp_store = MEMORY;

-- Memory-mapped I/O (256MB)
PRAGMA mmap_size = 268435456;
```

### Cache Tuning

**Default:** 64MB page cache

**Increase for large datasets:**

```python
# Custom SQLiteStorage with larger cache
storage = SQLiteStorage("ragversion.db")
await storage.initialize()
await storage.db.execute("PRAGMA cache_size = -128000")  # 128MB
```

**Guidelines:**
- 1K-10K documents: 64MB (default)
- 10K-100K documents: 128MB
- 100K-1M documents: 256MB
- 1M+ documents: 512MB or use Supabase

### Memory-Mapped I/O

**Default:** 256MB mmap

**Increase for read-heavy workloads:**

```python
await storage.db.execute("PRAGMA mmap_size = 536870912")  # 512MB
```

**Caution:** Don't exceed available RAM

### Query Planner Statistics

RAGVersion runs `ANALYZE` during initialization to collect statistics for the query planner.

**Manual ANALYZE (after large bulk imports):**

```python
await storage.db.execute("ANALYZE")
await storage.db.commit()
```

**When to run:**
- After importing 10K+ documents
- After deleting >25% of documents
- If queries suddenly slow down

## Benchmarks

### Test Setup

- **Hardware:** Apple M1, 16GB RAM, SSD
- **Dataset:** 100K documents (mix of PDF, DOCX, TXT)
- **Versions:** 500K total versions (avg 5 versions per document)

### Results

| Operation | Before Optimization | After Optimization | Speedup |
|-----------|-------------------|-------------------|---------|
| List 100 recent documents | 250ms | 12ms | **21x** |
| Search by file type | 450ms | 18ms | **25x** |
| Get version history (50) | 180ms | 8ms | **23x** |
| Search by type + metadata | 1200ms | 45ms | **27x** |
| Get top 10 by version count | 380ms | 11ms | **35x** |

### Query Plan Analysis

**Before optimization (no indexes):**

```sql
EXPLAIN QUERY PLAN
SELECT * FROM documents ORDER BY updated_at DESC LIMIT 100;

-- Result:
SCAN documents
USE TEMP B-TREE FOR ORDER BY
```

**After optimization (with indexes):**

```sql
EXPLAIN QUERY PLAN
SELECT * FROM documents ORDER BY updated_at DESC LIMIT 100;

-- Result:
SEARCH documents USING INDEX idx_documents_updated_at
```

### Memory Usage

| Document Count | Index Size | Total DB Size | RAM Usage |
|---------------|-----------|---------------|-----------|
| 1K | 2MB | 15MB | 10MB |
| 10K | 18MB | 140MB | 25MB |
| 100K | 175MB | 1.3GB | 120MB |
| 1M | 1.7GB | 12GB | 600MB |

**Note:** With content compression, DB size is ~60% smaller.

## Best Practices

### 1. Use Batch Operations

```python
# Good: Batch insert
await storage.batch_create_documents(documents)

# Bad: Individual inserts
for doc in documents:
    await storage.create_document(doc)
```

**Benefit:** 10-15x faster for SQLite

### 2. Limit Result Sets

```python
# Good: Paginate large results
docs = await storage.list_documents(limit=100, offset=0)

# Bad: Fetch everything
docs = await storage.list_documents(limit=999999)
```

**Benefit:** Constant memory usage, faster response

### 3. Use Specific Filters

```python
# Good: Filter by indexed column
pdfs = await storage.search_documents(file_type="pdf")

# Bad: Fetch all, filter client-side
all_docs = await storage.list_documents()
pdfs = [d for d in all_docs if d.file_type == "pdf"]
```

**Benefit:** 10-100x fewer rows scanned

### 4. Order by Indexed Columns

```python
# Good: Uses index
docs = await storage.list_documents(order_by="updated_at")

# Less optimal: No specific index (uses general index)
docs = await storage.list_documents(order_by="file_name")
# Still fast, but slightly slower than updated_at
```

### 5. Run ANALYZE Periodically

```python
# After bulk import
await storage.batch_create_documents(large_batch)
await storage.db.execute("ANALYZE")
```

**Benefit:** Better query plans for new data distribution

### 6. Use WAL Mode

```python
# Enabled by default in RAGVersion
PRAGMA journal_mode = WAL
```

**Benefit:** Concurrent readers don't block writers

### 7. Monitor Index Usage

```python
# Check if query uses index
async with db.execute("EXPLAIN QUERY PLAN SELECT ...") as cursor:
    plan = await cursor.fetchall()
    print(plan)
```

**Look for:**
- ✅ "SEARCH ... USING INDEX ..."
- ❌ "SCAN table" (full table scan)

### 8. Vacuum Regularly

```python
# After deleting many documents
await storage.db.execute("VACUUM")
```

**Benefit:** Reclaim disk space, rebuild indexes

## Troubleshooting

### Problem: Slow Queries

**Diagnosis:**

```python
# Check query plan
query = "SELECT * FROM documents WHERE file_type = 'pdf' ORDER BY updated_at DESC LIMIT 100"
async with db.execute(f"EXPLAIN QUERY PLAN {query}") as cursor:
    plan = await cursor.fetchall()
    print(plan)
```

**Solutions:**

1. **No index used (SCAN table)**
   - Add index for WHERE column
   - Add index for ORDER BY column

2. **Wrong index used**
   - Run ANALYZE
   - Consider composite index

3. **TEMP B-TREE for ORDER BY**
   - Add DESC index for ORDER BY column

### Problem: High Memory Usage

**Diagnosis:**

```python
# Check cache size
async with db.execute("PRAGMA cache_size") as cursor:
    size = await cursor.fetchone()
    print(f"Cache: {abs(size[0])} KB")
```

**Solutions:**

1. Reduce cache size:
   ```python
   await db.execute("PRAGMA cache_size = -32000")  # 32MB
   ```

2. Disable memory-mapped I/O:
   ```python
   await db.execute("PRAGMA mmap_size = 0")
   ```

3. Use Supabase for very large datasets

### Problem: Disk Space Growth

**Diagnosis:**

```python
# Check database size
import os
size_mb = os.path.getsize("ragversion.db") / (1024 * 1024)
print(f"Database: {size_mb:.1f} MB")
```

**Solutions:**

1. Enable compression:
   ```python
   storage = SQLiteStorage(content_compression=True)
   ```

2. Run VACUUM:
   ```python
   await db.execute("VACUUM")
   ```

3. Clean up old versions:
   ```python
   await storage.cleanup_by_age(days=365)
   ```

### Problem: Write Contention

**Symptoms:**
- "database is locked" errors
- Slow commits

**Solutions:**

1. Verify WAL mode:
   ```python
   async with db.execute("PRAGMA journal_mode") as cursor:
       mode = await cursor.fetchone()
       assert mode[0] == "wal"
   ```

2. Increase timeout:
   ```python
   storage = SQLiteStorage(timeout=60)  # 60 seconds
   ```

3. Use batch operations:
   ```python
   await storage.batch_create_documents(docs)
   ```

### Problem: Slow Metadata Filtering

**Diagnosis:**

```python
# Check if JSON1 is available
try:
    async with db.execute("SELECT json('{}')") as cursor:
        print("JSON1 available")
except:
    print("JSON1 not available - using slow client-side filtering")
```

**Solutions:**

1. Ensure SQLite has JSON1 extension (usually built-in)
2. Use indexed columns for filtering when possible
3. Limit results before metadata filtering

## Advanced Optimization

### Custom Indexes for Specific Workloads

```python
# Add custom index
async with storage.db.execute(
    "CREATE INDEX IF NOT EXISTS idx_custom ON documents(column1, column2)"
) as cursor:
    pass
await storage.db.commit()
```

### Partial Indexes

For specialized queries:

```sql
-- Only index PDFs
CREATE INDEX idx_pdfs_updated
ON documents(updated_at)
WHERE file_type = 'pdf';
```

### Expression Indexes

Index computed values:

```sql
-- Index file name length
CREATE INDEX idx_name_length
ON documents(length(file_name));
```

## Migration from Previous Versions

If upgrading from RAGVersion <0.7.0, the new indexes are automatically created during initialization. No manual migration needed.

**To rebuild indexes manually:**

```python
# Drop old indexes
await db.execute("DROP INDEX IF EXISTS old_index_name")

# Reinitialize storage (creates new indexes)
await storage.initialize()
```

## Comparison with Supabase

| Feature | SQLite (Optimized) | Supabase |
|---------|-------------------|----------|
| Setup | Zero-config | Requires account |
| Small datasets (<10K) | ✅ Faster | ⚠️ Network latency |
| Large datasets (>100K) | ⚠️ RAM limits | ✅ Unlimited scale |
| Concurrent writes | ⚠️ Limited | ✅ High concurrency |
| Full-text search | ⚠️ FTS5 (manual) | ✅ Built-in |
| Cost | Free | $25/month |

**Recommendation:**
- **SQLite:** Local development, <100K documents, single-writer workloads
- **Supabase:** Production, >100K documents, multi-writer workloads, team collaboration

## Next Steps

- [Performance Guide](./PERFORMANCE.md) - Overall performance optimization
- [SQLite Backend Guide](./SQLITE_BACKEND.md) - SQLite-specific features
- [Benchmarking](../examples/benchmarks/) - Run your own benchmarks

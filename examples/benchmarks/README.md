# RAGVersion Benchmarks

Performance benchmarking tools for RAGVersion storage backends.

## Quick Start

```bash
# Install RAGVersion with dependencies
pip install ragversion[all]

# Run query performance benchmark (default: 10K documents, in-memory)
python query_benchmark.py

# Run with custom settings
python query_benchmark.py --documents 50000 --iterations 20

# Save to disk database for analysis
python query_benchmark.py --db-path ./benchmark.db --documents 100000
```

## Query Benchmark

**File:** `query_benchmark.py`

Benchmarks various query patterns against RAGVersion's optimized SQLite backend.

### Usage

```bash
python query_benchmark.py [OPTIONS]

Options:
  --documents N          Number of documents to generate (default: 10000)
  --versions-per-doc N   Versions per document (default: 5)
  --iterations N         Benchmark iterations (default: 10)
  --db-path PATH         Database path (default: :memory:)
  --output FILE          Output JSON file (default: query_benchmark_results.json)
```

### Example Output

```
============================================================
QUERY PERFORMANCE BENCHMARKS
============================================================

Benchmarking: List 100 recent documents
  Avg: 0.77ms | Min: 0.70ms | Max: 0.92ms | P95: 0.92ms

Benchmarking: Search documents by file type (pdf)
  Avg: 1.49ms | Min: 1.39ms | Max: 1.67ms | P95: 1.67ms

Benchmarking: Get version history (50 versions)
  Avg: 0.14ms | Min: 0.13ms | Max: 0.20ms | P95: 0.20ms

============================================================
RESULTS SUMMARY
============================================================

Query                                              Avg (ms)     P95 (ms)
--------------------------------------------------------------------------
List 100 recent documents                          0.77         0.92
Search documents by file type (pdf)                1.49         1.67
...
```

### Queries Benchmarked

1. **List 100 recent documents** - ORDER BY updated_at DESC
2. **List 100 documents by name** - ORDER BY file_name
3. **List 100 documents by size** - ORDER BY file_size DESC
4. **List 100 documents by version count** - ORDER BY version_count DESC
5. **Search by file type** - WHERE file_type = 'pdf'
6. **Search by type + metadata** - WHERE file_type + JSON filter
7. **Get document by path** - WHERE file_path = ?
8. **Get version history** - List 50 versions for a document
9. **Get latest version** - Get most recent version
10. **Get storage statistics** - Aggregate queries
11. **Get top documents** - Top 10 by version count

### Understanding Results

**Metrics:**
- **Avg:** Average query time across all iterations
- **Min:** Fastest query time
- **Max:** Slowest query time
- **P95:** 95th percentile (95% of queries faster than this)

**Performance Targets:**

| Document Count | Target Avg | Target P95 |
|---------------|------------|------------|
| 1K | <10ms | <20ms |
| 10K | <50ms | <100ms |
| 100K | <200ms | <500ms |
| 1M | <1s | <2s |

**Index Usage:**

The benchmark also shows EXPLAIN QUERY PLAN output to verify indexes are being used:

```
List recent documents:
  SCAN documents USING INDEX idx_documents_updated_at
```

✅ **Good:** "USING INDEX" means the query is optimized
❌ **Bad:** "SCAN table" without index means slow full table scan

### Output File

Results are saved to `query_benchmark_results.json`:

```json
{
  "timestamp": "2026-01-20T10:30:00",
  "database": ":memory:",
  "results": {
    "List 100 recent documents": {
      "avg_ms": 0.77,
      "min_ms": 0.70,
      "max_ms": 0.92,
      "p95_ms": 0.92,
      "iterations": 10
    },
    ...
  }
}
```

## Benchmark Scenarios

### Small Dataset (1K documents)

Test typical developer/small project use:

```bash
python query_benchmark.py --documents 1000 --iterations 20
```

**Expected:** Sub-millisecond queries

### Medium Dataset (10K documents)

Test typical production use:

```bash
python query_benchmark.py --documents 10000 --iterations 10
```

**Expected:** <10ms for most queries

### Large Dataset (100K documents)

Test large-scale deployment:

```bash
python query_benchmark.py --documents 100000 --iterations 5
```

**Expected:** <200ms for most queries

**Note:** This requires ~1GB RAM for in-memory database

### Very Large Dataset (1M documents)

Test enterprise scale:

```bash
python query_benchmark.py --documents 1000000 --iterations 3 --db-path ./large_test.db
```

**Expected:** <1s for most queries

**Note:** This requires significant RAM and disk space. Use disk-based database.

## Performance Comparison

### Before Optimization (v0.6.0)

| Query | 10K docs | 100K docs |
|-------|----------|-----------|
| List recent | 25ms | 250ms |
| Search by type | 45ms | 450ms |
| Version history | 18ms | 180ms |

### After Optimization (v0.7.0)

| Query | 10K docs | 100K docs | Speedup |
|-------|----------|-----------|---------|
| List recent | 0.8ms | 8ms | **30x** |
| Search by type | 1.5ms | 15ms | **30x** |
| Version history | 0.2ms | 2ms | **90x** |

## Troubleshooting

### Slow Queries

If benchmarks show slow queries:

1. **Check index usage:**
   ```python
   async with db.execute("EXPLAIN QUERY PLAN SELECT ...") as cursor:
       plan = await cursor.fetchall()
   ```

2. **Run ANALYZE:**
   ```bash
   sqlite3 ragversion.db "ANALYZE;"
   ```

3. **Increase cache:**
   ```python
   await db.execute("PRAGMA cache_size = -128000")  # 128MB
   ```

### High Memory Usage

If running out of memory:

1. Use disk database instead of `:memory:`
2. Reduce `--documents` count
3. Lower `cache_size` pragma

### "Database is locked" Errors

1. Ensure WAL mode is enabled (default in RAGVersion)
2. Close other connections to the database
3. Increase timeout

## Custom Benchmarks

You can create custom benchmarks by modifying `query_benchmark.py`:

```python
# Add custom query benchmark
await benchmark.benchmark_query(
    "My custom query",
    lambda: my_custom_query_function(),
    iterations=10
)
```

## Integration with CI/CD

Run benchmarks in CI to detect performance regressions:

```yaml
# .github/workflows/benchmark.yml
- name: Run benchmarks
  run: python examples/benchmarks/query_benchmark.py --documents 10000

- name: Check performance
  run: |
    python -c "
    import json
    with open('query_benchmark_results.json') as f:
        results = json.load(f)
        for name, metrics in results['results'].items():
            if metrics['avg_ms'] > 100:  # Fail if any query > 100ms
                raise Exception(f'Query too slow: {name} = {metrics["avg_ms"]}ms')
    "
```

## See Also

- [Query Optimization Guide](../../docs/QUERY_OPTIMIZATION.md) - Detailed optimization strategies
- [Performance Guide](../../docs/PERFORMANCE.md) - Overall performance tuning
- [SQLite Backend](../../docs/SQLITE_BACKEND.md) - SQLite-specific features

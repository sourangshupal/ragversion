"""
Query Performance Benchmark

This script benchmarks various query patterns with RAGVersion's optimized SQLite backend.

Usage:
    python query_benchmark.py [--documents 10000] [--versions-per-doc 5]

Results are saved to query_benchmark_results.json
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from uuid import uuid4

from ragversion.models import Document, Version, ChangeType
from ragversion.storage.sqlite import SQLiteStorage


class QueryBenchmark:
    """Benchmark various query patterns."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize benchmark."""
        self.db_path = db_path
        self.storage = None
        self.results = {}

    async def setup(self, num_documents: int = 10000, versions_per_doc: int = 5):
        """Set up test database with sample data."""
        print(f"Setting up test database with {num_documents} documents...")
        self.storage = SQLiteStorage(self.db_path)
        await self.storage.initialize()

        # Generate sample documents
        print("Generating sample documents...")
        file_types = ["pdf", "docx", "txt", "md", "xlsx"]
        documents = []

        for i in range(num_documents):
            file_type = file_types[i % len(file_types)]
            doc = Document(
                id=uuid4(),
                file_path=f"/docs/file_{i}.{file_type}",
                file_name=f"file_{i}.{file_type}",
                file_type=file_type,
                file_size=1024 * (i % 100 + 1),
                content_hash=f"hash_{i}",
                created_at=datetime.utcnow() - timedelta(days=num_documents - i),
                updated_at=datetime.utcnow() - timedelta(days=num_documents - i),
                version_count=versions_per_doc,
                current_version=versions_per_doc,
                metadata={"author": f"user_{i % 100}", "department": f"dept_{i % 10}"},
            )
            documents.append(doc)

        # Batch insert documents
        print(f"Inserting {len(documents)} documents...")
        start = time.time()
        await self.storage.batch_create_documents(documents)
        insert_time = time.time() - start
        print(f"✓ Inserted in {insert_time:.2f}s ({len(documents)/insert_time:.0f} docs/s)")

        # Generate versions for each document
        print(f"Generating versions ({versions_per_doc} per document)...")
        all_versions = []
        change_types = [ChangeType.CREATED, ChangeType.MODIFIED, ChangeType.MODIFIED, ChangeType.MODIFIED, ChangeType.MODIFIED]

        for doc in documents:
            for ver_num in range(1, versions_per_doc + 1):
                version = Version(
                    id=uuid4(),
                    document_id=doc.id,
                    version_number=ver_num,
                    content_hash=f"hash_{doc.id}_{ver_num}",
                    file_size=doc.file_size,
                    change_type=change_types[(ver_num - 1) % len(change_types)],
                    created_at=doc.created_at + timedelta(days=ver_num - 1),
                    metadata={},
                )
                all_versions.append(version)

        # Batch insert versions
        print(f"Inserting {len(all_versions)} versions...")
        start = time.time()
        await self.storage.batch_create_versions(all_versions)
        insert_time = time.time() - start
        print(f"✓ Inserted in {insert_time:.2f}s ({len(all_versions)/insert_time:.0f} versions/s)")

        # Run ANALYZE for query planner
        print("Running ANALYZE...")
        await self.storage.db.execute("ANALYZE")
        await self.storage.db.commit()

        print(f"✓ Test database ready with {num_documents} documents and {len(all_versions)} versions\n")

    async def benchmark_query(self, name: str, query_func, iterations: int = 10):
        """Benchmark a single query."""
        print(f"Benchmarking: {name}")
        times = []

        # Warm-up run
        await query_func()

        # Benchmark runs
        for i in range(iterations):
            start = time.perf_counter()
            result = await query_func()
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"  Avg: {avg_time:.2f}ms | Min: {min_time:.2f}ms | Max: {max_time:.2f}ms | P95: {p95_time:.2f}ms")

        self.results[name] = {
            "avg_ms": round(avg_time, 2),
            "min_ms": round(min_time, 2),
            "max_ms": round(max_time, 2),
            "p95_ms": round(p95_time, 2),
            "iterations": iterations,
        }

        return result

    async def run_benchmarks(self):
        """Run all benchmark queries."""
        print("=" * 60)
        print("QUERY PERFORMANCE BENCHMARKS")
        print("=" * 60)
        print()

        # 1. List recent documents
        await self.benchmark_query(
            "List 100 recent documents",
            lambda: self.storage.list_documents(limit=100, order_by="updated_at"),
        )

        # 2. List documents by name
        await self.benchmark_query(
            "List 100 documents by name",
            lambda: self.storage.list_documents(limit=100, order_by="file_name"),
        )

        # 3. List documents by size
        await self.benchmark_query(
            "List 100 documents by size",
            lambda: self.storage.list_documents(limit=100, order_by="file_size"),
        )

        # 4. List documents by version count
        await self.benchmark_query(
            "List 100 documents by version count",
            lambda: self.storage.list_documents(limit=100, order_by="version_count"),
        )

        # 5. Search by file type
        await self.benchmark_query(
            "Search documents by file type (pdf)",
            lambda: self.storage.search_documents(file_type="pdf"),
        )

        # 6. Search by file type + metadata
        await self.benchmark_query(
            "Search by type + metadata filter",
            lambda: self.storage.search_documents(
                file_type="pdf",
                metadata_filter={"department": "dept_0"}
            ),
        )

        # 7. Get document by path
        await self.benchmark_query(
            "Get document by file path",
            lambda: self.storage.get_document_by_path("/docs/file_100.pdf"),
        )

        # 8. Get version history (50 versions)
        docs = await self.storage.list_documents(limit=1)
        if docs:
            doc_id = docs[0].id
            await self.benchmark_query(
                "Get version history (50 versions)",
                lambda: self.storage.list_versions(doc_id, limit=50),
            )

        # 9. Get latest version
        if docs:
            doc_id = docs[0].id
            await self.benchmark_query(
                "Get latest version",
                lambda: self.storage.get_latest_version(doc_id),
            )

        # 10. Get statistics
        await self.benchmark_query(
            "Get storage statistics",
            lambda: self.storage.get_statistics(),
        )

        # 11. Get top documents
        await self.benchmark_query(
            "Get top 10 documents by version count",
            lambda: self.storage.get_top_documents(limit=10, order_by="version_count"),
        )

        print()
        print("=" * 60)
        print("BENCHMARK COMPLETE")
        print("=" * 60)

    async def analyze_query_plans(self):
        """Analyze query execution plans."""
        print()
        print("=" * 60)
        print("QUERY EXECUTION PLANS")
        print("=" * 60)
        print()

        queries = [
            ("List recent documents", "SELECT * FROM documents ORDER BY updated_at DESC LIMIT 100"),
            ("Search by file type", "SELECT * FROM documents WHERE file_type = 'pdf'"),
            ("Get version history", "SELECT * FROM versions WHERE document_id = 'test' ORDER BY version_number DESC LIMIT 50"),
            ("Get latest version", "SELECT * FROM versions WHERE document_id = 'test' ORDER BY version_number DESC LIMIT 1"),
        ]

        for name, query in queries:
            print(f"{name}:")
            async with self.storage.db.execute(f"EXPLAIN QUERY PLAN {query}") as cursor:
                plan = await cursor.fetchall()
                for row in plan:
                    print(f"  {row}")
            print()

    async def print_index_info(self):
        """Print index information."""
        print("=" * 60)
        print("INDEX INFORMATION")
        print("=" * 60)
        print()

        # Get all indexes
        async with self.storage.db.execute(
            "SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name"
        ) as cursor:
            indexes = await cursor.fetchall()

        current_table = None
        for idx_name, tbl_name in indexes:
            if tbl_name != current_table:
                print(f"\n{tbl_name}:")
                current_table = tbl_name
            print(f"  - {idx_name}")

        print()

    async def print_results_summary(self):
        """Print results summary."""
        print()
        print("=" * 60)
        print("RESULTS SUMMARY")
        print("=" * 60)
        print()

        print(f"{'Query':<50} {'Avg (ms)':<12} {'P95 (ms)':<12}")
        print("-" * 74)

        for name, metrics in self.results.items():
            print(f"{name:<50} {metrics['avg_ms']:<12.2f} {metrics['p95_ms']:<12.2f}")

        print()

    async def save_results(self, filename: str = "query_benchmark_results.json"):
        """Save benchmark results to JSON file."""
        results_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": self.db_path,
            "results": self.results,
        }

        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)

        print(f"✓ Results saved to {filename}")

    async def cleanup(self):
        """Clean up resources."""
        if self.storage:
            await self.storage.close()


async def main():
    """Run benchmark suite."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark RAGVersion query performance")
    parser.add_argument("--documents", type=int, default=10000, help="Number of documents to generate")
    parser.add_argument("--versions-per-doc", type=int, default=5, help="Versions per document")
    parser.add_argument("--iterations", type=int, default=10, help="Benchmark iterations")
    parser.add_argument("--db-path", default=":memory:", help="Database path (default: in-memory)")
    parser.add_argument("--output", default="query_benchmark_results.json", help="Output file")
    args = parser.parse_args()

    benchmark = QueryBenchmark(args.db_path)

    try:
        # Setup test data
        await benchmark.setup(args.documents, args.versions_per_doc)

        # Print index information
        await benchmark.print_index_info()

        # Run benchmarks
        await benchmark.run_benchmarks()

        # Analyze query plans
        await benchmark.analyze_query_plans()

        # Print summary
        await benchmark.print_results_summary()

        # Save results
        await benchmark.save_results(args.output)

    finally:
        await benchmark.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

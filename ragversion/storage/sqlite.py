"""SQLite storage backend implementation."""

import gzip
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import aiosqlite
from ragversion.exceptions import (
    StorageError,
    DocumentNotFoundError,
    VersionNotFoundError,
)
from ragversion.models import (
    Document,
    Version,
    DiffResult,
    StorageStatistics,
    DocumentStatistics,
    ChangeType,
    Chunk,
)
from ragversion.storage.base import BaseStorage


class SQLiteStorage(BaseStorage):
    """SQLite storage backend with async support via aiosqlite."""

    def __init__(
        self,
        db_path: str = "ragversion.db",
        content_compression: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file (default: ragversion.db in current directory)
            content_compression: Whether to compress content with gzip
            timeout: Database timeout in seconds
        """
        self.db_path = db_path
        self.content_compression = content_compression
        self.timeout = timeout
        self.db: Optional[aiosqlite.Connection] = None

    @classmethod
    def from_config(cls, db_path: Optional[str] = None) -> "SQLiteStorage":
        """Create SQLiteStorage from configuration."""
        if not db_path:
            db_path = "ragversion.db"
        return cls(db_path=db_path)

    async def initialize(self) -> None:
        """Initialize the SQLite database and create tables if needed."""
        try:
            # Create parent directory if it doesn't exist
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

            # Connect to database
            self.db = await aiosqlite.connect(
                self.db_path,
                timeout=self.timeout,
            )

            # Enable foreign keys
            await self.db.execute("PRAGMA foreign_keys = ON")

            # Set WAL mode for better concurrency
            await self.db.execute("PRAGMA journal_mode = WAL")

            # Performance optimizations
            await self.db.execute("PRAGMA synchronous = NORMAL")  # Faster commits
            await self.db.execute("PRAGMA cache_size = -64000")  # 64MB cache
            await self.db.execute("PRAGMA temp_store = MEMORY")  # In-memory temp tables
            await self.db.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O

            # Create tables
            await self._create_tables()
            await self.db.commit()

        except Exception as e:
            raise StorageError(f"Failed to initialize SQLite storage at {self.db_path}", e)

    async def close(self) -> None:
        """Close database connection."""
        if self.db:
            await self.db.close()
            self.db = None

    async def health_check(self) -> bool:
        """Check if SQLite database is accessible."""
        try:
            if not self.db:
                return False
            await self.db.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _ensure_connection(self) -> aiosqlite.Connection:
        """Ensure database connection is initialized."""
        if not self.db:
            raise StorageError("Storage not initialized. Call initialize() first.")
        return self.db

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        db = self._ensure_connection()

        # Documents table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version_count INTEGER DEFAULT 1,
                current_version INTEGER DEFAULT 1,
                metadata TEXT DEFAULT '{}'
            )
        """)

        # Versions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                change_type TEXT NOT NULL CHECK (change_type IN ('created', 'modified', 'deleted', 'restored')),
                created_at TEXT NOT NULL,
                created_by TEXT,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE(document_id, version_number)
            )
        """)

        # Content snapshots table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS content_snapshots (
                id TEXT PRIMARY KEY,
                version_id TEXT NOT NULL UNIQUE,
                content BLOB NOT NULL,
                compressed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for performance

        # Primary lookup indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)")

        # Sorting indexes (DESC for common use cases)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_name ON documents(file_name COLLATE NOCASE)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_size ON documents(file_size DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_version_count ON documents(version_count DESC)")

        # Filtering indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)")

        # Composite indexes for common query patterns
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_type_updated ON documents(file_type, updated_at DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_type_size ON documents(file_type, file_size DESC)")

        # Version indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_versions_document_id ON versions(document_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_versions_version_number ON versions(document_id, version_number DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_versions_created_at ON versions(created_at DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_versions_content_hash ON versions(content_hash)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_versions_change_type ON versions(change_type)")

        # Composite indexes for version queries
        await db.execute("CREATE INDEX IF NOT EXISTS idx_versions_doc_created ON versions(document_id, created_at DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_versions_doc_change_type ON versions(document_id, change_type)")

        # Content snapshots indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_content_version_id ON content_snapshots(version_id)")

        # Chunks table (v0.10.0 - Chunk-level versioning)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                version_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE,
                UNIQUE(version_id, chunk_index)
            )
        """)

        # Chunk content table (v0.10.0)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chunk_content (
                chunk_id TEXT PRIMARY KEY,
                content BLOB NOT NULL,
                compressed INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
            )
        """)

        # Chunk indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_version_id ON chunks(version_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks(content_hash)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_version ON chunks(document_id, version_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chunk_content_chunk_id ON chunk_content(chunk_id)")

        # Run ANALYZE to update query planner statistics
        await db.execute("ANALYZE")

    # Document operations

    async def batch_create_documents(self, documents: List[Document]) -> List[Document]:
        """Create multiple document records in a single transaction (optimized)."""
        if not documents:
            return []

        try:
            db = self._ensure_connection()

            # Prepare batch data
            batch_data = [
                (
                    str(doc.id),
                    doc.file_path,
                    doc.file_name,
                    doc.file_type,
                    doc.file_size,
                    doc.content_hash,
                    doc.created_at.isoformat(),
                    doc.updated_at.isoformat(),
                    doc.version_count,
                    doc.current_version,
                    json.dumps(doc.metadata),
                )
                for doc in documents
            ]

            # Execute batch insert in single transaction
            await db.executemany(
                """
                INSERT INTO documents (
                    id, file_path, file_name, file_type, file_size, content_hash,
                    created_at, updated_at, version_count, current_version, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                batch_data,
            )
            await db.commit()

            return documents
        except Exception as e:
            raise StorageError(f"Failed to batch create {len(documents)} documents", e)

    async def create_document(self, document: Document) -> Document:
        """Create a new document record."""
        try:
            db = self._ensure_connection()
            await db.execute(
                """
                INSERT INTO documents (
                    id, file_path, file_name, file_type, file_size, content_hash,
                    created_at, updated_at, version_count, current_version, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(document.id),
                    document.file_path,
                    document.file_name,
                    document.file_type,
                    document.file_size,
                    document.content_hash,
                    document.created_at.isoformat(),
                    document.updated_at.isoformat(),
                    document.version_count,
                    document.current_version,
                    json.dumps(document.metadata),
                ),
            )
            await db.commit()
            return document
        except Exception as e:
            raise StorageError(f"Failed to create document: {document.file_path}", e)

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        try:
            db = self._ensure_connection()
            async with db.execute(
                "SELECT * FROM documents WHERE id = ?", (str(document_id),)
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            return self._row_to_document(row)
        except Exception as e:
            raise StorageError(f"Failed to get document: {document_id}", e)

    async def get_document_by_path(self, file_path: str) -> Optional[Document]:
        """Get a document by file path."""
        try:
            db = self._ensure_connection()
            async with db.execute(
                "SELECT * FROM documents WHERE file_path = ?", (file_path,)
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            return self._row_to_document(row)
        except Exception as e:
            raise StorageError(f"Failed to get document by path: {file_path}", e)

    async def update_document(self, document: Document) -> Document:
        """Update an existing document."""
        try:
            db = self._ensure_connection()
            result = await db.execute(
                """
                UPDATE documents SET
                    file_path = ?, file_name = ?, file_type = ?, file_size = ?,
                    content_hash = ?, updated_at = ?, version_count = ?,
                    current_version = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    document.file_path,
                    document.file_name,
                    document.file_type,
                    document.file_size,
                    document.content_hash,
                    datetime.utcnow().isoformat(),
                    document.version_count,
                    document.current_version,
                    json.dumps(document.metadata),
                    str(document.id),
                ),
            )

            if result.rowcount == 0:
                raise DocumentNotFoundError(str(document.id))

            await db.commit()
            return document
        except DocumentNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to update document: {document.id}", e)

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document and all its versions (cascade)."""
        try:
            db = self._ensure_connection()
            # SQLite will handle cascade deletion automatically
            await db.execute("DELETE FROM documents WHERE id = ?", (str(document_id),))
            await db.commit()
        except Exception as e:
            raise StorageError(f"Failed to delete document: {document_id}", e)

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "updated_at",
    ) -> List[Document]:
        """List documents with pagination."""
        try:
            db = self._ensure_connection()

            # Validate order_by to prevent SQL injection
            valid_order_fields = ["updated_at", "created_at", "file_name", "file_size", "version_count"]
            if order_by not in valid_order_fields:
                order_by = "updated_at"

            query = f"SELECT * FROM documents ORDER BY {order_by} DESC LIMIT ? OFFSET ?"

            async with db.execute(query, (limit, offset)) as cursor:
                rows = await cursor.fetchall()

            return [self._row_to_document(row) for row in rows]
        except Exception as e:
            raise StorageError("Failed to list documents", e)

    async def search_documents(
        self,
        metadata_filter: Optional[dict] = None,
        file_type: Optional[str] = None,
    ) -> List[Document]:
        """Search documents by metadata or file type."""
        try:
            db = self._ensure_connection()

            query = "SELECT * FROM documents WHERE 1=1"
            params = []

            if file_type:
                query += " AND file_type = ?"
                params.append(file_type)

            # Use JSON1 extension for efficient metadata filtering
            if metadata_filter:
                for key, value in metadata_filter.items():
                    # Use json_extract for efficient JSON querying
                    query += " AND json_extract(metadata, ?) = ?"
                    params.append(f"$.{key}")
                    # Convert value to JSON format for comparison
                    if isinstance(value, str):
                        params.append(json.dumps(value))
                    else:
                        params.append(json.dumps(value).strip('"'))

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

            return [self._row_to_document(row) for row in rows]
        except Exception as e:
            # Fall back to client-side filtering if JSON1 extension not available
            try:
                query = "SELECT * FROM documents WHERE 1=1"
                params = []

                if file_type:
                    query += " AND file_type = ?"
                    params.append(file_type)

                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()

                documents = [self._row_to_document(row) for row in rows]

                # Filter by metadata if provided (client-side filtering fallback)
                if metadata_filter:
                    filtered_docs = []
                    for doc in documents:
                        matches = all(
                            doc.metadata.get(k) == v for k, v in metadata_filter.items()
                        )
                        if matches:
                            filtered_docs.append(doc)
                    return filtered_docs

                return documents
            except Exception:
                raise StorageError("Failed to search documents", e)

    # Version operations

    async def batch_create_versions(self, versions: List[Version]) -> List[Version]:
        """Create multiple version records in a single transaction (optimized)."""
        if not versions:
            return []

        try:
            db = self._ensure_connection()

            # Prepare batch data
            batch_data = [
                (
                    str(ver.id),
                    str(ver.document_id),
                    ver.version_number,
                    ver.content_hash,
                    ver.file_size,
                    ver.change_type.value,
                    ver.created_at.isoformat(),
                    ver.created_by,
                    json.dumps(ver.metadata),
                )
                for ver in versions
            ]

            # Execute batch insert in single transaction
            await db.executemany(
                """
                INSERT INTO versions (
                    id, document_id, version_number, content_hash, file_size,
                    change_type, created_at, created_by, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                batch_data,
            )

            # Handle content storage for versions with content
            content_batch = []
            for ver in versions:
                if ver.content:
                    # Compress content if enabled
                    content_data = ver.content.encode("utf-8")
                    if self.content_compression:
                        content_data = gzip.compress(content_data)

                    from uuid import uuid4
                    snapshot_id = str(uuid4())

                    content_batch.append(
                        (
                            snapshot_id,
                            str(ver.id),
                            content_data,
                            1 if self.content_compression else 0,
                            datetime.utcnow().isoformat(),
                        )
                    )

            # Batch insert content if any
            if content_batch:
                await db.executemany(
                    """
                    INSERT INTO content_snapshots (
                        id, version_id, content, compressed, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    content_batch,
                )

            await db.commit()
            return versions
        except Exception as e:
            raise StorageError(f"Failed to batch create {len(versions)} versions", e)

    async def create_version(self, version: Version) -> Version:
        """Create a new version record."""
        try:
            db = self._ensure_connection()
            await db.execute(
                """
                INSERT INTO versions (
                    id, document_id, version_number, content_hash, file_size,
                    change_type, created_at, created_by, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(version.id),
                    str(version.document_id),
                    version.version_number,
                    version.content_hash,
                    version.file_size,
                    version.change_type.value,
                    version.created_at.isoformat(),
                    version.created_by,
                    json.dumps(version.metadata),
                ),
            )

            # Store content if provided
            if version.content:
                await self.store_content(
                    version.id, version.content, compress=self.content_compression
                )

            await db.commit()
            return version
        except Exception as e:
            raise StorageError(f"Failed to create version for document {version.document_id}", e)

    async def get_version(self, version_id: UUID) -> Optional[Version]:
        """Get a version by ID."""
        try:
            db = self._ensure_connection()
            async with db.execute(
                "SELECT * FROM versions WHERE id = ?", (str(version_id),)
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            return self._row_to_version(row)
        except Exception as e:
            raise StorageError(f"Failed to get version: {version_id}", e)

    async def get_version_by_number(
        self, document_id: UUID, version_number: int
    ) -> Optional[Version]:
        """Get a specific version of a document."""
        try:
            db = self._ensure_connection()
            async with db.execute(
                "SELECT * FROM versions WHERE document_id = ? AND version_number = ?",
                (str(document_id), version_number),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            return self._row_to_version(row)
        except Exception as e:
            raise StorageError(
                f"Failed to get version {version_number} for document {document_id}", e
            )

    async def list_versions(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Version]:
        """List all versions of a document."""
        try:
            db = self._ensure_connection()
            async with db.execute(
                """
                SELECT * FROM versions
                WHERE document_id = ?
                ORDER BY version_number DESC
                LIMIT ? OFFSET ?
                """,
                (str(document_id), limit, offset),
            ) as cursor:
                rows = await cursor.fetchall()

            return [self._row_to_version(row) for row in rows]
        except Exception as e:
            raise StorageError(f"Failed to list versions for document {document_id}", e)

    async def delete_version(self, version_id: UUID) -> None:
        """Delete a specific version (cascade will delete content)."""
        try:
            db = self._ensure_connection()
            await db.execute("DELETE FROM versions WHERE id = ?", (str(version_id),))
            await db.commit()
        except Exception as e:
            raise StorageError(f"Failed to delete version: {version_id}", e)

    async def get_latest_version(self, document_id: UUID) -> Optional[Version]:
        """Get the latest version of a document."""
        try:
            db = self._ensure_connection()
            async with db.execute(
                """
                SELECT * FROM versions
                WHERE document_id = ?
                ORDER BY version_number DESC
                LIMIT 1
                """,
                (str(document_id),),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            return self._row_to_version(row)
        except Exception as e:
            raise StorageError(f"Failed to get latest version for document {document_id}", e)

    # Content operations

    async def store_content(
        self,
        version_id: UUID,
        content: str,
        compress: bool = True,
    ) -> None:
        """Store version content (optionally compressed)."""
        try:
            db = self._ensure_connection()

            # Compress content if enabled
            content_data = content.encode("utf-8")
            if compress:
                content_data = gzip.compress(content_data)

            # Generate UUID for content snapshot
            from uuid import uuid4
            snapshot_id = str(uuid4())

            await db.execute(
                """
                INSERT OR REPLACE INTO content_snapshots (
                    id, version_id, content, compressed, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    str(version_id),
                    content_data,
                    1 if compress else 0,
                    datetime.utcnow().isoformat(),
                ),
            )
            await db.commit()
        except Exception as e:
            raise StorageError(f"Failed to store content for version {version_id}", e)

    async def get_content(self, version_id: UUID) -> Optional[str]:
        """Retrieve version content (automatically decompressed)."""
        try:
            db = self._ensure_connection()
            async with db.execute(
                "SELECT content, compressed FROM content_snapshots WHERE version_id = ?",
                (str(version_id),),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            content_data = row[0]
            compressed = bool(row[1])

            # Decompress if needed
            if compressed:
                content_data = gzip.decompress(content_data)

            return content_data.decode("utf-8")
        except Exception as e:
            raise StorageError(f"Failed to get content for version {version_id}", e)

    async def delete_content(self, version_id: UUID) -> None:
        """Delete stored content for a version."""
        try:
            db = self._ensure_connection()
            await db.execute(
                "DELETE FROM content_snapshots WHERE version_id = ?", (str(version_id),)
            )
            await db.commit()
        except Exception as e:
            raise StorageError(f"Failed to delete content for version {version_id}", e)

    # Chunk operations (v0.10.0 - Chunk-level versioning)

    async def create_chunks_batch(self, chunks: List[Chunk]) -> List[Chunk]:
        """Create multiple chunks in a single transaction (optimized)."""
        if not chunks:
            return []

        try:
            db = self._ensure_connection()

            # Prepare batch data for chunks
            chunk_batch = [
                (
                    str(chunk.id),
                    str(chunk.document_id),
                    str(chunk.version_id),
                    chunk.chunk_index,
                    chunk.content_hash,
                    chunk.token_count,
                    chunk.created_at.isoformat(),
                    json.dumps(chunk.metadata),
                )
                for chunk in chunks
            ]

            # Batch insert chunks
            await db.executemany(
                """INSERT INTO chunks (id, document_id, version_id, chunk_index,
                   content_hash, token_count, created_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                chunk_batch,
            )

            # Batch store chunk content (if present in metadata)
            content_batch = []
            for chunk in chunks:
                if "content" in chunk.metadata:
                    text = chunk.metadata["content"]
                    data = text.encode("utf-8")
                    if self.content_compression:
                        data = gzip.compress(data)
                    content_batch.append(
                        (
                            str(chunk.id),
                            data,
                            1 if self.content_compression else 0,
                            datetime.utcnow().isoformat(),
                        )
                    )

            if content_batch:
                await db.executemany(
                    "INSERT INTO chunk_content (chunk_id, content, compressed, created_at) VALUES (?, ?, ?, ?)",
                    content_batch,
                )

            await db.commit()
            return chunks
        except Exception as e:
            raise StorageError(f"Failed to batch create {len(chunks)} chunks", e)

    async def create_chunk(self, chunk: Chunk) -> Chunk:
        """Create a single chunk record."""
        try:
            db = self._ensure_connection()

            await db.execute(
                """INSERT INTO chunks (id, document_id, version_id, chunk_index,
                   content_hash, token_count, created_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(chunk.id),
                    str(chunk.document_id),
                    str(chunk.version_id),
                    chunk.chunk_index,
                    chunk.content_hash,
                    chunk.token_count,
                    chunk.created_at.isoformat(),
                    json.dumps(chunk.metadata),
                ),
            )

            # Store content if present
            if "content" in chunk.metadata:
                await self.store_chunk_content(
                    chunk.id, chunk.metadata["content"], self.content_compression
                )

            await db.commit()
            return chunk
        except Exception as e:
            raise StorageError(f"Failed to create chunk {chunk.id}", e)

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get a chunk by its ID."""
        try:
            db = self._ensure_connection()

            async with db.execute(
                """SELECT id, document_id, version_id, chunk_index, content_hash,
                   token_count, created_at, metadata
                   FROM chunks WHERE id = ?""",
                (str(chunk_id),),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            return Chunk(
                id=UUID(row[0]),
                document_id=UUID(row[1]),
                version_id=UUID(row[2]),
                chunk_index=row[3],
                content_hash=row[4],
                token_count=row[5],
                created_at=datetime.fromisoformat(row[6]),
                metadata=json.loads(row[7]) if row[7] else {},
            )
        except Exception as e:
            raise StorageError(f"Failed to get chunk {chunk_id}", e)

    async def get_chunks_by_version(self, version_id: UUID) -> List[Chunk]:
        """Get all chunks for a specific version, ordered by chunk_index."""
        try:
            db = self._ensure_connection()

            async with db.execute(
                """SELECT id, document_id, version_id, chunk_index, content_hash,
                   token_count, created_at, metadata
                   FROM chunks WHERE version_id = ?
                   ORDER BY chunk_index""",
                (str(version_id),),
            ) as cursor:
                rows = await cursor.fetchall()

            chunks = []
            for row in rows:
                chunk = Chunk(
                    id=UUID(row[0]),
                    document_id=UUID(row[1]),
                    version_id=UUID(row[2]),
                    chunk_index=row[3],
                    content_hash=row[4],
                    token_count=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    metadata=json.loads(row[7]) if row[7] else {},
                )
                chunks.append(chunk)

            return chunks
        except Exception as e:
            raise StorageError(f"Failed to get chunks for version {version_id}", e)

    async def store_chunk_content(
        self,
        chunk_id: UUID,
        content: str,
        compress: bool = True,
    ) -> None:
        """Store chunk content separately (optionally compressed)."""
        try:
            db = self._ensure_connection()

            # Prepare content
            content_data = content.encode("utf-8")
            if compress:
                content_data = gzip.compress(content_data)

            await db.execute(
                """INSERT OR REPLACE INTO chunk_content (chunk_id, content, compressed, created_at)
                   VALUES (?, ?, ?, ?)""",
                (
                    str(chunk_id),
                    content_data,
                    1 if compress else 0,
                    datetime.utcnow().isoformat(),
                ),
            )
            await db.commit()
        except Exception as e:
            raise StorageError(f"Failed to store content for chunk {chunk_id}", e)

    async def get_chunk_content(self, chunk_id: UUID) -> Optional[str]:
        """Retrieve chunk content (automatically decompressed)."""
        try:
            db = self._ensure_connection()

            async with db.execute(
                "SELECT content, compressed FROM chunk_content WHERE chunk_id = ?",
                (str(chunk_id),),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            content_data = row[0]
            compressed = bool(row[1])

            # Decompress if needed
            if compressed:
                content_data = gzip.decompress(content_data)

            return content_data.decode("utf-8")
        except Exception as e:
            raise StorageError(f"Failed to get content for chunk {chunk_id}", e)

    async def delete_chunks_by_version(self, version_id: UUID) -> int:
        """Delete all chunks associated with a version."""
        try:
            db = self._ensure_connection()

            # Get count before deletion
            async with db.execute(
                "SELECT COUNT(*) FROM chunks WHERE version_id = ?", (str(version_id),)
            ) as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0

            # Delete chunks (cascade will delete chunk_content)
            await db.execute("DELETE FROM chunks WHERE version_id = ?", (str(version_id),))
            await db.commit()

            return count
        except Exception as e:
            raise StorageError(f"Failed to delete chunks for version {version_id}", e)

    # Diff operations

    async def compute_diff(
        self,
        document_id: UUID,
        from_version: int,
        to_version: int,
    ) -> Optional[DiffResult]:
        """Compute diff between two versions."""
        try:
            # Get both versions
            from_ver = await self.get_version_by_number(document_id, from_version)
            to_ver = await self.get_version_by_number(document_id, to_version)

            if not from_ver or not to_ver:
                return None

            # Get content for both versions
            from_content = await self.get_content(from_ver.id)
            to_content = await self.get_content(to_ver.id)

            if not from_content or not to_content:
                return None

            # Compute diff using difflib
            import difflib

            from_lines = from_content.splitlines()
            to_lines = to_content.splitlines()

            diff = difflib.unified_diff(from_lines, to_lines, lineterm="")
            diff_text = "\n".join(diff)

            # Count additions and deletions
            additions = sum(1 for line in diff_text.split("\n") if line.startswith("+") and not line.startswith("+++"))
            deletions = sum(1 for line in diff_text.split("\n") if line.startswith("-") and not line.startswith("---"))

            return DiffResult(
                document_id=document_id,
                from_version=from_version,
                to_version=to_version,
                diff_text=diff_text,
                additions=additions,
                deletions=deletions,
                from_hash=from_ver.content_hash,
                to_hash=to_ver.content_hash,
            )
        except Exception as e:
            raise StorageError(
                f"Failed to compute diff for document {document_id} versions {from_version} to {to_version}",
                e,
            )

    # Cleanup operations

    async def cleanup_old_versions(
        self,
        document_id: UUID,
        keep_count: int = 10,
    ) -> int:
        """Delete old versions, keeping only the most recent ones."""
        try:
            # Get all versions
            versions = await self.list_versions(document_id, limit=10000)

            if len(versions) <= keep_count:
                return 0

            # Delete oldest versions
            versions_to_delete = versions[keep_count:]
            for version in versions_to_delete:
                await self.delete_version(version.id)

            return len(versions_to_delete)
        except Exception as e:
            raise StorageError(
                f"Failed to cleanup old versions for document {document_id}", e
            )

    async def cleanup_by_age(self, days: int) -> int:
        """Delete versions older than specified days."""
        try:
            db = self._ensure_connection()
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get old version IDs
            async with db.execute(
                "SELECT id FROM versions WHERE created_at < ?",
                (cutoff_date.isoformat(),),
            ) as cursor:
                rows = await cursor.fetchall()

            count = 0
            for row in rows:
                version_id = UUID(row[0])
                await self.delete_version(version_id)
                count += 1

            return count
        except Exception as e:
            raise StorageError(f"Failed to cleanup versions older than {days} days", e)

    # Statistics operations

    async def get_statistics(self) -> StorageStatistics:
        """Get overall storage statistics."""
        try:
            db = self._ensure_connection()

            # Count total documents
            async with db.execute("SELECT COUNT(*) FROM documents") as cursor:
                row = await cursor.fetchone()
                total_documents = row[0]

            # Count total versions
            async with db.execute("SELECT COUNT(*) FROM versions") as cursor:
                row = await cursor.fetchone()
                total_versions = row[0]

            # Calculate average versions per document
            average_versions_per_document = (
                total_versions / total_documents if total_documents > 0 else 0.0
            )

            # Get total storage (sum of file sizes)
            async with db.execute("SELECT SUM(file_size) FROM documents") as cursor:
                row = await cursor.fetchone()
                total_storage_bytes = row[0] or 0

            # Get documents by file type
            documents_by_file_type: dict = {}
            async with db.execute("SELECT file_type, COUNT(*) FROM documents GROUP BY file_type") as cursor:
                async for row in cursor:
                    documents_by_file_type[row[0]] = row[1]

            # Get recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            async with db.execute(
                "SELECT COUNT(*) FROM versions WHERE created_at >= ?",
                (seven_days_ago.isoformat(),),
            ) as cursor:
                row = await cursor.fetchone()
                recent_activity_count = row[0]

            # Get oldest and newest document dates
            async with db.execute("SELECT MIN(created_at), MAX(created_at) FROM documents") as cursor:
                row = await cursor.fetchone()
                oldest_document_date = datetime.fromisoformat(row[0]) if row[0] else None
                newest_document_date = datetime.fromisoformat(row[1]) if row[1] else None

            return StorageStatistics(
                total_documents=total_documents,
                total_versions=total_versions,
                total_storage_bytes=total_storage_bytes,
                average_versions_per_document=average_versions_per_document,
                documents_by_file_type=documents_by_file_type,
                recent_activity_count=recent_activity_count,
                oldest_document_date=oldest_document_date,
                newest_document_date=newest_document_date,
            )
        except Exception as e:
            raise StorageError("Failed to get storage statistics", e)

    async def get_document_statistics(self, document_id: UUID) -> DocumentStatistics:
        """Get statistics for a specific document."""
        try:
            # Get document
            document = await self.get_document(document_id)
            if not document:
                raise DocumentNotFoundError(str(document_id))

            # Get all versions for this document
            versions = await self.list_versions(document_id, limit=10000)
            total_versions = len(versions)

            # Count versions by change type
            versions_by_change_type: dict = {}
            for version in versions:
                change_type = version.change_type.value
                versions_by_change_type[change_type] = (
                    versions_by_change_type.get(change_type, 0) + 1
                )

            # Calculate average days between changes
            average_days_between_changes = 0.0
            if total_versions > 1:
                time_diff = document.updated_at - document.created_at
                days_diff = time_diff.total_seconds() / 86400
                average_days_between_changes = days_diff / (total_versions - 1)

            # Determine change frequency
            if average_days_between_changes < 1:
                change_frequency = "high"
            elif average_days_between_changes < 7:
                change_frequency = "medium"
            else:
                change_frequency = "low"

            return DocumentStatistics(
                document_id=document.id,
                file_name=document.file_name,
                file_path=document.file_path,
                total_versions=total_versions,
                versions_by_change_type=versions_by_change_type,
                total_size_bytes=document.file_size,
                first_tracked=document.created_at,
                last_updated=document.updated_at,
                average_days_between_changes=average_days_between_changes,
                change_frequency=change_frequency,
            )
        except DocumentNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get document statistics for {document_id}", e)

    async def get_top_documents(
        self,
        limit: int = 10,
        order_by: str = "version_count",
    ) -> List[Document]:
        """Get top documents by version count or other criteria."""
        try:
            db = self._ensure_connection()

            # Validate order_by parameter
            valid_order_fields = ["version_count", "updated_at", "file_size"]
            if order_by not in valid_order_fields:
                order_by = "version_count"

            query = f"SELECT * FROM documents ORDER BY {order_by} DESC LIMIT ?"

            async with db.execute(query, (limit,)) as cursor:
                rows = await cursor.fetchall()

            return [self._row_to_document(row) for row in rows]
        except Exception as e:
            raise StorageError(f"Failed to get top documents by {order_by}", e)

    # Helper methods

    def _row_to_document(self, row: tuple) -> Document:
        """Convert database row to Document model."""
        return Document(
            id=UUID(row[0]),
            file_path=row[1],
            file_name=row[2],
            file_type=row[3],
            file_size=row[4],
            content_hash=row[5],
            created_at=datetime.fromisoformat(row[6]),
            updated_at=datetime.fromisoformat(row[7]),
            version_count=row[8],
            current_version=row[9],
            metadata=json.loads(row[10]) if row[10] else {},
        )

    def _row_to_version(self, row: tuple) -> Version:
        """Convert database row to Version model."""
        return Version(
            id=UUID(row[0]),
            document_id=UUID(row[1]),
            version_number=row[2],
            content_hash=row[3],
            file_size=row[4],
            change_type=ChangeType(row[5]),
            created_at=datetime.fromisoformat(row[6]),
            created_by=row[7],
            metadata=json.loads(row[8]) if row[8] else {},
        )

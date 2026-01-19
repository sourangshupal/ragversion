# RAGVersion: File Versioning System for RAG Pipelines

## Implementation Plan Document

**Version:** 1.0  
**Date:** January 2025  
**Author:** Paul (KrishAI Technologies)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Solution Overview](#solution-overview)
4. [Architecture](#architecture)
5. [Package Structure](#package-structure)
6. [Core Components](#core-components)
7. [Data Models](#data-models)
8. [Database Schema](#database-schema)
9. [Public API Design](#public-api-design)
10. [Framework Integrations](#framework-integrations)
11. [CLI Interface](#cli-interface)
12. [Configuration](#configuration)
13. [Development Roadmap](#development-roadmap)
14. [Dependencies](#dependencies)
15. [Testing Strategy](#testing-strategy)
16. [Future Enhancements](#future-enhancements)

---

## Executive Summary

**RAGVersion** is a framework-agnostic document version control system designed specifically for RAG (Retrieval-Augmented Generation) pipelines. It tracks document changes across multiple file formats, maintains version history, and provides hooks for RAG systems to react to changes — without handling chunking, embedding, or vector storage internally.

**Package Name:** `ragversion`  
**Tagline:** *"Track, diff, and sync document changes across any RAG system"*

---

## Problem Statement

In production RAG systems, documents frequently get updated — a PDF might have new sections added, a Word document might be revised, or configuration files might change. Current challenges include:

1. **No change detection** — Re-indexing entire documents wastes compute resources
2. **No version history** — Cannot track what changed or when
3. **No rollback capability** — Cannot revert to previous document states
4. **Tight coupling** — Versioning logic is often embedded in specific RAG frameworks
5. **Format fragmentation** — Different file types require different handling approaches

---

## Solution Overview

### What RAGVersion Does

| Capability | Description |
|------------|-------------|
| **Track Documents** | Monitor files for changes across multiple formats |
| **Detect Changes** | Identify when documents are added, modified, or deleted |
| **Store Versions** | Maintain complete version history in a database |
| **Provide Diffs** | Show exactly what changed between versions |
| **Emit Events** | Notify RAG pipelines when changes occur |
| **Extract Content** | Parse various file formats to plain text |

### What RAGVersion Does NOT Do

| Out of Scope | Rationale |
|--------------|-----------|
| **Chunking** | Handled by your RAG framework (LangChain, LlamaIndex, etc.) |
| **Embedding Generation** | Handled by your embedding provider |
| **Vector Storage** | Handled by your vector database |
| **Retrieval** | Handled by your RAG pipeline |

This separation of concerns ensures RAGVersion integrates cleanly with any existing RAG architecture.

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Your RAG Pipeline                          │
│              (LangChain / LlamaIndex / Custom)                  │
│                                                                  │
│   ┌───────────┐    ┌───────────┐    ┌───────────────────┐      │
│   │  Chunker  │───▶│ Embedder  │───▶│    Vector DB      │      │
│   └───────────┘    └───────────┘    └───────────────────┘      │
│         ▲                                                        │
│         │ Content + Change Events                               │
└─────────┼───────────────────────────────────────────────────────┘
          │
┌─────────┴───────────────────────────────────────────────────────┐
│                    RAGVersion Package                            │
│                                                                  │
│   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐ │
│   │  File Parsers  │──▶│ Change Detector│──▶│    Storage     │ │
│   │ (PDF,DOCX,etc) │   │    Engine      │   │  (Supabase)    │ │
│   └────────────────┘   └────────────────┘   └────────────────┘ │
│                                                                  │
│   Outputs:                                                       │
│   • Change events (added / modified / deleted)                  │
│   • Extracted document content                                   │
│   • Version metadata                                             │
│   • Diff between versions                                        │
└──────────────────────────────────────────────────────────────────┘
```

### Change Detection Flow

```
                    File Input
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Step 1: Metadata Hash Check  │  ◀── Fast path
        │  (file size + modified time)  │      (Quick rejection for unchanged)
        └───────────────────────────────┘
                        │
                   Changed?
                   │      │
                  No     Yes
                   │      │
                   ▼      ▼
              Return   ┌───────────────────────────────┐
              None     │  Step 2: Content Hash Check   │  ◀── Confirms actual change
                       │  (SHA-256 of full content)    │
                       └───────────────────────────────┘
                                    │
                               Changed?
                               │      │
                              No     Yes
                               │      │
                               ▼      ▼
                          Return   ┌───────────────────────────────┐
                          None     │  Step 3: Parse & Extract      │
                                   │  (Extract text from file)     │
                                   └───────────────────────────────┘
                                                │
                                                ▼
                                   ┌───────────────────────────────┐
                                   │  Step 4: Create Version       │
                                   │  (Store in database)          │
                                   └───────────────────────────────┘
                                                │
                                                ▼
                                   ┌───────────────────────────────┐
                                   │  Step 5: Emit Change Event    │
                                   │  (Notify callbacks)           │
                                   └───────────────────────────────┘
```

---

## Package Structure

```
ragversion/
│
├── core/
│   ├── __init__.py
│   ├── tracker.py          # Main VersionTracker class
│   ├── detector.py         # Change detection engine
│   ├── hasher.py           # File and content hashing utilities
│   ├── models.py           # Pydantic data models
│   ├── events.py           # Event system for change notifications
│   └── exceptions.py       # Custom exceptions
│
├── storage/
│   ├── __init__.py
│   ├── base.py             # Abstract storage backend interface
│   ├── supabase.py         # Supabase (PostgreSQL) implementation
│   ├── sqlite.py           # Local SQLite for development/testing
│   └── postgres.py         # Direct PostgreSQL connection
│
├── parsers/
│   ├── __init__.py
│   ├── base.py             # Abstract parser interface
│   ├── registry.py         # Parser registration and lookup system
│   ├── pdf.py              # PDF text extraction
│   ├── docx.py             # Word document extraction
│   ├── txt.py              # Plain text files
│   ├── markdown.py         # Markdown files
│   ├── html.py             # HTML pages
│   ├── pptx.py             # PowerPoint presentations
│   ├── xlsx.py             # Excel spreadsheets
│   ├── csv_parser.py       # CSV files
│   ├── json_parser.py      # JSON documents
│   └── code.py             # Source code files
│
├── integrations/
│   ├── __init__.py
│   ├── base.py             # Base integration helpers
│   ├── langchain.py        # LangChain integration utilities
│   └── llamaindex.py       # LlamaIndex integration utilities
│
├── cli/
│   ├── __init__.py
│   ├── main.py             # CLI entry point (Click)
│   └── commands/
│       ├── __init__.py
│       ├── init.py         # Initialize configuration
│       ├── track.py        # Track files/directories
│       ├── status.py       # Show tracking status
│       ├── history.py      # View version history
│       ├── diff.py         # Compare versions
│       └── untrack.py      # Stop tracking documents
│
├── utils/
│   ├── __init__.py
│   ├── logging.py          # Logging configuration
│   ├── config.py           # Configuration loader
│   └── helpers.py          # Miscellaneous utilities
│
├── __init__.py             # Public API exports
├── config.py               # Default configuration values
└── py.typed                # PEP 561 type marker
```

---

## Core Components

### 1. Storage Backend Interface

The storage layer is abstracted to support multiple backends.

```
StorageBackend (Abstract Base Class)
│
├── Connection Management
│   ├── connect() → None
│   ├── disconnect() → None
│   └── is_connected() → bool
│
├── Document Operations
│   ├── create_document(doc: Document) → Document
│   ├── get_document(document_id: UUID) → Optional[Document]
│   ├── get_document_by_path(file_path: str) → Optional[Document]
│   ├── update_document(doc: Document) → Document
│   ├── delete_document(document_id: UUID, hard: bool) → bool
│   └── list_documents(filters: Dict) → List[Document]
│
├── Version Operations
│   ├── create_version(version: Version) → Version
│   ├── get_version(document_id: UUID, version_number: int) → Optional[Version]
│   ├── get_latest_version(document_id: UUID) → Optional[Version]
│   ├── get_version_history(document_id: UUID) → List[Version]
│   └── get_version_count(document_id: UUID) → int
│
├── Content Operations (Optional)
│   ├── store_content(document_id: UUID, version: int, content: str) → bool
│   ├── get_content(document_id: UUID, version: int) → Optional[str]
│   └── delete_content(document_id: UUID, version: int) → bool
│
└── Implementations
    ├── SupabaseStorage
    ├── SQLiteStorage
    └── PostgresStorage
```

### 2. Parser Interface

Each parser extracts text content from a specific file format.

```
DocumentParser (Abstract Base Class)
│
├── Properties
│   ├── supported_extensions: List[str]    # e.g., [".pdf", ".PDF"]
│   ├── parser_name: str                   # e.g., "PDFParser"
│   └── requires_binary: bool              # True if needs raw bytes
│
├── Methods
│   ├── parse(file_path: Path) → ParsedDocument
│   ├── parse_bytes(content: bytes, filename: str) → ParsedDocument
│   ├── can_parse(file_path: Path) → bool
│   └── extract_metadata(file_path: Path) → Dict[str, Any]
│
└── ParsedDocument (Output)
    ├── content: str                       # Extracted text
    ├── metadata: Dict[str, Any]           # File metadata
    ├── page_count: Optional[int]          # For paginated docs
    ├── word_count: int                    # Content statistics
    └── extraction_method: str             # Parser used
```

### 3. Parser Registry

Dynamic registration system for file parsers.

```
ParserRegistry
│
├── Built-in Parsers
│   ├── .pdf      → PDFParser
│   ├── .docx     → DocxParser
│   ├── .doc      → LegacyDocParser
│   ├── .txt      → TextParser
│   ├── .md       → MarkdownParser
│   ├── .html     → HTMLParser
│   ├── .htm      → HTMLParser
│   ├── .csv      → CSVParser
│   ├── .xlsx     → ExcelParser
│   ├── .xls      → LegacyExcelParser
│   ├── .pptx     → PowerPointParser
│   ├── .json     → JSONParser
│   ├── .xml      → XMLParser
│   ├── .py       → CodeParser
│   ├── .js       → CodeParser
│   ├── .ts       → CodeParser
│   ├── .java     → CodeParser
│   ├── .cpp      → CodeParser
│   ├── .c        → CodeParser
│   ├── .go       → CodeParser
│   └── .rs       → CodeParser
│
├── Methods
│   ├── register(extensions: List[str], parser: Type[DocumentParser])
│   ├── unregister(extension: str)
│   ├── get_parser(extension: str) → Optional[DocumentParser]
│   ├── get_parser_for_file(file_path: Path) → Optional[DocumentParser]
│   ├── list_supported_extensions() → List[str]
│   └── is_supported(file_path: Path) → bool
│
└── Custom Registration
    @registry.register([".custom", ".xyz"])
    class CustomParser(DocumentParser):
        ...
```

### 4. Event System

Callback-based notification system for changes.

```
EventEmitter
│
├── Event Types
│   ├── on_change     → Any change (add, modify, delete)
│   ├── on_add        → New document tracked
│   ├── on_modify     → Existing document modified
│   └── on_delete     → Document deleted/removed
│
├── Methods
│   ├── subscribe(event_type: str, callback: Callable)
│   ├── unsubscribe(event_type: str, callback: Callable)
│   ├── emit(event_type: str, event: ChangeEvent)
│   └── clear_all()
│
└── Callback Signature
    def callback(event: ChangeEvent) → None:
        ...
```

---

## Data Models

### Document

Represents a tracked document in the system.

```
Document
├── id: UUID                    # Unique identifier
├── file_path: str              # Absolute or relative path
├── file_name: str              # File name with extension
├── file_type: str              # Extension (e.g., ".pdf")
├── current_version: int        # Latest version number
├── content_hash: str           # SHA-256 of extracted text
├── file_hash: str              # SHA-256 of raw file bytes
├── file_size_bytes: int        # File size
├── is_deleted: bool            # Soft delete flag
├── created_at: datetime        # First tracked timestamp
├── updated_at: datetime        # Last change timestamp
└── metadata: Dict[str, Any]    # Extensible metadata
```

### Version

Represents a specific version of a document.

```
Version
├── id: UUID                    # Unique identifier
├── document_id: UUID           # Parent document reference
├── version_number: int         # Sequential version number
├── content_hash: str           # SHA-256 of content at this version
├── file_hash: str              # SHA-256 of file at this version
├── file_size_bytes: int        # File size at this version
├── change_type: ChangeType     # created | modified | restored
├── created_at: datetime        # Version creation timestamp
└── metadata: Dict[str, Any]    # Version-specific metadata
```

### ChangeEvent

Emitted when a document changes.

```
ChangeEvent
├── document_id: UUID           # Document that changed
├── file_path: str              # File path
├── file_name: str              # File name
├── change_type: ChangeType     # added | modified | deleted
├── old_version: Optional[int]  # Previous version (if applicable)
├── new_version: int            # New version number
├── content: str                # Extracted text content
├── old_content: Optional[str]  # Previous content (for diff)
├── old_content_hash: Optional[str]
├── new_content_hash: str
├── timestamp: datetime         # When change was detected
└── metadata: Dict[str, Any]    # Additional context
```

### ContentDiff

Result of comparing two versions.

```
ContentDiff
├── document_id: UUID           # Document being compared
├── version_from: int           # Starting version
├── version_to: int             # Ending version
├── added_lines: List[str]      # Lines added
├── removed_lines: List[str]    # Lines removed
├── modified_lines: int         # Count of changed lines
├── diff_text: str              # Unified diff format
├── similarity_score: float     # 0.0 to 1.0
└── change_summary: str         # Human-readable summary
```

### Enums

```
ChangeType (Enum)
├── ADDED       # New document
├── MODIFIED    # Existing document changed
├── DELETED     # Document removed
└── RESTORED    # Document restored from deletion

StorageBackendType (Enum)
├── SUPABASE
├── SQLITE
└── POSTGRES
```

---

## Database Schema

### Supabase / PostgreSQL Schema

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- DOCUMENTS TABLE
-- Master record for each tracked document
-- ============================================
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    current_version INTEGER NOT NULL DEFAULT 1,
    content_hash TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for documents
CREATE INDEX idx_documents_file_path ON documents(file_path);
CREATE INDEX idx_documents_file_type ON documents(file_type);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);
CREATE INDEX idx_documents_is_deleted ON documents(is_deleted);
CREATE INDEX idx_documents_updated_at ON documents(updated_at DESC);

-- ============================================
-- VERSIONS TABLE
-- Historical record of each document version
-- ============================================
CREATE TABLE versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    change_type TEXT NOT NULL CHECK (change_type IN ('created', 'modified', 'restored')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    UNIQUE(document_id, version_number)
);

-- Indexes for versions
CREATE INDEX idx_versions_document_id ON versions(document_id);
CREATE INDEX idx_versions_created_at ON versions(created_at DESC);
CREATE INDEX idx_versions_content_hash ON versions(content_hash);

-- ============================================
-- CONTENT_SNAPSHOTS TABLE (Optional)
-- Stores full content for diffing capability
-- ============================================
CREATE TABLE content_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_length INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(document_id, version_number)
);

-- Indexes for content_snapshots
CREATE INDEX idx_content_snapshots_document ON content_snapshots(document_id);

-- ============================================
-- TRIGGERS
-- Auto-update timestamps
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================
-- VIEWS
-- Useful aggregations
-- ============================================
CREATE VIEW document_stats AS
SELECT 
    d.id,
    d.file_path,
    d.file_name,
    d.file_type,
    d.current_version,
    d.is_deleted,
    d.created_at,
    d.updated_at,
    COUNT(v.id) as total_versions,
    MAX(v.created_at) as last_version_at
FROM documents d
LEFT JOIN versions v ON d.id = v.document_id
GROUP BY d.id;

-- ============================================
-- ROW LEVEL SECURITY (Optional - Multi-tenant)
-- ============================================
-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE versions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE content_snapshots ENABLE ROW LEVEL SECURITY;
```

---

## Public API Design

### Main Entry Point: VersionTracker

```
VersionTracker
│
├── Initialization
│   ├── __init__(storage: StorageBackend, parsers: Optional[ParserRegistry])
│   ├── from_config(config_path: str) → VersionTracker
│   ├── from_env() → VersionTracker
│   └── from_dict(config: Dict) → VersionTracker
│
├── Core Tracking Methods
│   ├── track(file_path: str) → Optional[ChangeEvent]
│   │   └── Track a single file, returns ChangeEvent if changed
│   │
│   ├── track_directory(
│   │       dir_path: str,
│   │       patterns: List[str] = ["*"],
│   │       recursive: bool = True
│   │   ) → List[ChangeEvent]
│   │   └── Track all matching files in directory
│   │
│   ├── untrack(document_id: UUID) → bool
│   │   └── Stop tracking a document (soft delete)
│   │
│   └── is_tracked(file_path: str) → bool
│       └── Check if file is being tracked
│
├── Change Detection Methods
│   ├── has_changed(file_path: str) → bool
│   │   └── Quick check if file has changed
│   │
│   ├── get_changes(file_path: str) → Optional[ChangeEvent]
│   │   └── Get change details without updating
│   │
│   └── scan_for_changes(
│           dir_path: str,
│           patterns: List[str] = ["*"]
│       ) → List[ChangeEvent]
│       └── Scan directory for all changes
│
├── Document Access Methods
│   ├── get_document(document_id: UUID) → Optional[Document]
│   │
│   ├── get_document_by_path(file_path: str) → Optional[Document]
│   │
│   ├── get_content(
│   │       document_id: UUID,
│   │       version: Optional[int] = None
│   │   ) → Optional[str]
│   │   └── Get content at specific version (None = latest)
│   │
│   ├── list_documents(
│   │       file_type: Optional[str] = None,
│   │       include_deleted: bool = False
│   │   ) → List[Document]
│   │
│   └── search_documents(query: str) → List[Document]
│       └── Search by file name or path
│
├── Version History Methods
│   ├── get_history(
│   │       document_id: UUID,
│   │       limit: Optional[int] = None
│   │   ) → List[Version]
│   │
│   ├── get_version(
│   │       document_id: UUID,
│   │       version_number: int
│   │   ) → Optional[Version]
│   │
│   ├── get_diff(
│   │       document_id: UUID,
│   │       version_from: int,
│   │       version_to: int
│   │   ) → ContentDiff
│   │
│   └── restore_version(
│           document_id: UUID,
│           version_number: int
│       ) → ChangeEvent
│       └── Restore document to a previous version
│
├── Event/Callback Methods
│   ├── on_change(callback: Callable[[ChangeEvent], None])
│   │   └── Register callback for any change
│   │
│   ├── on_add(callback: Callable[[ChangeEvent], None])
│   │   └── Register callback for new documents
│   │
│   ├── on_modify(callback: Callable[[ChangeEvent], None])
│   │   └── Register callback for modifications
│   │
│   ├── on_delete(callback: Callable[[ChangeEvent], None])
│   │   └── Register callback for deletions
│   │
│   └── remove_callback(callback: Callable)
│       └── Unregister a callback
│
└── Utility Methods
    ├── get_stats() → TrackerStats
    │   └── Get tracking statistics
    │
    ├── get_supported_extensions() → List[str]
    │   └── List all supported file types
    │
    ├── register_parser(
    │       extensions: List[str],
    │       parser: Type[DocumentParser]
    │   ) → None
    │   └── Register custom parser
    │
    └── export_history(
            document_id: UUID,
            format: str = "json"
        ) → str
        └── Export version history
```

### Usage Examples

#### Basic Usage

```python
from ragversion import VersionTracker, SupabaseStorage

# Initialize tracker
tracker = VersionTracker(
    storage=SupabaseStorage(
        url="https://xxx.supabase.co",
        key="your-service-key"
    )
)

# Track a single file
change = tracker.track("documents/report.pdf")

if change:
    print(f"Change: {change.change_type}")
    print(f"Version: {change.new_version}")
    print(f"Content length: {len(change.content)}")
    
    # Pass to your RAG pipeline
    # your_pipeline.process(change.content)
else:
    print("No changes detected")
```

#### Directory Tracking

```python
# Track all PDFs and Word docs in a directory
changes = tracker.track_directory(
    dir_path="./documents",
    patterns=["*.pdf", "*.docx", "*.md"],
    recursive=True
)

print(f"Found {len(changes)} changes")
for change in changes:
    print(f"  {change.file_name}: {change.change_type}")
```

#### Event Callbacks

```python
def handle_document_change(event: ChangeEvent):
    """Process document changes for RAG pipeline."""
    
    if event.change_type == ChangeType.ADDED:
        # New document - full indexing
        print(f"New document: {event.file_name}")
        chunks = my_chunker.chunk(event.content)
        embeddings = my_embedder.embed(chunks)
        my_vectordb.insert(
            embeddings,
            metadata={"document_id": str(event.document_id)}
        )
        
    elif event.change_type == ChangeType.MODIFIED:
        # Modified - re-index
        print(f"Modified: {event.file_name}")
        my_vectordb.delete(document_id=str(event.document_id))
        chunks = my_chunker.chunk(event.content)
        embeddings = my_embedder.embed(chunks)
        my_vectordb.insert(
            embeddings,
            metadata={"document_id": str(event.document_id)}
        )
        
    elif event.change_type == ChangeType.DELETED:
        # Deleted - remove from index
        print(f"Deleted: {event.file_name}")
        my_vectordb.delete(document_id=str(event.document_id))

# Register callback
tracker.on_change(handle_document_change)

# Now tracking automatically triggers the callback
tracker.track_directory("./documents")
```

#### Version History and Diff

```python
# Get document history
doc = tracker.get_document_by_path("documents/report.pdf")
history = tracker.get_history(doc.id)

for version in history:
    print(f"v{version.version_number} - {version.created_at}")
    print(f"  Change type: {version.change_type}")
    print(f"  Size: {version.file_size_bytes} bytes")

# Compare two versions
diff = tracker.get_diff(doc.id, version_from=1, version_to=3)
print(f"\nChanges between v1 and v3:")
print(f"  Similarity: {diff.similarity_score:.1%}")
print(f"  Lines added: {len(diff.added_lines)}")
print(f"  Lines removed: {len(diff.removed_lines)}")
print(f"\nDiff:\n{diff.diff_text}")

# Get content at specific version
old_content = tracker.get_content(doc.id, version=1)
```

---

## Framework Integrations

### LangChain Integration

```python
from ragversion import VersionTracker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant

# Initialize components
tracker = VersionTracker.from_config("ragversion.yaml")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50
)
embeddings = OpenAIEmbeddings()
vectorstore = Qdrant(...)

def sync_to_vectorstore(event: ChangeEvent):
    """Sync document changes to LangChain vectorstore."""
    
    doc_filter = {"document_id": str(event.document_id)}
    
    if event.change_type == ChangeType.DELETED:
        # Remove all chunks for this document
        vectorstore.delete(filter=doc_filter)
        return
    
    # For add/modify, remove existing then re-index
    if event.change_type == ChangeType.MODIFIED:
        vectorstore.delete(filter=doc_filter)
    
    # Chunk the content
    chunks = splitter.split_text(event.content)
    
    # Create metadata for each chunk
    metadatas = [
        {
            "document_id": str(event.document_id),
            "file_path": event.file_path,
            "file_name": event.file_name,
            "version": event.new_version,
            "chunk_index": i
        }
        for i in range(len(chunks))
    ]
    
    # Add to vectorstore
    vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    print(f"Indexed {len(chunks)} chunks for {event.file_name}")

# Register and track
tracker.on_change(sync_to_vectorstore)
tracker.track_directory("./documents", patterns=["*.pdf", "*.docx"])
```

### LlamaIndex Integration

```python
from ragversion import VersionTracker, ChangeType
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter

# Initialize
tracker = VersionTracker.from_config("ragversion.yaml")
node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)

def sync_to_llamaindex(event: ChangeEvent):
    """Sync document changes to LlamaIndex."""
    
    if event.change_type == ChangeType.DELETED:
        # Handle deletion in your index
        index.delete_ref_doc(str(event.document_id))
        return
    
    # Create LlamaIndex Document
    doc = Document(
        text=event.content,
        doc_id=str(event.document_id),
        metadata={
            "file_path": event.file_path,
            "file_name": event.file_name,
            "version": event.new_version,
            "file_type": event.metadata.get("file_type", "unknown")
        }
    )
    
    if event.change_type == ChangeType.MODIFIED:
        # Update existing document
        index.update_ref_doc(doc)
    else:
        # Insert new document
        index.insert(doc)
    
    print(f"Synced {event.file_name} to LlamaIndex")

# Register and track
tracker.on_change(sync_to_llamaindex)
tracker.track_directory("./documents")
```

---

## CLI Interface

### Commands Overview

```
ragversion CLI
│
├── ragversion init
│   ├── --storage [supabase|sqlite|postgres]
│   ├── --output PATH (default: ragversion.yaml)
│   └── Initialize configuration file
│
├── ragversion track <path>
│   ├── --recursive / --no-recursive
│   ├── --pattern PATTERN (repeatable)
│   ├── --dry-run
│   └── Track file(s) and report changes
│
├── ragversion status [path]
│   ├── --all (include deleted)
│   └── Show tracking status
│
├── ragversion history <file_path>
│   ├── --limit N
│   ├── --format [table|json]
│   └── Show version history
│
├── ragversion diff <file_path> <v1> <v2>
│   ├── --format [unified|side-by-side]
│   └── Show diff between versions
│
├── ragversion list
│   ├── --type EXTENSION
│   ├── --all (include deleted)
│   ├── --format [table|json]
│   └── List all tracked documents
│
├── ragversion untrack <file_path>
│   ├── --hard (permanent delete)
│   └── Stop tracking a document
│
├── ragversion stats
│   └── Show overall statistics
│
└── ragversion export <file_path>
    ├── --format [json|csv]
    ├── --output PATH
    └── Export version history
```

### CLI Usage Examples

```bash
# Initialize configuration
ragversion init --storage supabase

# Track a single file
ragversion track documents/report.pdf

# Track directory with patterns
ragversion track ./documents --pattern "*.pdf" --pattern "*.docx" --recursive

# Dry run to see what would be tracked
ragversion track ./documents --pattern "*.pdf" --dry-run

# Check status
ragversion status documents/report.pdf

# View version history
ragversion history documents/report.pdf --limit 10

# Compare versions
ragversion diff documents/report.pdf 1 3

# List all tracked documents
ragversion list --format table

# List only PDFs
ragversion list --type .pdf

# Show statistics
ragversion stats

# Export history
ragversion export documents/report.pdf --format json --output history.json

# Untrack a document (soft delete)
ragversion untrack documents/old-report.pdf

# Permanently remove
ragversion untrack documents/old-report.pdf --hard
```

---

## Configuration

### Configuration File (ragversion.yaml)

```yaml
# ragversion.yaml

# ============================================
# Storage Backend Configuration
# ============================================
storage:
  # Backend type: supabase | sqlite | postgres
  backend: supabase
  
  # Supabase configuration
  supabase:
    url: ${SUPABASE_URL}           # Environment variable
    key: ${SUPABASE_SERVICE_KEY}   # Service role key
    
  # SQLite configuration (for local development)
  sqlite:
    path: ./ragversion.db
    
  # Direct PostgreSQL configuration
  postgres:
    host: ${POSTGRES_HOST}
    port: 5432
    database: ragversion
    user: ${POSTGRES_USER}
    password: ${POSTGRES_PASSWORD}
    ssl_mode: require

# ============================================
# Parsing Configuration
# ============================================
parsing:
  # PDF parsing backend: pymupdf | pdfplumber | pypdf
  pdf_backend: pymupdf
  
  # Extract tables from documents
  extract_tables: true
  
  # Extract images (as base64) - increases storage
  extract_images: false
  
  # OCR for scanned documents
  ocr_enabled: false
  ocr_language: eng
  
  # Code file settings
  code:
    include_comments: true
    max_file_size_kb: 500

# ============================================
# Tracking Configuration
# ============================================
tracking:
  # Store full content for diffing capability
  store_content: true
  
  # Maximum file size to process (MB)
  max_file_size_mb: 50
  
  # Hash algorithm: sha256 | sha1 | md5
  hash_algorithm: sha256
  
  # Default file patterns to track
  default_patterns:
    - "*.pdf"
    - "*.docx"
    - "*.doc"
    - "*.txt"
    - "*.md"
    - "*.html"
  
  # Patterns to ignore
  ignore_patterns:
    - ".*"           # Hidden files
    - "__pycache__"
    - "node_modules"
    - "*.tmp"
    - "~*"

# ============================================
# Versioning Configuration
# ============================================
versioning:
  # Keep all versions or limit
  max_versions: null  # null = unlimited, or integer
  
  # Auto-cleanup old versions after N days
  auto_cleanup_days: null  # null = never
  
  # Soft delete by default
  soft_delete: true

# ============================================
# Logging Configuration
# ============================================
logging:
  # Log level: DEBUG | INFO | WARNING | ERROR
  level: INFO
  
  # Log format: json | text
  format: text
  
  # Log file (optional)
  file: null  # e.g., ./ragversion.log
```

### Environment Variables

```bash
# Required for Supabase
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_SERVICE_KEY="eyJ..."

# Required for PostgreSQL
export POSTGRES_HOST="localhost"
export POSTGRES_USER="ragversion"
export POSTGRES_PASSWORD="secret"

# Optional
export RAGVERSION_CONFIG="./ragversion.yaml"
export RAGVERSION_LOG_LEVEL="DEBUG"
```

---

## Development Roadmap

### Phase 1: Core Foundation (Weeks 1-3)

| Task | Priority | Status |
|------|----------|--------|
| Set up project structure and packaging | High | ⬜ |
| Implement core data models (Pydantic) | High | ⬜ |
| Implement hasher utilities | High | ⬜ |
| Implement change detector engine | High | ⬜ |
| Implement SQLite storage backend | High | ⬜ |
| Implement basic parsers (TXT, MD) | High | ⬜ |
| Implement PDF parser | High | ⬜ |
| Implement DOCX parser | High | ⬜ |
| Create VersionTracker core class | High | ⬜ |
| Basic unit tests | High | ⬜ |

### Phase 2: Storage & CLI (Weeks 4-5)

| Task | Priority | Status |
|------|----------|--------|
| Implement Supabase storage backend | High | ⬜ |
| Implement PostgreSQL storage backend | Medium | ⬜ |
| Implement configuration loader | High | ⬜ |
| Build CLI with Click | High | ⬜ |
| CLI: init command | High | ⬜ |
| CLI: track command | High | ⬜ |
| CLI: status command | High | ⬜ |
| CLI: history command | Medium | ⬜ |
| CLI: diff command | Medium | ⬜ |
| Integration tests | High | ⬜ |

### Phase 3: Advanced Parsing (Weeks 6-7)

| Task | Priority | Status |
|------|----------|--------|
| Implement parser registry | High | ⬜ |
| HTML parser | Medium | ⬜ |
| PowerPoint (PPTX) parser | Medium | ⬜ |
| Excel (XLSX) parser | Medium | ⬜ |
| CSV parser | Medium | ⬜ |
| JSON parser | Low | ⬜ |
| Code file parser | Low | ⬜ |
| Custom parser registration | Medium | ⬜ |

### Phase 4: Events & Integrations (Weeks 8-9)

| Task | Priority | Status |
|------|----------|--------|
| Implement event emitter system | High | ⬜ |
| LangChain integration helpers | High | ⬜ |
| LlamaIndex integration helpers | High | ⬜ |
| Version diff functionality | Medium | ⬜ |
| Version restore functionality | Medium | ⬜ |
| Async support | Medium | ⬜ |

### Phase 5: Polish & Release (Weeks 10-12)

| Task | Priority | Status |
|------|----------|--------|
| Comprehensive documentation | High | ⬜ |
| API reference documentation | High | ⬜ |
| README with examples | High | ⬜ |
| PyPI packaging and publishing | High | ⬜ |
| GitHub Actions CI/CD | Medium | ⬜ |
| Example projects | Medium | ⬜ |
| Video tutorial for YouTube | Medium | ⬜ |
| Performance optimization | Low | ⬜ |

---

## Dependencies

### Core Dependencies (Required)

```toml
[project]
dependencies = [
    "pydantic>=2.0",          # Data validation and models
    "python-dotenv>=1.0",     # Environment variable loading
    "pyyaml>=6.0",            # Configuration file parsing
    "click>=8.0",             # CLI framework
    "rich>=13.0",             # Beautiful terminal output
    "httpx>=0.25",            # Async HTTP client
]
```

### Optional Dependencies (Extras)

```toml
[project.optional-dependencies]

# Storage backends
supabase = ["supabase>=2.0"]
postgres = ["asyncpg>=0.29", "psycopg2-binary>=2.9"]

# Document parsers
pdf = ["pymupdf>=1.23"]
pdf-alt = ["pdfplumber>=0.10"]
docx = ["python-docx>=1.1"]
pptx = ["python-pptx>=0.6"]
excel = ["openpyxl>=3.1"]
html = ["beautifulsoup4>=4.12", "lxml>=5.0"]

# All parsers bundle
all-parsers = [
    "pymupdf>=1.23",
    "python-docx>=1.1",
    "python-pptx>=0.6",
    "openpyxl>=3.1",
    "beautifulsoup4>=4.12",
]

# Development
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
    "pre-commit>=3.0",
]

# Full installation
all = [
    "ragversion[supabase,all-parsers,dev]"
]
```

### Installation Commands

```bash
# Minimal installation
pip install ragversion

# With Supabase and PDF support
pip install ragversion[supabase,pdf]

# With all parsers
pip install ragversion[supabase,all-parsers]

# Full installation with dev dependencies
pip install ragversion[all]

# Development installation
pip install -e ".[dev]"
```

---

## Testing Strategy

### Test Structure

```
tests/
├── unit/
│   ├── test_hasher.py
│   ├── test_detector.py
│   ├── test_models.py
│   ├── test_events.py
│   └── parsers/
│       ├── test_pdf_parser.py
│       ├── test_docx_parser.py
│       ├── test_txt_parser.py
│       └── test_registry.py
│
├── integration/
│   ├── test_sqlite_storage.py
│   ├── test_supabase_storage.py
│   ├── test_tracker_sqlite.py
│   └── test_tracker_supabase.py
│
├── e2e/
│   ├── test_full_workflow.py
│   ├── test_langchain_integration.py
│   └── test_cli.py
│
├── fixtures/
│   ├── sample.pdf
│   ├── sample.docx
│   ├── sample.txt
│   ├── sample.md
│   └── sample.html
│
└── conftest.py
```

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ragversion --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run specific test file
pytest tests/unit/test_hasher.py -v
```

---

## Future Enhancements

### Version 1.1

- [ ] Webhook support for change notifications
- [ ] S3/GCS storage for content snapshots
- [ ] Batch processing for large directories
- [ ] Parallel file processing

### Version 1.2

- [ ] Real-time file watching (watchdog integration)
- [ ] Supabase Edge Functions integration
- [ ] Redis caching layer
- [ ] Metrics and monitoring (Prometheus)

### Version 2.0

- [ ] Multi-tenant support with RLS
- [ ] REST API server mode
- [ ] Web dashboard for version visualization
- [ ] Semantic diff (AI-powered change summaries)
- [ ] Git-style branching for document versions

---

## Contributing

Guidelines for contributing to the project:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style

- Use Black for formatting
- Use Ruff for linting
- Type hints required for all functions
- Docstrings required for public APIs

---

## License

MIT License (recommended for open-source distribution)

---

## Contact

**Author:** Paul  
**Organization:** KrishAI Technologies  
**Email:** [your-email]  
**YouTube:** [your-channel]

---

*Document Version: 1.0*  
*Last Updated: January 2025*

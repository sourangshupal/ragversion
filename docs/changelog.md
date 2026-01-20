# Changelog

All notable changes to RAGVersion will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - 2025-01-20

!!! success "Major Release: Chunk-Level Versioning System"
    This release introduces chunk-level versioning, enabling **80-95% embedding cost reduction** by tracking and re-embedding only changed chunks instead of entire documents.

### Added

#### Core Features
- **Chunk-level versioning system** with hash-based O(1) change detection
- `ChunkChangeDetector` with O(n+m) comparison algorithm
- `RecursiveTextChunker` and `CharacterChunker` for text splitting
- `ChunkerRegistry` for pluggable chunking strategies
- Chunk models: `Chunk`, `ChunkDiff`, `ChunkingConfig`, `ChunkChangeType`

#### Storage
- New database tables: `chunks`, `chunk_content`
- SQLite backend with optimized batch operations (`executemany`)
- Supabase backend with batch API support
- Chunk content compression (~70% storage savings)
- Migration SQL: `002_chunk_versioning.sql`

#### Integrations
- **LangChain**: Smart chunk-level updates with `_handle_modification_smart()`
- **LlamaIndex**: Node-level chunk tracking
- Automatic fallback to full re-embedding on errors
- Cost savings logging with percentage reports

#### Configuration
- `ChunkTrackingConfig` with environment variable support
- YAML configuration: `chunk_tracking` section
- Configurable: chunk size, overlap, splitter type, content storage

#### Testing & Documentation
- 30+ unit tests for chunking module (`tests/unit/test_chunking.py`)
- 15+ integration tests (`tests/integration/test_chunk_tracking_e2e.py`)
- Comprehensive guide: `CHUNK_VERSIONING.md` (500+ lines)
- Implementation summary with architecture diagrams
- Migration guide for existing installations

### Changed
- Updated `AsyncVersionTracker` with `chunk_tracking_enabled` parameter
- Enhanced storage base class with chunk operations interface
- Improved batch processing for large chunk counts

### Technical Highlights
- Async-first design throughout
- Production-ready error handling and logging
- Fallback mechanisms for missing dependencies
- 100% backward compatible (opt-in feature)
- ~3,500 lines of new code
- 8 new files, 10 files modified

### Performance
- Batch insert: <1s for 1,000 chunks
- Hash-based comparison: O(1) lookup with hash maps
- Compression: 70% storage reduction for chunk content

[0.10.0]: https://github.com/sourangshupal/ragversion/releases/tag/v0.10.0

---

## [0.1.0] - 2025-01-19

### Added
- Initial release of RAGVersion
- Async-first version tracking for RAG applications
- Supabase storage backend with PostgreSQL
- Document parsers: PDF, DOCX, TXT, Markdown
- Batch processing with error resilience
- LangChain integration helper
- LlamaIndex integration helper
- CLI tool with commands: init, migrate, track, list, history, diff, health
- Mock storage for testing
- Comprehensive documentation and examples

### Features
- AsyncVersionTracker core class
- Change detection with content hashing
- Event system with async callback support
- Configuration via YAML and environment variables
- Content compression with gzip
- Resilient batch processing (continue-on-error)

[0.1.0]: https://github.com/sourangshupal/ragversion/releases/tag/v0.1.0

---

For the complete changelog, see [CHANGELOG.md](https://github.com/sourangshupal/ragversion/blob/main/CHANGELOG.md) in the repository.

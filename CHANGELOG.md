# Changelog

All notable changes to RAGVersion will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - 2026-01-20

### 🎯 Major Feature: Chunk-Level Versioning

**Achieve 80-95% embedding cost reduction** by tracking and re-embedding only changed chunks instead of entire documents.

### Added

#### Core Chunk Tracking
- **ChunkChangeDetector** - Hash-based O(1) chunk comparison algorithm
  - Detects ADDED, REMOVED, UNCHANGED, and REORDERED chunks
  - Calculates cost savings metrics
  - Supports batch operations for 1000+ chunks
- **ChunkerRegistry** - Pluggable text splitting strategies
  - RecursiveTextChunker (LangChain integration with fallback)
  - CharacterChunker (simple fixed-size splitting)
  - Easy registration of custom chunkers
- **Chunk Models** - New Pydantic models for type safety
  - `Chunk`: Represents a content chunk with hash, token count, metadata
  - `ChunkDiff`: Result of chunk comparison between versions
  - `ChunkingConfig`: Configuration for chunking strategies
  - `ChunkChangeType`: Enum for chunk change types

#### Storage Layer
- **Database Schema** - New tables for chunk storage
  - `chunks`: Core chunk metadata with indexes
  - `chunk_content`: Compressed chunk content storage
  - Migration: `002_chunk_versioning.sql` (SQLite + Supabase)
- **Batch Operations** - Optimized chunk storage
  - SQLite: `executemany` for fast batch inserts
  - Supabase: Batch API for efficient uploads
  - Compression: gzip reduces storage by ~70%
- **Storage Interface Extensions**
  - `create_chunks_batch()` - Batch chunk creation
  - `get_chunks_by_version()` - Retrieve chunks ordered by index
  - `store_chunk_content()` - Compressed content storage
  - `get_chunk_content()` - Auto-decompression on retrieval

#### Tracker Enhancements
- **AsyncVersionTracker** - Chunk tracking support
  - `chunk_tracking_enabled` parameter (opt-in, default: False)
  - `chunk_config` parameter for chunking configuration
  - `track_with_chunks()` - Track file and create chunks
  - `get_chunk_diff()` - Get chunk-level diff between versions
  - Automatic chunker initialization on startup

#### Smart Integration Updates
- **LangChainSync** - Smart chunk-level updates
  - `enable_chunk_tracking` parameter
  - `_handle_modification_smart()` - Only embed changed chunks
  - Automatic fallback to full re-embedding on errors
  - Cost savings logging
- **LlamaIndexSync** - Smart chunk-level updates
  - Parallel implementation to LangChain
  - Node-level chunk tracking
  - Graceful degradation

#### Configuration
- **ChunkTrackingConfig** - Environment variable support
  - `RAGVERSION_CHUNK_ENABLED` - Enable/disable chunk tracking
  - `RAGVERSION_CHUNK_CHUNK_SIZE` - Target chunk size
  - `RAGVERSION_CHUNK_CHUNK_OVERLAP` - Overlap between chunks
  - `RAGVERSION_CHUNK_SPLITTER_TYPE` - Chunking strategy
  - YAML configuration support

### Documentation
- **Comprehensive Chunk Versioning Guide** (`docs/CHUNK_VERSIONING.md`)
  - Architecture overview with diagrams
  - Quick start guide
  - Real-world cost savings examples
  - Integration patterns
  - Migration guide
  - API reference
  - Troubleshooting
  - Best practices

### Performance
- **Batch Insert Optimization** - <1 second for 1000+ chunks
- **Strategic Indexing** - Optimized queries for chunk retrieval
- **Compression** - 70% storage reduction for text content
- **O(1) Change Detection** - Hash-based comparison algorithm

### Backward Compatibility
- ✅ **100% backward compatible** - Chunk tracking is opt-in
- ✅ **Default disabled** - Existing installations work unchanged
- ✅ **Graceful fallback** - Falls back to document-level tracking if chunks unavailable
- ✅ **No breaking changes** - All existing APIs remain functional

### Migration Path
1. Run database migration (automatic for SQLite, manual for Supabase)
2. Enable chunk tracking in configuration
3. Re-track existing documents to create chunks
4. Enable smart updates in integrations

### Example Usage

```python
from ragversion import AsyncVersionTracker
from ragversion.models import ChunkingConfig

# Enable chunk tracking
tracker = AsyncVersionTracker(
    storage=storage,
    chunk_tracking_enabled=True,
    chunk_config=ChunkingConfig(
        enabled=True,
        chunk_size=500,
        chunk_overlap=50
    )
)

# Track with chunks
event, chunk_diff = await tracker.track_with_chunks("document.txt")
print(f"Savings: {chunk_diff.savings_percentage:.1f}%")

# Smart vector store updates
from ragversion.integrations.langchain import LangChainSync

sync = LangChainSync(
    tracker=tracker,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True  # Only embed changed chunks
)
```

### Technical Highlights
- **Hash-based comparison** - SHA-256 for reliable change detection
- **Async-first design** - All chunk operations are async
- **Type-safe models** - Pydantic validation throughout
- **Extensible architecture** - Easy to add custom chunkers
- **Production-ready** - Comprehensive error handling and logging

---

## [0.9.0] - 2026-01-20

### Added
- **Simple Web Viewer** - Lightweight, read-only web UI for content teams
  - Built with Jinja2 templates (server-side rendering)
  - No authentication required (read-only access)
  - Clean, modern interface with responsive design
  - Dashboard with statistics overview and file type distribution
  - Document browser with search, filtering, and pagination
  - Document detail pages with version history
  - Visual diff viewer for comparing versions
  - Works seamlessly with REST API

### Web UI Pages
- **Dashboard (`/`)**: Statistics overview, top documents, file type distribution
- **Documents List (`/documents`)**: Searchable, filterable document browser with pagination
- **Document Detail (`/documents/{id}`)**: Version history, statistics, metadata
- **Version Diff (`/documents/{id}/diff/{from}/{to}`)**: Side-by-side comparison with color-coded changes

### Features
- Clean, modern UI with custom CSS styling
- Statistics cards showing key metrics
- Interactive tables with sorting and pagination
- Badge indicators for file types and change types
- Color-coded diff viewer (additions, deletions, context)
- Breadcrumb navigation
- Empty states for better UX
- Responsive design for various screen sizes

### API Changes
- Moved API endpoints to `/api` prefix:
  - `/api/documents`, `/api/versions`, `/api/track`, `/api/statistics`
  - `/api/docs` - Swagger UI (was `/docs`)
  - `/api/redoc` - ReDoc documentation (was `/redoc`)
  - `/api/health` - Health check (was `/health`)
- Root path `/` now serves web UI dashboard
- Web routes registered alongside API routes

### CLI Updates
- Updated `ragversion serve` command:
  - Now starts both web UI and REST API
  - Displays web interface URLs on startup
  - Shows dashboard and documents URLs
  - Updated documentation string

### Dependencies
- Added `jinja2>=3.1.0` to `api` optional dependencies
- Jinja2 required for template rendering

### Benefits for Content Teams
- **No CLI required** - Browse documents visually in web browser
- **Intuitive interface** - Familiar web-based UI
- **Quick insights** - Dashboard shows key statistics at a glance
- **Easy navigation** - Click through documents and versions
- **Visual diff** - See changes between versions with syntax highlighting
- **Search & filter** - Find documents by name, type, or metadata

### Usage
```bash
# Start server (includes web UI + API)
ragversion serve

# Access web interface
# Dashboard: http://localhost:6699/
# Documents: http://localhost:6699/documents

# Access API docs
# Swagger: http://localhost:6699/api/docs
# ReDoc: http://localhost:6699/api/redoc
```

### Technical Details
- Server-side rendered templates (not a SPA)
- Lightweight (no JavaScript frameworks)
- Fast page loads
- SEO-friendly
- Minimal JavaScript (future enhancement opportunity)
- Built on FastAPI's Jinja2Templates integration

## [0.8.0] - 2026-01-20

### Added
- **REST API with FastAPI** - Complete HTTP API for programmatic access
  - FastAPI-based async web framework
  - Automatic OpenAPI/Swagger documentation at `/docs`
  - ReDoc documentation at `/redoc`
  - Health check endpoint at `/health`
  - Full CORS support (configurable)
  - Optional API key authentication via `X-API-Key` header
  - Pydantic models for request/response validation
  - Dependency injection for tracker management
  - Comprehensive error handling with proper HTTP status codes

### API Endpoints

**Document Management:**
- `GET /documents` - List documents with pagination
- `GET /documents/{id}` - Get document by ID
- `GET /documents/path/{path}` - Get document by file path
- `POST /documents/search` - Search by type and metadata
- `DELETE /documents/{id}` - Delete document
- `GET /documents/top/by-version-count` - Get top documents

**Version Management:**
- `GET /versions/{id}` - Get version by ID
- `GET /versions/document/{id}` - List versions for document
- `GET /versions/document/{id}/number/{num}` - Get version by number
- `GET /versions/document/{id}/latest` - Get latest version
- `GET /versions/{id}/content` - Get version content
- `POST /versions/restore` - Restore to specific version
- `GET /versions/document/{id}/diff/{from}/{to}` - Get diff

**Tracking Operations:**
- `POST /track/file` - Track single file
- `POST /track/directory` - Track directory (batch)

**Statistics:**
- `GET /statistics` - Get storage statistics
- `GET /statistics/document/{id}` - Get document statistics

### CLI Commands
- `ragversion serve` - Start REST API server
  - `--host` - Bind host (default: 0.0.0.0)
  - `--port` - Bind port (default: 6699)
  - `--reload` - Enable auto-reload for development
  - Displays API endpoint URLs on startup
  - Graceful shutdown handling

### Configuration
- New `api` optional dependency group with FastAPI and uvicorn
- API configuration via `ragversion.yaml`:
  - `api.host` - Server host
  - `api.port` - Server port
  - `api.cors_enabled` - Enable/disable CORS
  - `api.cors_origins` - Allowed origins list
  - `api.auth_enabled` - Enable API key auth
  - `api.api_keys` - List of valid API keys

### Documentation
- Comprehensive API guide (`docs/API_GUIDE.md`):
  - Complete endpoint reference
  - Request/response models
  - Authentication guide
  - Code examples (Python, JavaScript, cURL)
  - Error handling patterns
  - Production deployment guides (Docker, systemd)
  - Best practices
  - Troubleshooting tips
- Python client example (`examples/api/api_client_example.py`):
  - Synchronous client class
  - Asynchronous client class
  - Usage examples for all endpoints
  - Concurrent request patterns

### Features
- Automatic OpenAPI schema generation
- Interactive API documentation
- Request validation with Pydantic
- Response serialization
- Pagination support for list endpoints
- Query parameter validation
- Path parameter validation
- JSON request body validation
- Proper HTTP status codes (200, 404, 500, etc.)
- Structured error responses
- Health check with storage backend status
- Lifespan management (startup/shutdown events)

### Installation
```bash
# Install with API support
pip install ragversion[api]

# Or install all features
pip install ragversion[all]
```

### Usage
```bash
# Start API server
ragversion serve

# Custom port
ragversion serve --port 5000

# Development mode
ragversion serve --reload

# Access documentation
# Swagger UI: http://localhost:6699/docs
# ReDoc: http://localhost:6699/redoc
```

### Benefits
- **Language Agnostic** - Use from any language with HTTP support
- **Framework Integration** - Easy integration with web frameworks
- **Programmatic Access** - Automate version tracking workflows
- **Web UIs** - Build custom dashboards and interfaces
- **Microservices** - Deploy as standalone service
- **Cloud Native** - Ready for Docker/Kubernetes deployment

## [0.7.0] - 2026-01-20

### Added
- **Query Optimization** - 10-100x faster queries for large document sets
  - 15+ comprehensive indexes for common query patterns
  - Composite indexes for complex queries (type + sorting, document + time)
  - Covering indexes to avoid table lookups
  - JSON1 extension support for efficient metadata filtering
  - Optimized PRAGMA settings (cache, mmap, synchronous)
  - ANALYZE command for query planner statistics
  - Performance documentation (`docs/QUERY_OPTIMIZATION.md`)
  - Query benchmark suite (`examples/benchmarks/query_benchmark.py`)

### Indexes
- **Primary lookups:** file_path, content_hash
- **Sorting:** updated_at, created_at, file_name, file_size, version_count
- **Filtering:** file_type, change_type
- **Composite:** type+updated, type+size, doc+created, doc+change_type
- All indexes optimized with DESC/COLLATE directives

### Performance
- List 100 recent documents: **0.77ms** (from ~250ms, 325x faster)
- Search by file type: **1.49ms** (from ~450ms, 300x faster)
- Get version history: **0.14ms** (from ~180ms, 1285x faster)
- Search by type + metadata: **0.28ms** (from ~1200ms with JSON1, 4285x faster)
- Get document by path: **0.09ms** (from ~50ms, 555x faster)

### PRAGMA Optimizations
- `synchronous = NORMAL` - Faster commits
- `cache_size = -64000` - 64MB page cache
- `temp_store = MEMORY` - In-memory temp tables
- `mmap_size = 268435456` - 256MB memory-mapped I/O

### Documentation
- Comprehensive query optimization guide with 500+ lines
- Index strategy explanations
- Query pattern analysis
- Performance tuning recommendations
- Benchmarking guide
- Troubleshooting tips
- Comparison with Supabase

## [0.6.0] - 2026-01-20

### Added
- **Change Notifications System** - Real-time alerts when documents change
  - Four notification providers: Slack, Discord, Email (SMTP), and Generic Webhooks
  - `NotificationManager` for orchestrating multiple notifiers simultaneously
  - Support for parallel or sequential notification delivery
  - Conditional notifications (e.g., only for deletions)
  - User and role mentions for Slack and Discord
  - HTML/plain text multipart email notifications
  - Customizable webhook payloads with metadata
  - Automatic retry and error handling
  - Integration with `AsyncVersionTracker` via `notification_manager` parameter
  - Integration with file watching for real-time alerts
- New `notifications` configuration section in `ragversion.yaml`
- `create_notification_manager()` factory function for building notifiers from config
- Comprehensive notifications documentation (`docs/NOTIFICATIONS.md`)
- Example configurations for all notification providers (`examples/notifications/`)
  - Slack example with user mentions
  - Discord example with role mentions
  - Email example with SMTP configuration
  - Webhook example with custom headers
  - Multi-provider example with environment variables
- `httpx` dependency for async HTTP requests

### Configuration
- Added `NotificationsConfig` with `enabled` flag and `notifiers` list
- Support for environment variable interpolation in notification configs
- Configurable timeout, headers, and retry behavior per notifier

### Integration
- Notifications automatically sent when documents are tracked
- Works seamlessly with file watching (`ragversion watch`)
- Custom metadata flows through to notification payloads
- Fire-and-forget error handling (failures don't block tracking)

### Documentation
- Complete notifications guide with setup instructions
- Provider-specific documentation (Slack, Discord, Email, Webhook)
- Security best practices
- Troubleshooting guide
- Advanced topics (custom notifiers, error handling)
- Example configurations and code samples

## [0.5.0] - 2026-01-20

### Added
- **Real-Time File Watching** - Automatic document tracking without manual intervention
  - New `ragversion watch` CLI command for daemon mode
  - `FileWatcher` class for programmatic watching
  - `watch_directory()` and `watch_paths()` convenience functions
  - Pattern matching for specific file types (e.g., *.md, *.txt)
  - Ignore patterns to exclude unwanted files
  - Automatic debouncing (1 second) for rapid file changes
  - Graceful shutdown handling (SIGINT/SIGTERM)
  - Custom callback support for change events
  - Background watching mode
- Comprehensive file watching documentation (`docs/FILE_WATCHING.md`)
- Integration test for file watcher functionality
- `watchdog` library dependency for file system monitoring

### Features
- **Real-time monitoring** - Instantly detect create, modify, delete events
- **Recursive watching** - Monitor nested directories automatically
- **Low overhead** - Event-driven architecture with minimal CPU usage
- **Production-ready** - Daemon mode with systemd/Docker examples

### Documentation
- Complete file watching guide with examples
- CLI usage examples (basic, patterns, ignore, verbose)
- Python API documentation with code samples
- Use cases (development, monitoring, notifications, RAG integration)
- Daemon mode setup (systemd, Docker)
- Performance guidelines and scaling tips
- Troubleshooting guide
- Best practices and anti-patterns

## [0.4.0] - 2026-01-20

### Added
- **Batch Operations** - High-performance bulk insert methods
  - `batch_create_documents()` - Insert multiple documents in single transaction
  - `batch_create_versions()` - Insert multiple versions in single transaction
  - 10-15x faster for SQLite (91% time reduction)
  - 20-50x faster for Supabase (fewer network round trips)
- **GitHub Actions Integration** - Automatic tracking in CI/CD pipelines
  - Reusable composite action (`.github/actions/ragversion-track`)
  - Support for both SQLite and Supabase backends
  - PR documentation validation workflows
  - Scheduled tracking jobs
  - Artifact upload for SQLite databases
  - Example workflows for common use cases
- Comprehensive performance documentation (`docs/PERFORMANCE.md`)
- GitHub Actions documentation (`docs/GITHUB_ACTIONS.md`)
- Performance benchmarks and optimization guide
- Scaling guidelines for small to very large deployments

### Performance
- **11x faster** bulk document creation (SQLite)
- **~118,000 docs/sec** throughput for batch operations (vs 11,800 for individual)
- Optimized indexes for common query patterns
- Connection reuse for better resource utilization

### Documentation
- Added detailed performance optimization guide
- Benchmarks for batch vs individual operations
- Scaling guidelines (1K to 100K+ documents)
- Common performance issues and solutions
- Best practices checklist

## [0.3.0] - 2026-01-20

### Added
- **SQLite Storage Backend** - Zero-configuration local storage (now default)
  - Async support via aiosqlite
  - Automatic schema management (no manual migrations needed)
  - WAL mode for better concurrency
  - In-memory database support for testing
  - Content compression with gzip
- Storage backend selection via configuration (`sqlite` or `supabase`)
- Comprehensive SQLite documentation (`docs/SQLITE_BACKEND.md`)
- Updated example configuration with SQLite as default

### Changed
- **BREAKING**: Default storage backend changed from Supabase to SQLite
  - Existing users: Add `storage.backend: supabase` to `ragversion.yaml` to keep using Supabase
  - New users: Works immediately with zero configuration
- Simplified CLI setup - no configuration required for basic usage
- Updated README with zero-config quick start
- CLI commands now support both SQLite and Supabase backends automatically
- `migrate` command now auto-migrates SQLite (no manual steps needed)

### Fixed
- Storage backend factory pattern for cleaner CLI code
- Configuration loading with better defaults

### Documentation
- Added detailed SQLite backend guide
- Updated Quick Start with zero-config examples
- Added migration guide from SQLite to Supabase
- Updated all code examples to show both backends

## [0.2.0] - 2026-01-19

### Added
- Statistics and analytics command (`ragversion stats`)
- JSON export support for statistics
- Rich CLI visualizations with tables and charts
- Document-specific analytics
- Top documents query by version count/size/activity

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

[0.5.0]: https://github.com/sourangshupal/ragversion/releases/tag/v0.5.0
[0.4.0]: https://github.com/sourangshupal/ragversion/releases/tag/v0.4.0
[0.3.0]: https://github.com/sourangshupal/ragversion/releases/tag/v0.3.0
[0.2.0]: https://github.com/sourangshupal/ragversion/releases/tag/v0.2.0
[0.1.0]: https://github.com/sourangshupal/ragversion/releases/tag/v0.1.0

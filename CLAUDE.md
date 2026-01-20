# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAGVersion is an async-first version tracking system for RAG (Retrieval-Augmented Generation) applications. It tracks document changes, maintains version history, and integrates with LangChain and LlamaIndex frameworks. The system uses Supabase as the primary storage backend.

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install development dependencies
pip install -e ".[dev]"

# Install with all optional dependencies
pip install -e ".[all]"
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=ragversion --cov-report=html

# Run specific test file
pytest tests/test_tracker.py

# Run tests in verbose mode
pytest -v
```

### Code Quality
```bash
# Format code with Black (100 character line length)
black ragversion/

# Lint with Ruff
ruff check ragversion/

# Type checking with mypy
mypy ragversion/

# Run all checks before committing
black ragversion/ && ruff check ragversion/ && mypy ragversion/ && pytest
```

### CLI Development
```bash
# Test CLI commands locally
python -m ragversion.cli --help

# Run specific CLI commands
python -m ragversion.cli init
python -m ragversion.cli track ./documents
python -m ragversion.cli list
```

## Architecture Overview

### Core Components

1. **AsyncVersionTracker** (`ragversion/tracker.py`)
   - Main entry point for all tracking operations
   - Manages async context and lifecycle (initialize/close)
   - Provides event system with callbacks
   - Handles batch processing with semaphore-based concurrency control
   - Must be initialized before use: `await tracker.initialize()` or use as context manager

2. **ChangeDetector** (`ragversion/detector.py`)
   - Detects changes by comparing content hashes (SHA-256 by default)
   - Normalizes all file paths to absolute paths for consistency
   - Delegates to ParserRegistry for file parsing
   - Creates Document and Version records via storage backend
   - Handles four change types: CREATED, MODIFIED, DELETED, RESTORED

3. **Storage Layer** (`ragversion/storage/`)
   - Abstract interface: `BaseStorage` defines all storage operations
   - Current implementation: `SupabaseStorage` (async Supabase client)
   - All operations are async and must be awaited
   - Manual migrations required (SQL files provided, run in Supabase console)

4. **Parser System** (`ragversion/parsers/`)
   - `ParserRegistry`: Routes files to appropriate parser based on extension
   - Parsers: PDF, DOCX, Text, Markdown
   - All parsers are async and implement `BaseParser.parse(file_path) -> str`
   - Falls back to text parser for unknown file types

5. **Models** (`ragversion/models.py`)
   - Pydantic models for type safety and validation
   - Key models: Document, Version, ChangeEvent, BatchResult, DiffResult
   - All use UTC timestamps (datetime.utcnow())
   - UUIDs for all primary identifiers

### Integration Architecture

**LangChain Integration** (`ragversion/integrations/langchain.py`):
- `LangChainSync`: Real-time sync using tracker callbacks
- Registers callback via `tracker.on_change()` to automatically update vector stores
- `LangChainLoader`: One-time bulk loading for migrations
- Requires vector store to support deletion by metadata filter

**LlamaIndex Integration** (`ragversion/integrations/llamaindex.py`):
- Similar pattern to LangChain integration
- Uses node-level tracking

### Async Patterns

The entire codebase is async-first:
- All I/O operations use `async`/`await`
- File reading uses `aiofiles`
- Storage operations are async
- Batch processing uses `asyncio.gather()` with semaphore for concurrency control
- Callbacks can be sync or async (automatically detected with `inspect.iscoroutinefunction()`)

### Error Handling Philosophy

**Continue-on-Error Design**:
- Batch operations (`track_directory`) continue processing even if individual files fail
- Failed files captured in `BatchResult.failed` with detailed error types
- Error types: "parsing", "storage", "unknown"
- Configurable via `on_error` parameter: "continue" (default) or "stop"

## Key Patterns and Conventions

### File Path Normalization
All file paths are normalized to absolute paths using `Path(file_path).absolute()` for consistency across storage and tracking operations.

### Version Numbering
- Versions are 1-indexed (first version is 1, not 0)
- Document tracks `current_version` and `version_count`
- Each change increments both values
- Deletion creates a version with file_size=0 and no content

### Content Hashing
- Default algorithm: SHA-256 (configurable)
- Hash computed on parsed text content (not raw bytes)
- Used for change detection: `existing_doc.content_hash != new_hash`

### Metadata System
- Both Document and Version support arbitrary metadata dictionaries
- Metadata flows through: track() -> ChangeEvent -> Version
- Document metadata updates merge (doesn't replace)

### Context Manager Usage
Always use tracker as async context manager in production:
```python
async with AsyncVersionTracker(storage=storage) as tracker:
    result = await tracker.track_directory("./docs")
```

### Callback System
- Register callbacks: `tracker.on_change(callback)`
- Callbacks can be sync or async
- Timeout enforced (default 60s, configurable via `callback_timeout`)
- Exceptions in callbacks are logged but don't stop processing

## Configuration

### Environment Variables
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### Config File (ragversion.yaml)
- Uses Pydantic Settings for validation
- Supports environment variable interpolation: `${SUPABASE_URL}`
- Config loaded via `RAGVersionConfig.load(config_path)`

## Database Schema

Key tables (defined in SQL migrations):
- `documents`: Main document tracking table
- `versions`: Version history per document
- `version_content`: Stores actual content (optionally compressed)

All tables use UUIDs as primary keys. Foreign key: `versions.document_id -> documents.id`

## Common Workflows

### Adding a New Parser
1. Create new parser class in `ragversion/parsers/`
2. Inherit from `BaseParser`
3. Implement async `parse(file_path: str) -> str` method
4. Register in `ParserRegistry` with file extensions
5. Add optional dependency to `pyproject.toml` if needed

### Adding a New Storage Backend
1. Create new storage module in `ragversion/storage/`
2. Inherit from `BaseStorage`
3. Implement all abstract methods (initialize, close, CRUD operations)
4. Add configuration support in `ragversion/config.py`
5. Update CLI to support new backend

### Extending Integration Support
1. Create new integration file in `ragversion/integrations/`
2. Follow pattern: Sync class (real-time) + Loader class (bulk)
3. Use tracker callbacks for real-time updates
4. Provide metadata extraction customization
5. Add optional dependency group in `pyproject.toml`

## Testing Strategy

- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Test utilities: `ragversion/testing/` (MockStorage, fixtures)
- Use `pytest-asyncio` for async tests
- Mock storage backend for fast unit tests
- Integration tests require Supabase credentials

## Important Implementation Details

### Semaphore-Based Concurrency
Batch processing uses `asyncio.Semaphore(max_workers)` to limit concurrent file processing. Default is 4 workers.

### Content Storage
- Controlled by `store_content` flag (default: True)
- When False, only hashes are stored (for deduplication only)
- Content stored separately in storage backend (compression optional)

### Change Detection Logic
```python
if not file_exists:
    if was_tracked: DELETED
    else: None (skip)
elif not was_tracked: CREATED
elif hash_changed: MODIFIED
else: None (unchanged)
```

### Rich Console Output
CLI uses Rich library for formatted output (tables, status, colors). When modifying CLI, maintain consistent styling.

## Dependencies

**Core** (always installed):
- pydantic, aiofiles, click, pyyaml, python-dotenv, supabase, httpx

**Optional Groups**:
- `[parsers]`: pypdf, python-docx, python-pptx, openpyxl, markdown
- `[langchain]`: langchain, langchain-community
- `[llamaindex]`: llama-index
- `[dev]`: pytest, black, ruff, mypy, pre-commit

## Release Process

Version defined in:
- `pyproject.toml`: `version = "0.1.0"`
- `ragversion/__init__.py`: `__version__ = "0.1.0"`

Keep these synchronized when releasing.

## Common Pitfalls

1. **Forgetting to initialize tracker**: Always call `await tracker.initialize()` or use context manager
2. **Mixing sync/async code**: Everything in this codebase is async
3. **File path inconsistencies**: Always use normalized absolute paths
4. **Version numbering**: Remember versions are 1-indexed, not 0-indexed
5. **Storage migrations**: Migrations must be run manually in Supabase SQL editor
6. **Rich import in CLI**: CLI requires `rich` library for console output

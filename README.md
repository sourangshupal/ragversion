<div align="center">

# 🔄 RAGVersion

**Async-first version tracking system for RAG applications**

[![PyPI version](https://badge.fury.io/py/ragversion.svg)](https://badge.fury.io/py/ragversion)
[![Python Support](https://img.shields.io/pypi/pyversions/ragversion.svg)](https://pypi.org/project/ragversion/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/ragversion)](https://pepy.tech/project/ragversion)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![GitHub stars](https://img.shields.io/github/stars/sourangshupal/ragversion?style=social)](https://github.com/sourangshupal/ragversion/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/sourangshupal/ragversion?style=social)](https://github.com/sourangshupal/ragversion/network/members)
[![GitHub issues](https://img.shields.io/github/issues/sourangshupal/ragversion)](https://github.com/sourangshupal/ragversion/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/sourangshupal/ragversion)](https://github.com/sourangshupal/ragversion/pulls)
[![Last Commit](https://img.shields.io/github/last-commit/sourangshupal/ragversion)](https://github.com/sourangshupal/ragversion/commits/main)

[📖 How-to Guide](How_to.md) • [Documentation](DOCUMENTATION.md) • [Roadmap](future-enhancements.md) • [Contributing](CONTRIBUTING.md) • [PyPI](https://pypi.org/project/ragversion/)

</div>

---

RAGVersion is a plug-and-play module that tracks document changes and integrates seamlessly with LangChain, LlamaIndex, and other RAG frameworks. It provides automatic version control, change detection, and content diffing for your document pipelines.

<div align="center">

**[Key Features](#features)** • **[Quick Start](#quick-start)** • **[Integrations](#integrations)** • **[CLI](#cli)** • **[Documentation](#documentation)**

</div>

## ✨ Features

<table>
<tr>
<td width="50%">

### Core Capabilities
- 🚀 **Async-first architecture** - Built for modern Python async/await patterns
- 📦 **Plug-and-play** - Works with any RAG system
- 🔄 **Batch processing** - Efficiently process large document collections
- 👀 **Real-time file watching** - Automatic tracking with daemon mode
- 🛡️ **Resilient** - Continue-on-error design for production systems

</td>
<td width="50%">

### Integrations & Storage
- 💾 **Zero-config SQLite** - Default local storage, no setup required
- ☁️ **Supabase option** - Cloud storage with PostgreSQL
- 🌐 **REST API** - FastAPI-based HTTP API with automatic OpenAPI docs
- 🔗 **Framework integrations** - LangChain & LlamaIndex ready
- 📝 **Document parsing** - PDF, DOCX, TXT, Markdown support
- 🔍 **Change detection** - Automatic tracking with content hashing
- ⚡ **GitHub Actions** - Automatic tracking in CI/CD pipelines
- 🔔 **Smart notifications** - Slack, Discord, Email, and webhook alerts
- ⚡ **Query optimization** - 100-1000x faster queries with comprehensive indexing

</td>
</tr>
</table>

## 🎯 Why RAGVersion?

> **Problem**: RAG applications need to track when documents change to keep vector databases in sync, but most solutions require manual tracking or complex pipelines.

> **Solution**: RAGVersion automatically detects document changes and provides version history, making it easy to maintain up-to-date RAG systems.

**Perfect for:**
- 📚 Documentation sites that need to track content updates
- 🤖 AI chatbots that need fresh knowledge bases
- 📊 Data pipelines processing evolving documents
- 🔄 Systems requiring audit trails of document changes

---

## 📦 Installation

```bash
# Basic installation
pip install ragversion

# With all parsers
pip install ragversion[parsers]

# With REST API support
pip install ragversion[api]

# With LangChain integration
pip install ragversion[langchain]

# With LlamaIndex integration
pip install ragversion[llamaindex]

# Everything (recommended)
pip install ragversion[all]
```

**System Requirements:**
- Python 3.9+
- (Optional) Supabase account for cloud storage

<details>
<summary>📋 Optional Dependencies</summary>

- `parsers` - PDF, DOCX, and other document parsers
- `langchain` - LangChain framework integration
- `llamaindex` - LlamaIndex framework integration
- `all` - All optional dependencies

</details>

## 🚀 Quick Start

### Zero-Config Setup (SQLite - Recommended for Getting Started)

```bash
# 1. Install RAGVersion
pip install ragversion[all]

# 2. Start tracking immediately - no configuration needed!
ragversion track ./documents

# That's it! RAGVersion uses SQLite by default (ragversion.db)
```

### Basic Usage (Python)

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage

async def main():
    # Initialize tracker with SQLite (zero configuration)
    tracker = AsyncVersionTracker(
        storage=SQLiteStorage()  # Creates ragversion.db automatically
    )

    # Track a single file
    change = await tracker.track("document.pdf")
    if change:
        print(f"Document changed: {change.change_type}")

    # Track a directory (batch processing)
    result = await tracker.track_directory(
        "./documents",
        patterns=["*.pdf", "*.docx"],
        recursive=True
    )

    print(f"✅ Processed: {len(result.successful)} files")
    print(f"❌ Failed: {len(result.failed)} files")

asyncio.run(main())
```

<details>
<summary>☁️ Cloud Setup (Supabase - For Production/Collaboration)</summary>

```bash
# 1. Install RAGVersion
pip install ragversion[all]

# 2. Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"

# 3. Configure backend
echo "storage:
  backend: supabase
  supabase:
    url: \${SUPABASE_URL}
    key: \${SUPABASE_SERVICE_KEY}" > ragversion.yaml

# 4. Initialize database
ragversion migrate

# 5. Start tracking!
ragversion track ./documents
```

**Python usage with Supabase:**
```python
from ragversion.storage import SupabaseStorage

async def main():
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env()
    )
    # ... rest of your code
```

</details>

### ⚡ Framework Integration (LangChain/LlamaIndex)

**NEW in v0.11.0**: One-line setup for LangChain and LlamaIndex!

<table>
<tr>
<td width="50%">

**LangChain (3 lines!)**
```python
from ragversion.integrations.langchain import quick_start

# That's it! 🚀
sync = await quick_start("./documents")

# Ready to query
results = await sync.vectorstore.asimilarity_search("query")
```

</td>
<td width="50%">

**LlamaIndex (3 lines!)**
```python
from ragversion.integrations.llamaindex import quick_start

# That's it! 🚀
sync = await quick_start("./documents")

# Ready to query
query_engine = sync.index.as_query_engine()
response = query_engine.query("query")
```

</td>
</tr>
</table>

**What `quick_start()` does automatically:**
- ✅ Creates and initializes RAGVersion tracker
- ✅ Sets up vector store (FAISS/Chroma for LangChain)
- ✅ Configures embeddings (OpenAI by default)
- ✅ Creates text splitter with optimal defaults
- ✅ Syncs your documents directory
- ✅ Enables smart chunk-level tracking (80-95% cost savings!)

**Before vs After:**
```python
# BEFORE: 35+ lines of boilerplate 😰
storage = SupabaseStorage.from_env()
tracker = AsyncVersionTracker(storage=storage)
await tracker.initialize()
text_splitter = RecursiveCharacterTextSplitter(...)
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(...)
sync = LangChainSync(tracker, text_splitter, embeddings, vectorstore)
await sync.sync_directory("./documents")

# AFTER: 3 lines 🎉
from ragversion.integrations.langchain import quick_start
sync = await quick_start("./documents")
# Done!
```

**Customization options:**
```python
# LangChain with custom settings
sync = await quick_start(
    directory="./documents",
    vectorstore_type="faiss",        # or "chroma"
    vectorstore_path="./vectorstore", # persistent storage
    storage_backend="sqlite",         # or "supabase", "auto"
    chunk_size=500,                  # custom chunk size
    enable_chunk_tracking=True,      # smart updates (default)
)

# LlamaIndex with custom settings
sync = await quick_start(
    directory="./documents",
    storage_backend="supabase",      # cloud storage
    chunk_size=2048,                 # larger chunks
    enable_chunk_tracking=False,     # disable for full re-embedding
)
```

👉 **[See complete quick start examples](examples/quick_start_langchain.py)**

---

## 🎓 Complete Integration Guide

**Want to integrate RAGVersion with LangChain or LlamaIndex?**

👉 **[Read the complete How-to Guide](How_to.md)** - Comprehensive guide with 10+ practical examples:

- ✅ LangChain integration (basic and chunk-level)
- ✅ LlamaIndex integration (basic and chunk-level)
- ✅ Real-time file watching
- ✅ Cost optimization with chunk-level versioning (80-95% savings!)
- ✅ 4 common use cases (docs, support KB, research, multi-tenant)
- ✅ Best practices and troubleshooting
- ✅ Production-ready complete example

**Quick Example - LangChain with Chunk Tracking:**
```python
from ragversion import AsyncVersionTracker
from ragversion.models import ChunkingConfig
from ragversion.integrations.langchain import LangChainSync

# Enable chunk tracking for 80-95% cost savings!
chunk_config = ChunkingConfig(enabled=True, chunk_size=500)
tracker = AsyncVersionTracker(
    storage=storage,
    chunk_tracking_enabled=True,
    chunk_config=chunk_config
)

# Auto-sync with LangChain - only changed chunks re-embedded!
sync = LangChainSync(
    tracker=tracker,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True
)
await sync.sync_directory("./docs")
```

---

## ⚙️ Configuration

### Default (SQLite) - No Configuration Required

RAGVersion works out of the box with SQLite. No setup needed!

```bash
# Just start tracking - uses ragversion.db by default
ragversion track ./documents
```

### Custom Configuration File (Optional)

Create a `ragversion.yaml` file for advanced settings:

```yaml
storage:
  backend: sqlite  # or "supabase" for cloud storage
  sqlite:
    db_path: ragversion.db
    content_compression: true

tracking:
  store_content: true
  max_file_size_mb: 50
  batch:
    max_workers: 4
    on_error: continue

content:
  compression: gzip
  ttl_days: 365
```

### Switching to Supabase (Cloud Storage)

For production or team collaboration:

```yaml
storage:
  backend: supabase
  supabase:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_SERVICE_KEY}
```

Or use environment variables:

```bash
export RAGVERSION_STORAGE_BACKEND=supabase
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

<details>
<summary>🔧 Advanced Configuration Options</summary>

```yaml
# Full configuration example with all options
storage:
  backend: supabase
  supabase:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_SERVICE_KEY}
    connection_timeout: 30
    retry_attempts: 3

tracking:
  store_content: true
  max_file_size_mb: 50
  hash_algorithm: sha256
  batch:
    max_workers: 4
    on_error: continue
    timeout_seconds: 300

content:
  compression: gzip
  compression_level: 6
  ttl_days: 365

notifications:
  enabled: true
  notifiers:
    - type: slack
      name: team-slack
      enabled: true
      webhook_url: ${SLACK_WEBHOOK_URL}
    - type: discord
      name: dev-discord
      enabled: true
      webhook_url: ${DISCORD_WEBHOOK_URL}
    - type: email
      name: admin-email
      enabled: true
      smtp_host: smtp.gmail.com
      smtp_port: 587
      smtp_username: ${EMAIL_USERNAME}
      smtp_password: ${EMAIL_PASSWORD}
      from_address: ragversion@company.com
      to_addresses:
        - admin@company.com

events:
  enabled: true
  handlers:
    - type: webhook
      url: https://your-webhook-url.com
```

</details>

---

## ⚡ GitHub Actions Integration

Automatically track documentation changes in your CI/CD pipeline:

```yaml
# .github/workflows/track-docs.yml
name: Track Documentation

on:
  push:
    branches: [main]
    paths: ['docs/**', '*.md']

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Track documentation with RAGVersion
        uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/ README.md'
          storage-backend: 'sqlite'
          file-patterns: '*.md *.txt *.pdf'
```

**Benefits:**
- ✅ Automatic tracking on every commit
- ✅ PR documentation validation
- ✅ Scheduled tracking jobs
- ✅ Zero manual intervention
- ✅ Archive tracking history as artifacts

**Common Use Cases:**

<table>
<tr>
<td width="50%">

**PR Checks**
```yaml
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  check-docs:
    steps:
      - uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/'
          fail-on-error: true
```

</td>
<td width="50%">

**Scheduled Tracking**
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  track:
    steps:
      - uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/ examples/'
          max-workers: 8
```

</td>
</tr>
</table>

📖 **Full documentation:** [docs/GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md)

---

## 👀 Real-Time File Watching

Automatically track document changes without manual intervention:

```bash
# Start watching a directory
ragversion watch ./docs

# Watch only Markdown files
ragversion watch ./docs --pattern "*.md"

# Watch multiple directories
ragversion watch ./docs ./guides --pattern "*.md" --pattern "*.txt"
```

**Features:**
- ✅ Real-time change detection (create, modify, delete)
- ✅ Pattern matching for specific file types
- ✅ Recursive directory watching
- ✅ Automatic debouncing
- ✅ Custom change callbacks
- ✅ Daemon mode for 24/7 monitoring

**Python API:**

```python
from ragversion import watch_directory

async def on_change(change):
    print(f"📄 {change.change_type.value}: {change.file_name}")

async def main():
    async with AsyncVersionTracker(storage=storage) as tracker:
        await watch_directory(
            tracker,
            "./docs",
            patterns=["*.md", "*.txt"],
            on_change=on_change
        )

asyncio.run(main())
```

**Use Cases:**
- 🔄 Development environment (auto-track while editing)
- 🚀 Production monitoring (24/7 daemon mode)
- 🔔 Custom notifications (Slack, email, webhooks)
- 🤖 RAG integration (auto-update vector stores)

📖 **Full documentation:** [docs/FILE_WATCHING.md](docs/FILE_WATCHING.md)

---

## 🔔 Notifications

Get real-time alerts when documents change via Slack, Discord, Email, or custom webhooks.

```yaml
# ragversion.yaml
notifications:
  enabled: true
  notifiers:
    - type: slack
      name: team-slack
      enabled: true
      webhook_url: ${SLACK_WEBHOOK_URL}
      mention_on_types: ["deleted"]  # Mention users for deletions

    - type: discord
      name: dev-discord
      enabled: true
      webhook_url: ${DISCORD_WEBHOOK_URL}

    - type: email
      name: admin-email
      enabled: true
      smtp_host: smtp.gmail.com
      smtp_port: 587
      smtp_username: ${EMAIL_USERNAME}
      smtp_password: ${EMAIL_PASSWORD}
      from_address: ragversion@company.com
      to_addresses:
        - admin@company.com
```

**Supported Providers:**
- 💬 **Slack** - Rich formatted messages with user mentions
- 🎮 **Discord** - Embed-based notifications with role mentions
- 📧 **Email** - HTML/plain text via SMTP
- 🔗 **Webhook** - Custom HTTP endpoints for any integration

**Features:**
- ✅ Multiple providers simultaneously
- ✅ Parallel or sequential delivery
- ✅ Conditional notifications (e.g., only for deletions)
- ✅ User/role mentions
- ✅ Custom metadata in messages
- ✅ Automatic retry and error handling

**CLI Usage:**
```bash
# Notifications are sent automatically with file watching
ragversion watch ./documents --config ragversion.yaml
```

**Python API:**
```python
from ragversion.notifications import create_notification_manager
from ragversion.config import RAGVersionConfig

# Load config with notifications
config = RAGVersionConfig.load("ragversion.yaml")
notification_manager = create_notification_manager(
    config.notifications.notifiers
)

# Create tracker with notifications
tracker = AsyncVersionTracker(
    storage=storage,
    notification_manager=notification_manager
)

async with tracker:
    await tracker.track("./documents/report.pdf")
    # Notifications sent automatically
```

📖 **Full documentation:** [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md)
📝 **Examples:** [examples/notifications/](examples/notifications/)

---

## 🔗 Integrations

RAGVersion seamlessly integrates with popular RAG frameworks:

<table>
<tr>
<td width="50%" valign="top">

### 🦜 LangChain

```python
from ragversion.integrations.langchain import LangChainSync
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant

sync = LangChainSync(
    tracker=tracker,
    text_splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000
    ),
    embeddings=OpenAIEmbeddings(),
    vectorstore=qdrant_client
)

# Automatically sync only changed documents
await sync.sync_directory("./documents")
```

**Features:**
- ✅ Automatic change detection
- ✅ Incremental vector store updates
- ✅ Custom text splitters
- ✅ Batch processing

</td>
<td width="50%" valign="top">

### 🦙 LlamaIndex

```python
from ragversion.integrations.llamaindex import LlamaIndexSync
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

sync = LlamaIndexSync(
    tracker=tracker,
    node_parser=SentenceSplitter(
        chunk_size=1024
    ),
    index=vector_index
)

# Keep your index in sync effortlessly
await sync.sync_directory("./documents")
```

**Features:**
- ✅ Native LlamaIndex integration
- ✅ Node-level tracking
- ✅ Custom node parsers
- ✅ Async operations

</td>
</tr>
</table>

### 🎯 Custom Integrations

RAGVersion's modular design makes it easy to integrate with any RAG framework:

```python
from ragversion import AsyncVersionTracker

async def custom_sync(tracker, documents_path):
    result = await tracker.track_directory(documents_path)

    for change in result.successful:
        if change.change_type in ["created", "modified"]:
            # Your custom processing logic
            await process_document(change.document)
```

---

## 🖥️ CLI

RAGVersion includes a powerful command-line interface for managing document versions:

<table>
<tr>
<td width="50%">

### 📋 Basic Commands

```bash
# Initialize a new project
ragversion init

# Track files or directories
ragversion track ./documents

# List tracked documents
ragversion list

# Run database migrations
ragversion migrate
```

</td>
<td width="50%">

### 🔍 Version Management

```bash
# View document history
ragversion history <document-id>

# Get document diff between versions
ragversion diff <document-id> --versions 1 2

# Show version details
ragversion show <version-id>
```

</td>
</tr>
</table>

### 💡 CLI Examples

```bash
# Track all PDFs in a directory recursively
ragversion track ./documents --pattern "*.pdf" --recursive

# List recently changed documents
ragversion list --recent 10

# Export version history
ragversion export --format json --output history.json

# Show configuration
ragversion config show
```

<details>
<summary>📖 See all CLI commands</summary>

```bash
ragversion --help

Commands:
  init        Initialize RAGVersion in the current directory
  track       Track files or directories for changes
  list        List tracked documents
  history     Show version history for a document
  diff        Show differences between versions
  show        Show detailed version information
  migrate     Run database migrations
  config      Manage configuration
  export      Export version history
  import      Import version history
  status      Show tracking status
  validate    Validate configuration
```

</details>

---

## 🖥️ Web Interface

RAGVersion includes a simple, clean web interface perfect for content teams and non-technical users:

```bash
# Start the server (includes web UI + REST API)
ragversion serve

# Access the web interface
# Dashboard: http://localhost:6699/
# Documents: http://localhost:6699/documents
```

**Web UI Features:**
- 📊 **Dashboard** - Statistics overview, top documents, file type distribution
- 📄 **Document Browser** - Search, filter, and browse all tracked documents
- 📈 **Version History** - View complete version timeline for each document
- 🔍 **Visual Diff Viewer** - Compare versions with color-coded changes
- 🎨 **Clean Design** - Modern, responsive interface with intuitive navigation
- 🚀 **Fast & Lightweight** - Server-side rendering, no heavy JavaScript frameworks

**Perfect for:**
- Content managers who need to track document changes visually
- Non-technical stakeholders who want quick insights
- Teams that prefer web interfaces over command-line tools
- Quick browsing and searching through document history

**Screenshots:**

<table>
<tr>
<td width="50%">

**Dashboard View:**
- Total documents, versions, storage used
- Recent activity metrics
- Top documents by version count
- File type distribution chart

</td>
<td width="50%">

**Document Detail:**
- Complete version history
- Change statistics and frequency
- Visual badges for change types
- Version comparison links

</td>
</tr>
</table>

---

## 🌐 REST API

RAGVersion also provides a comprehensive REST API for programmatic access from any language or platform:

```bash
# Start the API server (same command as web UI)
ragversion serve

# Custom host and port
ragversion serve --host localhost --port 5000

# Development mode with auto-reload
ragversion serve --reload
```

**API Features:**
- 🚀 **FastAPI-based** - Modern async web framework
- 📖 **Auto documentation** - Swagger UI at `/api/docs`, ReDoc at `/api/redoc`
- 🔐 **Optional auth** - API key authentication via `X-API-Key` header
- 🌍 **CORS support** - Configurable cross-origin requests
- ⚡ **Async operations** - Non-blocking request handling
- ✅ **Type validation** - Automatic request/response validation with Pydantic

### Quick API Examples

<table>
<tr>
<td width="50%">

**Python:**
```python
import requests

BASE_URL = "http://localhost:6699/api"

# Track a file
response = requests.post(
    f"{BASE_URL}/track/file",
    json={"file_path": "/path/to/doc.pdf"}
)
event = response.json()

# List documents
docs = requests.get(
    f"{BASE_URL}/documents?limit=10"
).json()

# Get statistics
stats = requests.get(
    f"{BASE_URL}/statistics"
).json()
```

</td>
<td width="50%">

**JavaScript:**
```javascript
const BASE_URL = "http://localhost:6699/api";

// Track a file
const response = await fetch(
  `${BASE_URL}/track/file`,
  {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      file_path: "/path/to/doc.pdf"
    })
  }
);
const event = await response.json();

// Get version history
const versions = await fetch(
  `${BASE_URL}/versions/document/${docId}`
).then(r => r.json());
```

</td>
</tr>
</table>

**cURL Examples:**
```bash
# Track directory
curl -X POST http://localhost:6699/api/track/directory \
  -H "Content-Type: application/json" \
  -d '{"dir_path": "/docs", "patterns": ["*.md"]}'

# Get diff between versions
curl "http://localhost:6699/api/versions/document/<doc-id>/diff/1/3"

# Health check
curl http://localhost:6699/api/health
```

**API Endpoints:**
- `/api/documents` - Document management (list, get, search, delete)
- `/api/versions` - Version management (list, get, content, diff, restore)
- `/api/track` - Tracking operations (file, directory)
- `/api/statistics` - Analytics and statistics
- `/api/health` - Server health check

See the [API Guide](docs/API_GUIDE.md) for complete documentation.

---

## ⏰ Batch Processing & Automation

### Cron Job Example

Create a scheduled sync script:

```python
#!/usr/bin/env python3
"""sync_documents.py - Cron job to sync documents"""

import asyncio
import logging
from ragversion import AsyncVersionTracker, SupabaseStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_documents():
    """Sync all documents in the directory"""
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env()
    )

    result = await tracker.track_directory(
        "./documents",
        patterns=["*.pdf", "*.docx"],
        recursive=True
    )

    logger.info(f"✅ Synced {len(result.successful)} documents")

    if result.failed:
        logger.error(f"❌ Failed to process {len(result.failed)} documents")
        for error in result.failed:
            logger.error(f"  - {error.file_path}: {error.error}")

if __name__ == "__main__":
    asyncio.run(sync_documents())
```

### Schedule with Crontab

```bash
# Edit crontab
crontab -e

# Add this line to sync every hour
0 * * * * /path/to/venv/bin/python /path/to/sync_documents.py >> /var/log/ragversion.log 2>&1

# Or sync every 15 minutes
*/15 * * * * /path/to/venv/bin/python /path/to/sync_documents.py >> /var/log/ragversion.log 2>&1
```

### Use with GitHub Actions

```yaml
name: Sync Documents

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install ragversion[all]
      - name: Sync documents
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: ragversion track ./documents
```

---

## 🏗️ Architecture

RAGVersion follows a modular, async-first architecture designed for production systems:

```
┌─────────────────────────────────────────────────────────────┐
│                    AsyncVersionTracker                      │
│                    (Core Tracking Engine)                   │
└─────────────────┬───────────────────────────┬───────────────┘
                  │                           │
    ┌─────────────▼──────────┐   ┌───────────▼────────────┐
    │   Storage Backends     │   │   Document Parsers     │
    │  - Supabase (current)  │   │  - PDF, DOCX, TXT      │
    │  - PostgreSQL (future) │   │  - Markdown, CSV       │
    │  - SQLite (future)     │   │  - Pluggable system    │
    └────────────────────────┘   └────────────────────────┘
                  │
    ┌─────────────▼──────────────────────────┐
    │         Core Components                │
    │  • Change Detector (hashing & diffs)   │
    │  • Event System (async callbacks)      │
    │  • Batch Processor (error handling)    │
    │  • Compression & Storage optimization  │
    └────────────────────────────────────────┘
```

### Key Components

| Component | Description | Status |
|-----------|-------------|--------|
| **AsyncVersionTracker** | Core tracking engine with async/await support | ✅ Stable |
| **Storage Backends** | Abstract storage interface (Supabase implemented) | ✅ Stable |
| **Document Parsers** | Pluggable parsers for various file formats | ✅ Stable |
| **Change Detector** | Content hashing and intelligent diff generation | ✅ Stable |
| **Event System** | Async callbacks for change notifications | ✅ Stable |
| **Batch Processor** | Resilient batch processing with error recovery | ✅ Stable |

---

## 🛡️ Error Handling

RAGVersion uses a **continue-on-error** approach designed for production resilience:

```python
result = await tracker.track_directory("./documents")

# Detailed error reporting
print(f"✅ Successful: {len(result.successful)}")
print(f"❌ Failed: {len(result.failed)}")

# Handle failures gracefully
if result.failed:
    for error in result.failed:
        print(f"Failed: {error.file_path}")
        print(f"Reason: {error.error}")
        print(f"Type: {error.error_type}")  # "parsing" | "storage" | "unknown"

        # Retry logic for specific error types
        if error.error_type == "parsing":
            # Handle parsing errors
            pass
        elif error.error_type == "storage":
            # Handle storage errors
            pass
```

### Error Types

| Error Type | Description | Recommended Action |
|------------|-------------|-------------------|
| `parsing` | Failed to parse document content | Check file format, update parsers |
| `storage` | Failed to save to database | Check connection, retry |
| `validation` | Invalid configuration or input | Fix configuration |
| `unknown` | Unexpected error | Review logs, report issue |

---

## 🧪 Testing

RAGVersion includes testing utilities for integration tests:

```python
from ragversion.testing import MockStorage, create_sample_documents

async def test_integration():
    # Use in-memory mock storage for testing
    tracker = AsyncVersionTracker(storage=MockStorage())

    # Generate sample test documents
    docs = create_sample_documents(count=10, file_type="pdf")

    # Test your integration
    results = []
    for doc in docs:
        result = await tracker.track(doc.path)
        results.append(result)

    # Assertions
    assert len(results) == 10
    assert all(r.change_type == "created" for r in results)
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=ragversion --cov-report=html

# Run specific test file
pytest tests/test_tracker.py
```

---

## 📚 Documentation

<table>
<tr>
<td width="50%">

### 📖 Complete Guide

**[DOCUMENTATION.md](DOCUMENTATION.md)** - Comprehensive documentation covering:
- ✅ Complete feature walkthrough
- ✅ Integration guides (LangChain, LlamaIndex)
- ✅ API reference
- ✅ Advanced use cases
- ✅ Best practices
- ✅ Troubleshooting
- ✅ Architecture deep dive

</td>
<td width="50%">

### 🚀 Roadmap

**[future-enhancements.md](future-enhancements.md)** - What's coming next:
- 🔮 New framework integrations
- 🔮 Storage backend expansions
- 🔮 Advanced document parsers
- 🔮 Enterprise features
- 🔮 Performance optimizations
- 🔮 Security enhancements

</td>
</tr>
</table>

---

## 💼 Use Cases

<details>
<summary><b>📚 Documentation Versioning</b></summary>

Track changes to documentation sites and keep chatbots up-to-date:

```python
# Monitor docs directory and update vector store
async def monitor_docs():
    tracker = AsyncVersionTracker(storage=SupabaseStorage.from_env())
    sync = LangChainSync(tracker=tracker, vectorstore=qdrant)

    while True:
        result = await sync.sync_directory("./docs")
        print(f"Updated {len(result.successful)} documents")
        await asyncio.sleep(300)  # Check every 5 minutes
```

</details>

<details>
<summary><b>🤖 AI Chatbot Knowledge Base</b></summary>

Maintain fresh knowledge bases for AI assistants:

```python
# Sync changed documents to chatbot's knowledge base
async def update_chatbot_kb():
    tracker = AsyncVersionTracker(storage=SupabaseStorage.from_env())
    result = await tracker.track_directory("./knowledge-base")

    for change in result.successful:
        if change.change_type in ["created", "modified"]:
            await chatbot.update_knowledge(change.document)
```

</details>

<details>
<summary><b>📊 Data Pipeline Monitoring</b></summary>

Track document changes in data processing pipelines:

```python
# Monitor source documents and trigger pipeline
async def pipeline_monitor():
    tracker = AsyncVersionTracker(storage=SupabaseStorage.from_env())

    result = await tracker.track_directory("./data/input")

    # Trigger processing only for changed files
    for change in result.successful:
        if change.change_type != "unchanged":
            await trigger_pipeline(change.document)
```

</details>

<details>
<summary><b>🔍 Compliance & Audit Trails</b></summary>

Maintain complete audit trails of document changes:

```python
# Track all changes with full history
async def audit_documents():
    tracker = AsyncVersionTracker(storage=SupabaseStorage.from_env())

    # Get complete version history
    history = await tracker.get_history(document_id)

    for version in history:
        print(f"{version.timestamp}: {version.change_type}")
        print(f"Content hash: {version.content_hash}")
```

</details>

---

## ⚡ Performance

RAGVersion is built for production scale:

| Metric | Performance |
|--------|-------------|
| **Batch Processing** | 100+ docs/second |
| **Memory Footprint** | < 50MB base |
| **Storage Overhead** | ~10% (with compression) |
| **Async Operations** | Non-blocking I/O |
| **Scalability** | Horizontal scaling ready |

### Optimization Tips

```python
# Use batch processing for large directories
result = await tracker.track_directory(
    "./documents",
    batch_size=50,  # Process 50 files at a time
    max_workers=4   # Use 4 parallel workers
)

# Enable compression to reduce storage
tracker = AsyncVersionTracker(
    storage=SupabaseStorage.from_env(),
    compression="gzip"  # or "zstd" for better compression
)
```

---

## 📋 Requirements

- **Python:** 3.9+
- **Database:** Supabase account (free tier available at [supabase.com](https://supabase.com))
- **Optional:** Redis for caching (future feature)

---

## 📜 License

RAGVersion is released under the **MIT License**. See [LICENSE](LICENSE) file for details.

```
MIT License - Free for personal and commercial use
✅ Private use   ✅ Commercial use   ✅ Modification   ✅ Distribution
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

<table>
<tr>
<td width="33%" align="center">

### 🐛 Report Bugs
Found a bug?
[Open an issue](https://github.com/sourangshupal/ragversion/issues/new)

</td>
<td width="33%" align="center">

### ✨ Request Features
Have an idea?
[Start a discussion](https://github.com/sourangshupal/ragversion/discussions)

</td>
<td width="33%" align="center">

### 🔧 Submit PRs
Want to contribute code?
[Read guidelines](CONTRIBUTING.md)

</td>
</tr>
</table>

**Quick Links:**
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CONTRIBUTING.md#code-of-conduct)
- [Development Setup](CONTRIBUTING.md#development-setup)
- [Architecture Guide](DOCUMENTATION.md#architecture)

---

## 🌟 Show Your Support

If you find RAGVersion helpful, please consider:

- ⭐ **Starring** this repository
- 🐦 **Sharing** on social media
- 📝 **Writing** a blog post about your experience
- 💬 **Contributing** to discussions
- 🐛 **Reporting** bugs or suggesting features

---

## 📞 Support & Community

<table>
<tr>
<td width="25%" align="center">

### 📖 Documentation
[Read Docs](DOCUMENTATION.md)

</td>
<td width="25%" align="center">

### 🐛 Issues
[Report Bug](https://github.com/sourangshupal/ragversion/issues)

</td>
<td width="25%" align="center">

### 💬 Discussions
[Join Discussion](https://github.com/sourangshupal/ragversion/discussions)

</td>
<td width="25%" align="center">

### 📦 PyPI
[View Package](https://pypi.org/project/ragversion/)

</td>
</tr>
</table>

---

## 🗺️ Roadmap

Check out our [detailed roadmap](future-enhancements.md) to see what's coming next!

**High Priority Features:**
- 🔄 Real-time file watching
- 💾 SQLite & PostgreSQL backends
- 🔗 Haystack & Weaviate integrations
- 🌐 REST API server
- 🖥️ Web UI dashboard
- 🔒 Enterprise security features

---

## 📊 Project Stats

![GitHub repo size](https://img.shields.io/github/repo-size/sourangshupal/ragversion)
![GitHub code size](https://img.shields.io/github/languages/code-size/sourangshupal/ragversion)
![Lines of code](https://img.shields.io/tokei/lines/github/sourangshupal/ragversion)

---

<div align="center">

**Made with ❤️ by the RAGVersion Team**

[⭐ Star on GitHub](https://github.com/sourangshupal/ragversion) • [📦 Install from PyPI](https://pypi.org/project/ragversion/) • [📖 Read the Docs](DOCUMENTATION.md)

</div>

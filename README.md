# RAGVersion

**Async-first version tracking system for RAG applications**

RAGVersion is a plug-and-play module that tracks document changes and integrates seamlessly with LangChain, LlamaIndex, and other RAG frameworks. It provides automatic version control, change detection, and content diffing for your document pipelines.

## Features

- 🚀 **Async-first architecture** - Built for modern Python async/await patterns
- 📦 **Plug-and-play** - Works with any RAG system
- 🔄 **Batch processing** - Efficiently process large document collections
- 💾 **Supabase integration** - Primary storage backend with PostgreSQL
- 📝 **Document parsing** - Supports PDF, DOCX, TXT, Markdown, and more
- 🔍 **Change detection** - Automatic tracking with content hashing
- 🔗 **Framework integrations** - Ready-to-use helpers for LangChain & LlamaIndex
- 🛡️ **Resilient** - Continue-on-error design for production systems

## Installation

```bash
# Basic installation
pip install ragversion

# With all parsers
pip install ragversion[parsers]

# With LangChain integration
pip install ragversion[langchain]

# With LlamaIndex integration
pip install ragversion[llamaindex]

# Everything
pip install ragversion[all]
```

## Quick Start

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage

async def main():
    # Initialize tracker
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env()
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

    print(f"Processed: {len(result.successful)} files")
    print(f"Failed: {len(result.failed)} files")

asyncio.run(main())
```

## Configuration

Create a `ragversion.yaml` file:

```yaml
storage:
  backend: supabase
  supabase:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_SERVICE_KEY}

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

Or use environment variables:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

## Integrations

### LangChain

```python
from ragversion.integrations.langchain import LangChainSync
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant

sync = LangChainSync(
    tracker=tracker,
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000),
    embeddings=OpenAIEmbeddings(),
    vectorstore=qdrant_client
)

await sync.sync_directory("./documents")
```

### LlamaIndex

```python
from ragversion.integrations.llamaindex import LlamaIndexSync
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

sync = LlamaIndexSync(
    tracker=tracker,
    node_parser=SentenceSplitter(chunk_size=1024),
    index=vector_index
)

await sync.sync_directory("./documents")
```

## CLI

```bash
# Initialize a new project
ragversion init

# Track files
ragversion track ./documents

# List tracked documents
ragversion list

# View document history
ragversion history <document-id>

# Get document diff
ragversion diff <document-id> --versions 1 2

# Run migrations
ragversion migrate
```

## Batch Processing for Cron Jobs

```python
#!/usr/bin/env python3
"""Cron job to sync documents"""

import asyncio
from ragversion import AsyncVersionTracker, SupabaseStorage

async def sync_documents():
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env()
    )

    result = await tracker.track_directory(
        "./documents",
        patterns=["*.pdf", "*.docx"],
        recursive=True
    )

    print(f"Synced {len(result.successful)} documents")

    for error in result.failed:
        print(f"Error: {error.file_path} - {error.error}")

if __name__ == "__main__":
    asyncio.run(sync_documents())
```

Add to crontab:
```bash
0 * * * * /path/to/venv/bin/python /path/to/sync_documents.py
```

## Architecture

RAGVersion follows an async-first architecture:

- **AsyncVersionTracker** - Core tracking engine
- **Storage Backends** - Abstract interface with Supabase implementation
- **Document Parsers** - Pluggable parsers for different file types
- **Change Detector** - Content hashing and diff generation
- **Event System** - Async callbacks for change notifications
- **Batch Processor** - Resilient batch processing with error handling

## Error Handling

RAGVersion uses a continue-on-error approach for batch operations:

```python
result = await tracker.track_directory("./documents")

# Check for failures
if result.failed:
    for error in result.failed:
        print(f"Failed: {error.file_path}")
        print(f"Error: {error.error}")
        print(f"Type: {error.error_type}")  # "parsing" | "storage" | "unknown"
```

## Testing

```python
from ragversion.testing import MockStorage, create_sample_documents

async def test_integration():
    # Use mock storage for testing
    tracker = AsyncVersionTracker(storage=MockStorage())

    # Create sample documents
    docs = create_sample_documents(count=10, file_type="pdf")

    # Test your integration
    for doc in docs:
        await tracker.track(doc.path)
```

## Documentation

📚 **Complete documentation available in [DOCUMENTATION.md](DOCUMENTATION.md)**

This comprehensive guide covers:
- Complete feature walkthrough
- Integration guides (LangChain, LlamaIndex)
- API reference
- Advanced use cases
- Best practices
- Troubleshooting
- Architecture deep dive

## Requirements

- Python 3.9+
- Supabase account (for primary storage backend)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- GitHub Issues: https://github.com/sourangshupal/ragversion/issues
- Documentation: See [DOCUMENTATION.md](DOCUMENTATION.md)
- PyPI: https://pypi.org/project/ragversion/

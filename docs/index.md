# RAGVersion

**Async-first version tracking system for RAG applications**

RAGVersion solves the critical problem of keeping vector databases synchronized with changing source documents in Retrieval-Augmented Generation (RAG) applications.

## Why RAGVersion?

When building RAG applications, you face a challenge: **documents change, but vector databases don't update automatically**. RAGVersion provides:

- ✅ **Automatic change detection** - Know exactly which documents changed
- ✅ **Version history** - Complete audit trail of all changes
- ✅ **Cost optimization** - Only re-index changed documents (99% cost reduction)
- ✅ **Production-ready** - Resilient error handling and async architecture
- ✅ **Framework integrations** - Works with LangChain, LlamaIndex, and custom pipelines

## Quick Start

Install RAGVersion:

```bash
pip install ragversion
```

Track your documents:

```python
import asyncio
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage

async def main():
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env()
    )

    # Track a directory
    result = await tracker.track_directory(
        "./documents",
        patterns=["*.pdf", "*.docx"],
        recursive=True
    )

    print(f"Changes detected: {result.success_count}")

asyncio.run(main())
```

## Key Features

### 🚀 Async-First Architecture
Built from the ground up for Python's async/await patterns, enabling efficient concurrent processing.

### 📊 Change Detection
Automatic content-based change detection using hashing - no manual tracking needed.

### 🔄 Batch Processing
Process thousands of documents efficiently with parallel workers and resilient error handling.

### 🗄️ Supabase Integration
Reliable PostgreSQL-backed storage with Supabase for production deployments.

### 🔗 Framework Integrations
Ready-to-use helpers for:
- **LangChain** - Sync with LangChain vector stores
- **LlamaIndex** - Sync with LlamaIndex indexes
- **Custom** - Build your own integrations

### 📝 Complete Documentation
15,000+ words of comprehensive documentation covering:
- Installation and setup
- Core concepts
- API reference
- Integration guides
- Best practices
- Troubleshooting

## The Problem RAGVersion Solves

### Without RAGVersion ❌
```
Documents change → Don't know which ones → Re-index everything →
Expensive API calls → Slow updates → Or risk serving stale data
```

### With RAGVersion ✅
```
Documents change → Automatic detection → Only re-index changed docs →
99% cost savings → Fast updates → Always fresh data
```

## Real-World Impact

| Metric | Without RAGVersion | With RAGVersion |
|--------|-------------------|-----------------|
| **Cost** | $50 per update | $0.50 per update |
| **Time** | 33 minutes | 20 seconds |
| **Files processed** | 1,000 (all) | 10 (only changed) |
| **Savings** | - | **99% reduction** |

## Use Cases

- 📚 **Documentation Sites** - Keep docs in sync with latest changes
- 💬 **Customer Support** - Always use up-to-date product information
- 🏢 **Enterprise Knowledge Bases** - Track document changes for compliance
- 🔬 **Research Systems** - Version control for research papers and datasets
- 📊 **Content Management** - Track changes across large content libraries

## Installation Options

```bash
# Basic installation
pip install ragversion

# With document parsers (PDF, DOCX, etc.)
pip install "ragversion[parsers]"

# With LangChain integration
pip install "ragversion[langchain]"

# With LlamaIndex integration
pip install "ragversion[llamaindex]"

# Everything (recommended)
pip install "ragversion[all]"
```

## Next Steps

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } __Getting Started__

    ---

    Install RAGVersion and track your first document in 5 minutes

    [:octicons-arrow-right-24: Installation Guide](getting-started/installation.md)

-   :material-book-open-variant:{ .lg .middle } __User Guide__

    ---

    Learn core concepts and how to use RAGVersion effectively

    [:octicons-arrow-right-24: Core Concepts](guide/core-concepts.md)

-   :material-connection:{ .lg .middle } __Integrations__

    ---

    Integrate with LangChain, LlamaIndex, or build custom integrations

    [:octicons-arrow-right-24: Integration Guides](integrations/langchain.md)

-   :material-code-tags:{ .lg .middle } __API Reference__

    ---

    Detailed API documentation for all components

    [:octicons-arrow-right-24: API Docs](api/tracker.md)

</div>

## Community & Support

- 🐛 [Report Issues](https://github.com/sourangshupal/ragversion/issues) - Bug reports and feature requests
- 💬 [Discussions](https://github.com/sourangshupal/ragversion/discussions) - Ask questions and share ideas
- 📦 [PyPI Package](https://pypi.org/project/ragversion/) - Install from PyPI
- 🌟 [GitHub Repository](https://github.com/sourangshupal/ragversion) - Star the project

## License

RAGVersion is licensed under the [MIT License](https://github.com/sourangshupal/ragversion/blob/main/LICENSE).

---

**Built with ❤️ for the RAG community**

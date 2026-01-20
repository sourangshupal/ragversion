# RAGVersion Examples

This directory contains examples demonstrating different use cases and features of RAGVersion.

## Quick Start

**Absolute Beginner** (Never used RAGVersion before):
- Start with: `hello_world.py` (15 lines, tracks one file)

**Framework Integration** (Using LangChain/LlamaIndex):
- See: `quick_start_langchain.py` or `quick_start_llamaindex.py`

**Advanced Usage**:
- `basic_usage.py` - Manual configuration and tracking
- `file_watching.py` - Real-time file monitoring
- `batch_processing.py` - Processing directories with patterns

## Running Examples

### 1. Install RAGVersion

```bash
pip install ragversion
```

### 2. Run Any Example

```bash
# Start with the simplest example
python examples/hello_world.py

# Try directory tracking
python examples/basic_usage.py

# Watch files for changes
python examples/file_watching.py
```

### 3. Framework Integrations

For LangChain or LlamaIndex integrations, install the extras:

```bash
# For LangChain
pip install ragversion[langchain]
python examples/quick_start_langchain.py

# For LlamaIndex
pip install ragversion[llamaindex]
python examples/quick_start_llamaindex.py
```

## Example Descriptions

### `hello_world.py`
**What it does**: Tracks a single file (README.md) with minimal setup.

**When to use**: Your first RAGVersion script, learning the basics.

**Key concepts**: Factory method, context manager, basic tracking.

---

### `basic_usage.py`
**What it does**: Demonstrates manual configuration and tracking multiple files.

**When to use**: Understanding tracker configuration options.

**Key concepts**: Custom configuration, directory tracking, file patterns.

---

### `file_watching.py`
**What it does**: Monitors a directory for file changes in real-time.

**When to use**: Building applications that react to file system changes.

**Key concepts**: FileWatcher, callbacks, real-time monitoring.

---

### `batch_processing.py`
**What it does**: Efficiently processes large directories with concurrency control.

**When to use**: Tracking large document collections.

**Key concepts**: Batch processing, error handling, progress tracking.

---

### `quick_start_langchain.py`
**What it does**: Integrates RAGVersion with LangChain vector stores (3-line setup).

**When to use**: Building RAG applications with LangChain.

**Key concepts**: LangChain integration, automatic sync, embeddings management.

**Requirements**: `pip install ragversion[langchain]` + OpenAI API key

---

### `quick_start_llamaindex.py`
**What it does**: Integrates RAGVersion with LlamaIndex (3-line setup).

**When to use**: Building RAG applications with LlamaIndex.

**Key concepts**: LlamaIndex integration, automatic sync, index updates.

**Requirements**: `pip install ragversion[llamaindex]` + OpenAI API key

---

## Common Patterns

### Track a Single File
```python
import asyncio
from ragversion import AsyncVersionTracker

async def main():
    async with await AsyncVersionTracker.create() as tracker:
        event = await tracker.track("document.pdf")
        if event:
            print(f"Tracked version {event.version_number}")

asyncio.run(main())
```

### Track a Directory
```python
async with await AsyncVersionTracker.create() as tracker:
    result = await tracker.track_directory("./documents")
    print(f"Tracked {result.successful_count} files")
```

### Track Specific File Types
```python
async with await AsyncVersionTracker.create() as tracker:
    result = await tracker.track_directory(
        "./documents",
        patterns=["*.pdf", "*.docx"]
    )
```

### Use Callbacks
```python
def on_change(event):
    print(f"File changed: {event.file_name}")

async with await AsyncVersionTracker.create() as tracker:
    tracker.on_change(on_change)
    result = await tracker.track_directory("./documents")
```

## Need Help?

- **Documentation**: See [docs/](../docs/) for detailed guides
- **Troubleshooting**: Check [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) (if available)
- **Issues**: [GitHub Issues](https://github.com/sourangshupal/ragversion/issues)
- **Tutorials**: Start with [5-Minute Tutorial](../docs/5-MINUTE-TUTORIAL.md) (if available)

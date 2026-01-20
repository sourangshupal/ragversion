# LlamaIndex Integration

RAGVersion provides seamless integration with LlamaIndex, making it easy to keep your indexes in sync with document changes.

## Quick Start (Recommended)

**NEW in v0.11.0**: One-line setup!

```python
from ragversion.integrations.llamaindex import quick_start

# That's it! 🚀
sync = await quick_start("./documents")

# Ready to query
query_engine = sync.index.as_query_engine()
response = query_engine.query("What are the features?")
```

**What this does:**
- ✅ Creates RAGVersion tracker with smart defaults
- ✅ Initializes VectorStoreIndex
- ✅ Sets up OpenAI embeddings
- ✅ Configures node parser
- ✅ Indexes your documents
- ✅ Enables chunk-level tracking for 80-95% cost savings

See the [Quick Start Guide](../QUICK_START_GUIDE.md) for more details.

## Customization

### Custom Configuration

```python
sync = await quick_start(
    directory="./documents",
    storage_backend="supabase",      # or "sqlite", "auto"
    chunk_size=2048,                 # Custom chunk size
    chunk_overlap=200,               # Custom overlap
    enable_chunk_tracking=True,      # Smart updates (default)
)
```

### Custom Embeddings

```python
from llama_index.embeddings.openai import OpenAIEmbedding

embeddings = OpenAIEmbedding(model="text-embedding-3-small")
sync = await quick_start("./documents", embeddings=embeddings)
```

### File Patterns

```python
sync = await quick_start(
    directory="./documents",
    file_patterns=["*.pdf", "*.docx", "*.txt", "*.md"],
)
```

## Advanced Usage

### Manual Setup (For Full Control)

If you need complete control over the setup:

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage
from ragversion.integrations.llamaindex import LlamaIndexSync

# Setup storage
storage = SQLiteStorage()
tracker = AsyncVersionTracker(storage=storage)
await tracker.initialize()

# Setup LlamaIndex components
embeddings = OpenAIEmbedding()
node_parser = SentenceSplitter(
    chunk_size=1024,
    chunk_overlap=20,
)
index = VectorStoreIndex.from_documents([], embed_model=embeddings)

# Create sync
sync = LlamaIndexSync(
    tracker=tracker,
    index=index,
    node_parser=node_parser,
    enable_chunk_tracking=True,  # Enable smart updates
)

# Sync directory
await sync.sync_directory("./documents")
```

### Using the Sync Integration

```python
# Query the index
query_engine = sync.index.as_query_engine()
response = query_engine.query("What changed today?")

# Use as retriever
retriever = sync.index.as_retriever(similarity_top_k=5)
nodes = retriever.retrieve("sample query")

# Track new files (auto-updates index)
await sync.tracker.track("./new_doc.pdf")

# Custom metadata extraction
def extract_metadata(file_path):
    return {"source": "internal", "department": "engineering"}

sync = LlamaIndexSync(
    tracker=tracker,
    index=index,
    node_parser=node_parser,
    metadata_extractor=extract_metadata,
)
```

## Smart Chunk-Level Tracking

When `enable_chunk_tracking=True` (default), RAGVersion only re-embeds changed chunks on document updates, achieving **80-95% cost savings** compared to full re-embedding.

```python
sync = await quick_start(
    directory="./documents",
    enable_chunk_tracking=True,  # Default
)

# Update a document
await sync.tracker.track("./documents/updated.pdf")
# Only changed chunks are re-embedded!
```

## Examples

- [Quick Start Example](../../examples/quick_start_llamaindex.py)
- [Basic Integration](../../examples/llamaindex_integration.py)
- [Complete How-to Guide](../../How_to.md)

## API Reference

### `quick_start()`

One-line setup for LlamaIndex integration.

**Parameters:**
- `directory` (str): Directory to track and index
- `index_path` (str, optional): Reserved for future persistence support
- `embeddings` (BaseEmbedding, optional): Custom embeddings model
- `storage_backend` (str): "auto", "sqlite", or "supabase" (default: "auto")
- `chunk_size` (int): Node parser chunk size (default: 1024)
- `chunk_overlap` (int): Node parser overlap (default: 20)
- `file_patterns` (List[str]): File patterns to track (default: ["*.txt", "*.md", "*.pdf"])
- `enable_chunk_tracking` (bool): Enable smart chunk updates (default: True)

**Returns:**
- `LlamaIndexSync`: Initialized sync instance with documents indexed

### `LlamaIndexSync`

Main integration class for automatic synchronization.

**Methods:**
- `sync_directory(dir_path, patterns, recursive)`: Sync all files in directory
- `refresh_index()`: Refresh the entire index from tracked documents
- `_handle_creation(event)`: Handle document creation events
- `_handle_modification(event)`: Handle document modification events
- `_handle_deletion(event)`: Handle document deletion events

See the [complete documentation](../../DOCUMENTATION.md) for detailed API reference.

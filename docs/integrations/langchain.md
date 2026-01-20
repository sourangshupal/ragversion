# LangChain Integration

RAGVersion provides seamless integration with LangChain, making it easy to keep your vector stores in sync with document changes.

## Quick Start (Recommended)

**NEW in v0.11.0**: One-line setup!

```python
from ragversion.integrations.langchain import quick_start

# That's it! 🚀
sync = await quick_start("./documents")

# Ready to query
results = await sync.vectorstore.asimilarity_search("query", k=5)
```

**What this does:**
- ✅ Creates RAGVersion tracker with smart defaults
- ✅ Initializes FAISS vector store
- ✅ Sets up OpenAI embeddings
- ✅ Configures text splitter
- ✅ Syncs your documents
- ✅ Enables chunk-level tracking for 80-95% cost savings

See the [Quick Start Guide](../QUICK_START_GUIDE.md) for more details.

## Customization

### Vector Store Options

```python
# FAISS (in-memory, fast)
sync = await quick_start(
    directory="./documents",
    vectorstore_type="faiss",
    vectorstore_path="./vectorstore",  # Save/load location
)

# Chroma (persistent)
sync = await quick_start(
    directory="./documents",
    vectorstore_type="chroma",
    vectorstore_path="./chroma_db",
)
```

### Custom Configuration

```python
sync = await quick_start(
    directory="./documents",
    vectorstore_type="faiss",
    storage_backend="supabase",      # or "sqlite", "auto"
    chunk_size=500,                  # Custom chunk size
    chunk_overlap=100,               # Custom overlap
    enable_chunk_tracking=True,      # Smart updates (default)
)
```

### Custom Embeddings

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
sync = await quick_start("./documents", embeddings=embeddings)
```

## Advanced Usage

### Manual Setup (For Full Control)

If you need complete control over the setup:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage
from ragversion.integrations.langchain import LangChainSync

# Setup storage
storage = SQLiteStorage()
tracker = AsyncVersionTracker(storage=storage)
await tracker.initialize()

# Setup LangChain components
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(["placeholder"], embeddings)

# Create sync
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True,  # Enable smart updates
)

# Sync directory
await sync.sync_directory("./documents")
```

### Using the Sync Integration

```python
# Query vector store
results = await sync.vectorstore.asimilarity_search("query", k=5)

# Track new files (auto-updates vector store)
await sync.tracker.track("./new_doc.pdf")

# Custom metadata extraction
def extract_metadata(file_path):
    return {"source": "internal", "department": "engineering"}

sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
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

- [Quick Start Example](../../examples/quick_start_langchain.py)
- [Basic Integration](../../examples/langchain_integration.py)
- [Complete How-to Guide](../../How_to.md)

## API Reference

### `quick_start()`

One-line setup for LangChain integration.

**Parameters:**
- `directory` (str): Directory to track and sync
- `vectorstore_type` (str): "faiss" or "chroma" (default: "faiss")
- `vectorstore_path` (str, optional): Path for persistent storage
- `embeddings` (Embeddings, optional): Custom embeddings model
- `storage_backend` (str): "auto", "sqlite", or "supabase" (default: "auto")
- `chunk_size` (int): Text splitter chunk size (default: 1000)
- `chunk_overlap` (int): Text splitter overlap (default: 200)
- `file_patterns` (List[str]): File patterns to track (default: ["*.txt", "*.md", "*.pdf"])
- `enable_chunk_tracking` (bool): Enable smart chunk updates (default: True)

**Returns:**
- `LangChainSync`: Initialized sync instance with documents synced

### `LangChainSync`

Main integration class for automatic synchronization.

**Methods:**
- `sync_directory(dir_path, patterns, recursive)`: Sync all files in directory
- `_handle_creation(event)`: Handle document creation events
- `_handle_modification(event)`: Handle document modification events
- `_handle_deletion(event)`: Handle document deletion events

See the [complete documentation](../../DOCUMENTATION.md) for detailed API reference.

# HuggingFace Embeddings + Chroma Vector Store

**Use case:** Local development, no API costs
**Cost:** Free (runs locally)
**Pros:** No API keys, works offline, persistent storage
**Cons:** Slower on CPU, requires model downloads (~100-500MB)

## Installation

```bash
pip install ragversion[langchain]
pip install sentence-transformers langchain-chroma chromadb
```

## Quick Start

```python
from ragversion.integrations.langchain import quick_start

# Auto-detection will use HuggingFace if sentence-transformers is installed
sync = await quick_start(
    directory="./documents",
    vectorstore_type="chroma",
    embedding_provider="auto",  # Auto-detects HuggingFace
)
```

That's it! RAGVersion will:
1. Auto-detect that `sentence-transformers` is installed
2. Use HuggingFace embeddings with `all-MiniLM-L6-v2` model
3. Create a persistent Chroma database at `./chroma_db`
4. Sync all documents in `./documents`

## Manual Setup (Advanced)

```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage
from ragversion.integrations.langchain import LangChainSync

# Create tracker with SQLite (no Supabase needed)
storage = SQLiteStorage("./ragversion.db")
tracker = AsyncVersionTracker(storage=storage, store_content=True)
await tracker.initialize()

# Create HuggingFace embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},  # Use 'cuda' for GPU
    encode_kwargs={'normalize_embeddings': True}
)

# Create Chroma vectorstore
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
)

# Create text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

# Create sync
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True,
)

# Sync directory
await sync.sync_directory("./documents")
```

## Embedding Model Options

### Fast & Small (Recommended for Most Use Cases)

```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
```
- **Size:** 80MB
- **Speed:** ~500 sentences/second (CPU)
- **Quality:** Good for general use

### Higher Quality

```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)
```
- **Size:** 420MB
- **Speed:** ~300 sentences/second (CPU)
- **Quality:** Better retrieval accuracy

### Multilingual

```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
```
- **Size:** 970MB
- **Speed:** ~200 sentences/second (CPU)
- **Quality:** Supports 50+ languages

### Largest & Best Quality

```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-roberta-large-v1"
)
```
- **Size:** 1.3GB
- **Speed:** ~100 sentences/second (CPU)
- **Quality:** Highest accuracy

## Performance Optimization

### Use GPU for Faster Embeddings

```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cuda'},  # Use GPU
)
```

**Speed comparison:**
- CPU: ~500 sentences/second
- GPU (NVIDIA): ~5000 sentences/second (10x faster!)

### Batch Processing

```python
# Process multiple documents in parallel
await sync.sync_directory(
    "./documents",
    max_workers=8,  # More workers for CPU-bound tasks
)
```

### Pre-download Models

First time usage downloads the model. Pre-download to avoid delays:

```python
from sentence_transformers import SentenceTransformer

# Download model once
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("Model downloaded!")
```

Models are cached in `~/.cache/huggingface/hub/`

## Persistent Chroma Database

Chroma automatically persists data:

```python
# First run - creates database
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
)

# Later runs - loads existing database
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
)
```

### Backup Chroma Database

```bash
# Backup
tar -czf chroma_backup.tar.gz chroma_db/

# Restore
tar -xzf chroma_backup.tar.gz
```

## Querying

```python
# Similarity search
results = await vectorstore.asimilarity_search("What is RAGVersion?", k=5)

for doc in results:
    print(f"Content: {doc.page_content}")
    print(f"Source: {doc.metadata['file_path']}")
    print("---")

# With metadata filter
results = await vectorstore.asimilarity_search(
    "API documentation",
    k=5,
    filter={"file_name": {"$regex": ".*\\.md$"}}  # Only markdown files
)
```

## Offline Usage

HuggingFace embeddings work completely offline after initial model download:

```python
# 1. Download model once (requires internet)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 2. Use offline (no internet required)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
```

Perfect for:
- Air-gapped systems
- Development on planes/trains
- Privacy-sensitive applications

## Local-First Architecture

Completely self-contained setup with no external dependencies:

```python
from ragversion.integrations.langchain import quick_start

# Everything runs locally
sync = await quick_start(
    directory="./documents",
    vectorstore_type="chroma",
    embedding_provider="huggingface",
    storage_backend="sqlite",  # Local SQLite instead of Supabase
)
```

**No external services needed:**
- ✓ Embeddings: HuggingFace (local)
- ✓ Vector store: Chroma (local)
- ✓ Version storage: SQLite (local)
- ✓ Works completely offline

## Memory Usage

```python
import psutil
import os

# Monitor memory usage
process = psutil.Process(os.getpid())
print(f"Memory before: {process.memory_info().rss / 1024 / 1024:.2f} MB")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print(f"Memory after: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

**Typical memory usage:**
- `all-MiniLM-L6-v2`: ~200MB RAM
- `all-mpnet-base-v2`: ~500MB RAM
- `all-roberta-large-v1`: ~1.5GB RAM

## Switching from OpenAI to HuggingFace

Already using OpenAI? Easy migration:

```python
# Before (OpenAI)
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()

# After (HuggingFace)
from langchain_community.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
```

**Note:** You'll need to re-embed all documents (embeddings are not compatible).

## Troubleshooting

### Model Download Fails

```
Error: HTTPSConnectionPool... Connection refused
```

**Solution:** Check internet connection and retry. Models download to `~/.cache/huggingface/`

### Out of Memory

```
Error: RuntimeError: CUDA out of memory
```

**Solutions:**
1. Use CPU instead of GPU:
   ```python
   model_kwargs={'device': 'cpu'}
   ```
2. Use smaller model (all-MiniLM-L6-v2)
3. Process fewer documents at once (reduce `max_workers`)

### Slow Performance on CPU

**Solutions:**
1. Use GPU if available
2. Use smaller model
3. Reduce chunk size
4. Enable multi-threading:
   ```python
   embeddings = HuggingFaceEmbeddings(
       model_name="sentence-transformers/all-MiniLM-L6-v2",
       encode_kwargs={'batch_size': 32}  # Larger batches
   )
   ```

### Chroma Database Corruption

```
Error: Database disk image is malformed
```

**Solution:** Restore from backup or recreate:
```bash
rm -rf chroma_db/
# Re-sync documents
```

## Comparison: HuggingFace vs OpenAI

| Feature | HuggingFace | OpenAI |
|---------|-------------|---------|
| **Cost** | Free | $0.02-$0.13 per 1M tokens |
| **Speed (CPU)** | ~500 sent/sec | N/A (API) |
| **Speed (GPU)** | ~5000 sent/sec | ~10000 sent/sec (API) |
| **Quality** | Good | Excellent |
| **Offline** | ✓ Yes | ✗ No |
| **Privacy** | ✓ Local | ✗ Sends to API |
| **Setup** | Download model | API key |

## See Also

- [OpenAI + Pinecone](openai_pinecone.md) - Cloud-based alternative
- [Ollama + Qdrant](ollama_qdrant.md) - Alternative local setup
- [Cost Optimization Guide](cost_optimization.md) - General optimization tips

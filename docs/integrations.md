# Embeddings and Vector Store Integrations

This guide helps you choose and configure embeddings and vector stores for RAGVersion.

## Overview

RAGVersion is a **version tracking and sync layer** - it works with ANY LangChain/LlamaIndex compatible embeddings and vector stores. You bring your own components, RAGVersion handles the synchronization.

**Your responsibility:**
- Choose and configure embeddings
- Choose and configure vector store
- Provide text splitter

**RAGVersion's responsibility:**
- Track document changes
- Sync changes to your vector store
- Only re-embed what changed (with chunk tracking)

---

## Choosing Embeddings

### Decision Matrix

| Factor | OpenAI | HuggingFace | Ollama | Cohere |
|--------|--------|-------------|---------|--------|
| **Cost** | $0.02-$0.13/1M tokens | FREE | FREE | $0.10/1M tokens |
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Speed** | Fast (API) | Slow (CPU), Fast (GPU) | Fast (GPU) | Fast (API) |
| **Privacy** | ❌ Sends to API | ✅ Local | ✅ Local | ❌ Sends to API |
| **Offline** | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| **Setup** | API key | `pip install` | Install Ollama | API key |

### Recommendations by Use Case

#### Production / Best Quality
```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```
**Why:** Best quality-to-cost ratio, fast, reliable

#### Privacy-Sensitive / Offline
```python
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
```
**Why:** Runs completely locally, no data leaves your network

#### Development / Testing
```python
# Auto-detection (tries OpenAI → HuggingFace → Ollama)
from ragversion.integrations.langchain import quick_start

sync = await quick_start(
    directory="./documents",
    embedding_provider="auto"
)
```
**Why:** Works without configuration, uses what's available

#### Latest Models / Self-Hosted
```python
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")
```
**Why:** Access to latest open-source models, full control

### All Supported Embeddings

**LangChain:**
- OpenAI (`langchain-openai`)
- HuggingFace (`sentence-transformers` + `langchain-community`)
- Ollama (`ollama` + `langchain-community`)
- Cohere (`langchain-cohere`)
- Google VertexAI (`langchain-google-vertexai`)
- AWS Bedrock (`langchain-aws`)
- Azure OpenAI (`langchain-openai`)
- Anthropic Voyage (`langchain-voyage`)
- Jina (`langchain-community`)
- 60+ more via `langchain-community`

**LlamaIndex:**
- OpenAI (`llama-index-embeddings-openai`)
- HuggingFace (`llama-index-embeddings-huggingface`)
- Ollama (`llama-index-embeddings-ollama`)
- Cohere (`llama-index-embeddings-cohere`)
- Google (`llama-index-embeddings-google`)
- 60+ more via `llama-index-embeddings-*`

**All embeddings that implement the base class interface work automatically.**

---

## Choosing Vector Stores

### Decision Matrix

| Factor | FAISS | Chroma | Pinecone | Qdrant | Weaviate |
|--------|-------|--------|----------|--------|----------|
| **Cost** | FREE | FREE | $70+/mo | FREE (self-hosted) | FREE (self-hosted) |
| **Persistence** | Manual | ✅ Auto | ✅ Cloud | ✅ Auto | ✅ Auto |
| **Scale** | In-memory | 10M+ docs | Billions | Billions | Billions |
| **Setup** | Easy | Easy | API key | Docker/Cloud | Docker/Cloud |
| **Production** | ⚠️ Not recommended | ✅ Good | ✅ Excellent | ✅ Excellent | ✅ Excellent |

### Recommendations by Use Case

#### Development / Quick Start
```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(["placeholder"], embeddings)
```
**Why:** No setup, fast, works out of the box

#### Local Development / Testing
```python
from langchain_chroma import Chroma

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
```
**Why:** Persistent, works offline, zero configuration

#### Production / Managed Service
```python
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

pc = Pinecone(api_key="...")
index = pc.Index("my-index")

vectorstore = PineconeVectorStore(
    index=index,
    embedding=embeddings
)
```
**Why:** Fully managed, scalable, reliable

#### Self-Hosted Production
```python
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

vectorstore = QdrantVectorStore(
    client=client,
    collection_name="my_collection",
    embedding=embeddings
)
```
**Why:** Full control, open source, cost-effective at scale

### All Supported Vector Stores

**LangChain:**
- FAISS (`faiss-cpu` or `faiss-gpu`)
- Chroma (`chromadb` + `langchain-chroma`)
- Pinecone (`pinecone-client` + `langchain-pinecone`)
- Qdrant (`qdrant-client` + `langchain-qdrant`)
- Weaviate (`weaviate-client` + `langchain-weaviate`)
- Milvus (`pymilvus` + `langchain-milvus`)
- Elasticsearch (`elasticsearch` + `langchain-elasticsearch`)
- Redis (`redis` + `langchain-redis`)
- MongoDB Atlas (`pymongo` + `langchain-mongodb`)
- Supabase Vector (via Supabase client)
- 40+ more via LangChain integrations

**LlamaIndex:**
- All of the above via LlamaIndex wrappers
- Same compatibility requirements

---

## Compatibility Requirements

### Vector Store Requirements

To work with RAGVersion, vector stores MUST support:

1. **Async document insertion:**
   ```python
   await vectorstore.aadd_documents(documents: List[Document]) -> List[str]
   ```

2. **Deletion by metadata filter:**
   ```python
   vectorstore.delete(filter: Dict[str, Any]) -> None
   ```

**✅ Compatible:** FAISS, Chroma, Pinecone, Qdrant, Weaviate, Milvus, Elasticsearch

**⚠️ Limited support:** Vector stores without metadata filtering (updates may not work)

### Embeddings Requirements

Embeddings MUST implement:

1. **Embed documents:**
   ```python
   embeddings.embed_documents(texts: List[str]) -> List[List[float]]
   ```

2. **Embed query:**
   ```python
   embeddings.embed_query(text: str) -> List[float]
   ```

**All LangChain/LlamaIndex embeddings meet these requirements.**

### Validation

RAGVersion automatically validates compatibility on initialization:

```python
from ragversion.integrations.langchain import LangChainSync

# Raises TypeError if incompatible
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,  # Validated
    vectorstore=vectorstore,  # Validated
)
```

Error messages provide actionable guidance:
```
TypeError: Vector store 'CustomStore' does not support aadd_documents().

RAGVersion requires LangChain-compatible vector stores with:
  - aadd_documents(documents: List[Document]) -> List[str]
  - delete(filter: Dict[str, Any]) -> None

Supported stores: FAISS, Chroma, Pinecone, Qdrant, Weaviate, etc.
See: https://docs.ragversion.com/integrations/vectorstores
```

---

## Configuration Examples

### Production Stack

```python
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage
from ragversion.integrations.langchain import LangChainSync

# Storage (Supabase)
storage = SupabaseStorage.from_env()

# Tracker
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=True,
    enable_chunk_tracking=True  # 80-95% cost savings
)
await tracker.initialize()

# Embeddings (OpenAI)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Vector Store (Pinecone)
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("production-index")
vectorstore = PineconeVectorStore(index=index, embedding=embeddings)

# Text Splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# Sync
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True
)

# Sync documents
await sync.sync_directory("./documents")
```

### Zero-Cost Local Stack

```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage
from ragversion.integrations.langchain import LangChainSync

# Storage (SQLite - free)
storage = SQLiteStorage("./ragversion.db")

# Tracker
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=True,
    enable_chunk_tracking=True
)
await tracker.initialize()

# Embeddings (HuggingFace - free)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Vector Store (Chroma - free)
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# Text Splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# Sync
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True
)

# 100% free, 100% local!
await sync.sync_directory("./documents")
```

### Quick Start (Auto-Detection)

```python
from ragversion.integrations.langchain import quick_start

# Automatically detects available embeddings and creates vectorstore
sync = await quick_start(
    directory="./documents",
    embedding_provider="auto",  # OpenAI → HuggingFace → Ollama
    vectorstore_type="chroma",  # or "faiss"
)
```

---

## Migration Guide

### Changing Embeddings

**Important:** Embeddings from different models are NOT compatible. You must re-embed all documents.

```python
# Step 1: Clear existing vectorstore
vectorstore.delete(filter={})  # Delete all

# Or create new vectorstore
vectorstore = Chroma(
    persist_directory="./chroma_db_new",
    embedding_function=new_embeddings
)

# Step 2: Create new sync with new embeddings
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=new_embeddings,  # ← New embeddings
    vectorstore=vectorstore,
)

# Step 3: Re-sync all documents
await sync.sync_directory("./documents")
```

### Changing Vector Stores

```python
# Step 1: Create new vectorstore
new_vectorstore = PineconeVectorStore(...)  # New store

# Step 2: Create sync with new vectorstore
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=new_vectorstore,  # ← New vectorstore
)

# Step 3: Re-sync all documents
# Documents will be embedded to new vectorstore
await sync.sync_directory("./documents")
```

### Zero-Downtime Migration

```python
# Run both vectorstores in parallel
sync_old = LangChainSync(..., vectorstore=old_vectorstore)
sync_new = LangChainSync(..., vectorstore=new_vectorstore)

# Sync to both
await sync_old.sync_directory("./documents")
await sync_new.sync_directory("./documents")

# Verify new vectorstore works
results = await new_vectorstore.asimilarity_search("test query", k=5)
assert len(results) > 0

# Switch traffic to new vectorstore
# Decommission old vectorstore
```

---

## Troubleshooting

### "Vector store does not support aadd_documents"

**Cause:** Using incompatible vector store

**Solution:** Use supported vector store (FAISS, Chroma, Pinecone, Qdrant, etc.)

### "Embeddings does not support embed_documents"

**Cause:** Using non-LangChain/LlamaIndex embeddings

**Solution:** Wrap in LangChain/LlamaIndex embeddings class

### "Dimension mismatch"

**Cause:** Vector store dimension doesn't match embeddings

**Solution:** Ensure vector store dimension matches embedding dimension:
- `text-embedding-3-small`: 1536 dimensions
- `text-embedding-3-large`: 3072 dimensions
- `all-MiniLM-L6-v2`: 384 dimensions

### "Rate limit exceeded"

**Cause:** Too many API requests to embeddings provider

**Solution:**
1. Reduce `max_workers` parameter
2. Enable chunk tracking (fewer embeddings)
3. Use local embeddings (HuggingFace/Ollama)

---

## Best Practices

### 1. Always Enable Chunk Tracking

```python
sync = LangChainSync(
    tracker=tracker,
    ...,
    enable_chunk_tracking=True  # 80-95% cost savings
)
```

### 2. Use Metadata Extractors

```python
def metadata_extractor(file_path: str) -> dict:
    return {
        "source": "documentation",
        "team": "engineering",
        "last_updated": datetime.now().isoformat()
    }

sync = LangChainSync(
    ...,
    metadata_extractor=metadata_extractor
)

# Query with filters
results = vectorstore.similarity_search(
    "API docs",
    filter={"team": "engineering"}
)
```

### 3. Monitor Performance

```python
import time

start = time.time()
result = await sync.sync_directory("./documents")
elapsed = time.time() - start

print(f"Synced {result.success_count} documents in {elapsed:.2f}s")
print(f"Average: {result.success_count / elapsed:.2f} docs/sec")
```

### 4. Handle Errors Gracefully

```python
try:
    await sync.sync_directory("./documents")
except RuntimeError as e:
    if "rate limit" in str(e).lower():
        await asyncio.sleep(60)
        await sync.sync_directory("./documents")
    else:
        raise
```

---

## See Also

- [Cookbook Examples](cookbook/) - Production-ready configurations
- [Cost Optimization Guide](cookbook/cost_optimization.md) - Save 80-95% on embeddings
- [LangChain Documentation](https://python.langchain.com/docs/integrations/vectorstores/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/en/stable/module_guides/storing/vector_stores.html)

# Ollama Embeddings + Qdrant Vector Store

**Use case:** Self-hosted setup with large language models
**Cost:** Free (self-hosted)
**Pros:** Latest models, local or cloud deployment, production-ready
**Cons:** Requires Ollama installation, larger resource usage

## Prerequisites

### Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.com](https://ollama.com/download)

### Pull Embedding Model

```bash
# Recommended: Small, fast model
ollama pull nomic-embed-text

# Alternative: Larger, higher quality
ollama pull mxbai-embed-large
```

## Installation

```bash
pip install ragversion[langchain]
pip install ollama langchain-community langchain-qdrant qdrant-client
```

## Quick Start (Local Qdrant)

```python
from ragversion.integrations.langchain import quick_start

# Auto-detection will use Ollama if installed
sync = await quick_start(
    directory="./documents",
    vectorstore_type="faiss",  # Will customize with Qdrant below
    embedding_provider="auto",  # Auto-detects Ollama
)
```

## Manual Setup with Qdrant

### Option 1: Local Qdrant (Docker)

```bash
# Start Qdrant in Docker
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

```python
from langchain_community.embeddings import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ragversion import AsyncVersionTracker
from ragversion.storage import SQLiteStorage
from ragversion.integrations.langchain import LangChainSync

# Create tracker
storage = SQLiteStorage("./ragversion.db")
tracker = AsyncVersionTracker(storage=storage, store_content=True)
await tracker.initialize()

# Create Ollama embeddings
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"  # Default Ollama URL
)

# Create Qdrant client
qdrant_client = QdrantClient(url="http://localhost:6333")

# Create collection
collection_name = "ragversion_docs"

# Create vectorstore
vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name=collection_name,
    embedding=embeddings,
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

### Option 2: Qdrant Cloud

```python
from qdrant_client import QdrantClient

# Connect to Qdrant Cloud
qdrant_client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key",
)

# Rest is the same as local setup
vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name="ragversion_docs",
    embedding=embeddings,
)
```

### Option 3: In-Memory Qdrant (Development)

```python
from qdrant_client import QdrantClient

# In-memory (no persistence)
qdrant_client = QdrantClient(":memory:")

vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name="ragversion_docs",
    embedding=embeddings,
)
```

## Ollama Model Options

### Text Embeddings

```bash
# Recommended: Fast, good quality (270M parameters)
ollama pull nomic-embed-text

# Higher quality, slower (335M parameters)
ollama pull mxbai-embed-large

# Multilingual support
ollama pull paraphrase-multilingual
```

### Using Different Models

```python
# nomic-embed-text (recommended)
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# mxbai-embed-large (higher quality)
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# Custom model
embeddings = OllamaEmbeddings(model="your-custom-model")
```

## Configuration

### Ollama Server Configuration

```python
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",  # Ollama server URL
    temperature=0,  # Deterministic embeddings
)
```

### Remote Ollama Server

```python
# Connect to remote Ollama instance
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://192.168.1.100:11434",  # Remote server
)
```

### Qdrant Configuration

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Create client with custom settings
qdrant_client = QdrantClient(
    url="http://localhost:6333",
    timeout=120,  # Longer timeout for large batches
)

# Create collection with specific vector size
qdrant_client.create_collection(
    collection_name="ragversion_docs",
    vectors_config=VectorParams(
        size=768,  # nomic-embed-text dimension
        distance=Distance.COSINE,
    ),
)
```

## Performance Optimization

### GPU Acceleration

Ollama automatically uses GPU if available:

```bash
# Check GPU usage
ollama list
nvidia-smi  # For NVIDIA GPUs
```

### Batch Size Tuning

```python
# Larger batches for better throughput
await sync.sync_directory(
    "./documents",
    max_workers=4,  # Adjust based on GPU memory
)
```

### Model Quantization

```bash
# Pull quantized model (smaller, faster)
ollama pull nomic-embed-text:q4_0  # 4-bit quantized
```

## Monitoring

### Ollama Server Logs

```bash
# View Ollama logs
ollama logs

# Follow logs
ollama logs -f
```

### Qdrant Metrics

```python
# Check collection info
info = qdrant_client.get_collection("ragversion_docs")
print(f"Total vectors: {info.vectors_count}")
print(f"Indexed: {info.indexed_vectors_count}")
```

## Querying

```python
# Similarity search
results = await vectorstore.asimilarity_search("What is RAGVersion?", k=5)

for doc in results:
    print(f"Content: {doc.page_content}")
    print(f"Source: {doc.metadata['file_path']}")
    print("---")

# With score threshold
results = await vectorstore.asimilarity_search_with_score(
    "API documentation",
    k=10,
    score_threshold=0.7  # Only results above this similarity
)

# With metadata filter
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = await vectorstore.asimilarity_search(
    "configuration",
    k=5,
    filter=Filter(
        must=[
            FieldCondition(
                key="file_name",
                match=MatchValue(value="config.md")
            )
        ]
    )
)
```

## Production Deployment

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  ollama_data:
  qdrant_data:
```

Start services:
```bash
docker-compose up -d

# Pull model
docker exec -it ollama_container ollama pull nomic-embed-text
```

### Kubernetes Deployment

```yaml
# qdrant-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        - containerPort: 6334
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
      volumes:
      - name: qdrant-storage
        persistentVolumeClaim:
          claimName: qdrant-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
spec:
  selector:
    app: qdrant
  ports:
  - port: 6333
    targetPort: 6333
```

## Backup and Restore

### Qdrant Backup

```python
# Create snapshot
snapshot_info = qdrant_client.create_snapshot(collection_name="ragversion_docs")
print(f"Snapshot created: {snapshot_info.name}")

# Download snapshot
qdrant_client.download_snapshot(
    collection_name="ragversion_docs",
    snapshot_name=snapshot_info.name,
    output_path="./backup.snapshot"
)
```

### Restore from Snapshot

```python
# Upload and restore
qdrant_client.recover_snapshot(
    collection_name="ragversion_docs",
    snapshot_path="./backup.snapshot"
)
```

## Troubleshooting

### Ollama Not Running

```
Error: Failed to connect to Ollama at http://localhost:11434
```

**Solution:**
```bash
# Start Ollama
ollama serve

# Or check if running
ps aux | grep ollama
```

### Model Not Found

```
Error: model 'nomic-embed-text' not found
```

**Solution:**
```bash
# Pull model
ollama pull nomic-embed-text

# List available models
ollama list
```

### Qdrant Connection Failed

```
Error: Failed to connect to Qdrant at localhost:6333
```

**Solutions:**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Check logs
docker logs qdrant_container
```

### Out of Memory

```
Error: CUDA out of memory
```

**Solutions:**
1. Use CPU instead:
   ```bash
   # Unset GPU for Ollama
   OLLAMA_GPU_LAYERS=0 ollama serve
   ```
2. Use quantized model:
   ```bash
   ollama pull nomic-embed-text:q4_0
   ```
3. Reduce batch size:
   ```python
   await sync.sync_directory("./documents", max_workers=1)
   ```

### Slow Embeddings

**Solutions:**
1. Use GPU if available
2. Use smaller model (nomic-embed-text instead of mxbai-embed-large)
3. Enable chunk tracking (only embed changes)
4. Increase Ollama concurrent requests:
   ```bash
   OLLAMA_NUM_PARALLEL=4 ollama serve
   ```

## Comparison: Ollama vs Alternatives

| Feature | Ollama | OpenAI | HuggingFace |
|---------|---------|---------|--------------|
| **Cost** | Free | $0.02-$0.13/1M | Free |
| **Setup** | Install Ollama | API key | Install package |
| **Models** | Latest OSS | Proprietary | Thousands |
| **Privacy** | ✓ Local | ✗ API | ✓ Local |
| **GPU** | ✓ Auto | N/A | Manual |
| **Updates** | Easy | Automatic | Manual |

## Advanced: Custom Models

Create custom embedding model:

```bash
# Create Modelfile
cat > Modelfile <<EOF
FROM nomic-embed-text
PARAMETER temperature 0
PARAMETER num_ctx 2048
EOF

# Create custom model
ollama create my-embed-model -f Modelfile

# Use custom model
```

```python
embeddings = OllamaEmbeddings(model="my-embed-model")
```

## See Also

- [OpenAI + Pinecone](openai_pinecone.md) - Cloud-based alternative
- [HuggingFace + Chroma](huggingface_chroma.md) - Alternative local setup
- [Cost Optimization Guide](cost_optimization.md) - General optimization tips

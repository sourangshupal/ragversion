# OpenAI Embeddings + Pinecone Vector Store

**Use case:** Production RAG system with managed infrastructure
**Cost:** ~$0.13 per 1M tokens (embeddings) + Pinecone pricing
**Pros:** Best quality, scalable, fully managed
**Cons:** Requires paid services

## Installation

```bash
pip install ragversion[langchain]
pip install langchain-openai langchain-pinecone pinecone-client
```

## Setup

```python
import os
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index if it doesn't exist
index_name = "ragversion-docs"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI text-embedding-3-small dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Get index
index = pc.Index(index_name)

# Create embeddings and vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
```

## Quick Start with RAGVersion

```python
from ragversion.integrations.langchain import quick_start

# Option 1: Let quick_start auto-detect OpenAI (if OPENAI_API_KEY is set)
sync = await quick_start(
    directory="./documents",
    embedding_provider="auto",  # Will use OpenAI if API key is set
    vectorstore_type="faiss",  # We'll replace this
)

# Option 2: Provide custom embeddings and vectorstore (recommended for Pinecone)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage
from ragversion.integrations.langchain import LangChainSync

# Create tracker
storage = SupabaseStorage.from_env()
tracker = AsyncVersionTracker(storage=storage, store_content=True)
await tracker.initialize()

# Create text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

# Create sync with Pinecone
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True,  # Save 80-95% on embedding costs!
)

# Sync directory
await sync.sync_directory("./documents", patterns=["*.txt", "*.md", "*.pdf"])
```

## Cost Optimization

### Enable Chunk Tracking (80-95% Savings)

RAGVersion's chunk tracking only re-embeds changed portions of documents:

```python
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True,  # ✓ Only embed changed chunks
)
```

**Example savings:**
- 1000-page document updated: 1 page changed
- Without chunk tracking: Re-embed all 1000 pages ($0.13)
- With chunk tracking: Re-embed 1 page ($0.0001) = **99.9% savings**

### Use Cheaper Embedding Models

```python
# Higher quality, more expensive
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")  # $0.13 per 1M tokens

# Good quality, cheaper (recommended)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")  # $0.02 per 1M tokens

# Even cheaper
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")  # $0.0001 per 1M tokens
```

### Reduce Chunk Size

Smaller chunks = fewer tokens = lower cost:

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,   # Smaller chunks
    chunk_overlap=50,  # Less overlap
)
```

**Tradeoff:** Smaller chunks may reduce retrieval quality.

## Querying the Vector Store

```python
# Similarity search
results = await vectorstore.asimilarity_search("What is RAGVersion?", k=5)

for doc in results:
    print(f"Content: {doc.page_content}")
    print(f"Source: {doc.metadata['file_path']}")
    print(f"Version: {doc.metadata['version_number']}")
    print("---")

# With score
results = await vectorstore.asimilarity_search_with_score("What is RAGVersion?", k=5)

for doc, score in results:
    print(f"Score: {score}")
    print(f"Content: {doc.page_content}")
    print("---")
```

## Production Best Practices

### 1. Use Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
```

### 2. Handle Rate Limits

```python
from openai import RateLimitError

try:
    await sync.sync_directory("./documents")
except RateLimitError:
    # Wait and retry
    await asyncio.sleep(60)
    await sync.sync_directory("./documents")
```

### 3. Monitor Costs

```python
import tiktoken

def estimate_cost(text: str, model: str = "text-embedding-3-small") -> float:
    """Estimate embedding cost for text."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = len(encoding.encode(text))

    # Pricing (as of 2024)
    prices = {
        "text-embedding-3-small": 0.00002 / 1000,  # $0.02 per 1M tokens
        "text-embedding-3-large": 0.00013 / 1000,  # $0.13 per 1M tokens
    }

    return tokens * prices.get(model, 0.00002 / 1000)

# Before syncing
with open("large_doc.txt") as f:
    content = f.read()
    cost = estimate_cost(content)
    print(f"Estimated cost: ${cost:.4f}")
```

### 4. Use Metadata Filters

```python
# Track source metadata
def metadata_extractor(file_path: str) -> dict:
    return {
        "source": "documentation",
        "department": "engineering",
    }

sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    metadata_extractor=metadata_extractor,
)

# Query with filters
results = vectorstore.similarity_search(
    "API documentation",
    k=5,
    filter={"department": "engineering"}
)
```

## Troubleshooting

### OpenAI API Key Error

```
Error: OpenAI API key not found
```

**Solution:**
```bash
export OPENAI_API_KEY="sk-..."
```

### Pinecone Index Not Found

```
Error: Index 'ragversion-docs' not found
```

**Solution:** Create the index first (see Setup section above)

### Rate Limit Exceeded

```
Error: Rate limit reached for requests
```

**Solutions:**
1. Reduce `max_workers` parameter:
   ```python
   await sync.sync_directory("./documents", max_workers=2)
   ```
2. Add delays between batches
3. Upgrade OpenAI tier

### Dimension Mismatch

```
Error: Dimension mismatch: expected 1536, got 3072
```

**Solution:** Ensure Pinecone index dimension matches embedding model:
- `text-embedding-3-small`: 1536 dimensions
- `text-embedding-3-large`: 3072 dimensions
- `text-embedding-ada-002`: 1536 dimensions

## See Also

- [HuggingFace + Chroma](huggingface_chroma.md) - Free local alternative
- [Ollama + Qdrant](ollama_qdrant.md) - Self-hosted setup
- [Cost Optimization Guide](cost_optimization.md) - Save 80-95% on embeddings

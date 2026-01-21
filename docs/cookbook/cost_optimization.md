# Cost Optimization Guide

This guide shows how to minimize embedding costs while using RAGVersion.

## TL;DR - Quick Wins

**Enable chunk tracking for 80-95% cost savings:**

```python
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True,  # ← This one line saves 80-95%
)
```

**Or use free local embeddings:**

```python
from ragversion.integrations.langchain import quick_start

sync = await quick_start(
    directory="./documents",
    embedding_provider="huggingface",  # Free!
)
```

---

## Understanding Embedding Costs

### Cost per 1M Tokens (as of 2024)

| Provider | Model | Cost per 1M tokens | Quality |
|----------|-------|-------------------|---------|
| **OpenAI** | text-embedding-3-small | $0.02 | Excellent |
| **OpenAI** | text-embedding-3-large | $0.13 | Best |
| **OpenAI** | ada-002 (legacy) | $0.10 | Good |
| **Cohere** | embed-english-v3.0 | $0.10 | Excellent |
| **Google** | text-embedding-004 | $0.025 | Excellent |
| **Voyage** | voyage-2 | $0.12 | Excellent |
| **HuggingFace** | All models | **FREE** | Good |
| **Ollama** | All models | **FREE** | Good |

### What is a Token?

Approximate conversions:
- **1 token** ≈ 4 characters ≈ 0.75 words
- **100 tokens** ≈ 75 words ≈ 1 paragraph
- **1000 tokens** ≈ 750 words ≈ 3 pages

Example:
```python
import tiktoken

text = "RAGVersion is a version tracking system for RAG applications."
encoding = tiktoken.encoding_for_model("text-embedding-3-small")
tokens = len(encoding.encode(text))
print(f"Tokens: {tokens}")  # Output: ~13 tokens
```

---

## Strategy 1: Enable Chunk Tracking (80-95% Savings)

### How It Works

**Without chunk tracking:**
- Document changes → Re-embed entire document
- 1000-page doc, 1 page changes → Re-embed 1000 pages

**With chunk tracking:**
- Document changes → Re-embed only changed chunks
- 1000-page doc, 1 page changes → Re-embed 1 page

### Implementation

```python
from ragversion.integrations.langchain import quick_start

sync = await quick_start(
    directory="./documents",
    enable_chunk_tracking=True,  # ← Enable here
)
```

Or manually:

```python
from ragversion import AsyncVersionTracker
from ragversion.integrations.langchain import LangChainSync

# Create tracker with chunk tracking enabled
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=True,
    enable_chunk_tracking=True,  # ← Enable here
)

# Create sync
sync = LangChainSync(
    tracker=tracker,
    text_splitter=text_splitter,
    embeddings=embeddings,
    vectorstore=vectorstore,
    enable_chunk_tracking=True,  # ← Enable here too
)
```

### Real-World Savings Example

**Scenario:** Documentation site with 1000 pages, 10 pages updated daily

**Without chunk tracking:**
- Daily embeddings: 10 full documents = 500,000 tokens
- Monthly cost (OpenAI small): 15M tokens × $0.02 / 1M = **$0.30/month**

**With chunk tracking:**
- Daily embeddings: 10 changed chunks = 50,000 tokens
- Monthly cost: 1.5M tokens × $0.02 / 1M = **$0.03/month**
- **Savings: $0.27/month (90%)**

For larger codebases with thousands of files, this can save **hundreds of dollars per month**.

---

## Strategy 2: Use Cheaper Embedding Models

### OpenAI Model Comparison

```python
# Most expensive (best quality)
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")  # $0.13/1M
# Dimensions: 3072

# Recommended (good balance)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")  # $0.02/1M ⭐
# Dimensions: 1536

# Legacy (not recommended)
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")  # $0.10/1M
# Dimensions: 1536
```

**Cost comparison for 10M tokens:**
- `text-embedding-3-large`: $1.30
- `text-embedding-3-small`: $0.20 ← **Save $1.10 (85%)**
- `ada-002`: $1.00

### Quality vs Cost Tradeoff

Test different models on your data:

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def compare_models():
    # Test query
    query = "What is RAGVersion?"

    # Model 1: Expensive
    embeddings_large = OpenAIEmbeddings(model="text-embedding-3-large")
    results_large = vectorstore.similarity_search(query, k=5)

    # Model 2: Cheap
    embeddings_small = OpenAIEmbeddings(model="text-embedding-3-small")
    results_small = vectorstore.similarity_search(query, k=5)

    # Compare results
    print(f"Large model results: {[r.page_content[:50] for r in results_large]}")
    print(f"Small model results: {[r.page_content[:50] for r in results_small]}")

# If results are similar, use cheaper model!
```

---

## Strategy 3: Use Free Local Embeddings

### Zero Cost Options

#### Option 1: HuggingFace (Recommended)

```python
from ragversion.integrations.langchain import quick_start

sync = await quick_start(
    directory="./documents",
    embedding_provider="huggingface",
    vectorstore_type="chroma",
    storage_backend="sqlite",  # Also free!
)
```

**Pros:**
- ✓ Completely free
- ✓ Works offline
- ✓ No rate limits
- ✓ Privacy (data stays local)

**Cons:**
- ✗ Slower on CPU (~500 docs/sec vs ~5000 with OpenAI)
- ✗ Slightly lower quality
- ✗ Requires ~200MB RAM

#### Option 2: Ollama

```python
sync = await quick_start(
    directory="./documents",
    embedding_provider="ollama",
    vectorstore_type="chroma",
)
```

**Pros:**
- ✓ Completely free
- ✓ Latest open-source models
- ✓ GPU acceleration
- ✓ Privacy

**Cons:**
- ✗ Requires Ollama installation
- ✗ Larger resource usage

### Cost Comparison: 1 Billion Tokens

| Provider | Cost |
|----------|------|
| OpenAI text-embedding-3-large | $130 |
| OpenAI text-embedding-3-small | $20 |
| Cohere embed-english-v3.0 | $100 |
| **HuggingFace** | **$0** |
| **Ollama** | **$0** |

---

## Strategy 4: Reduce Token Usage

### 1. Optimize Chunk Size

Smaller chunks = fewer tokens:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Before: Large chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,  # 2000 chars ≈ 500 tokens
    chunk_overlap=400,
)

# After: Smaller chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # 1000 chars ≈ 250 tokens
    chunk_overlap=200,
)
```

**Savings:** ~50% fewer tokens per chunk

**Tradeoff:** May reduce retrieval quality (less context per chunk)

### 2. Reduce Chunk Overlap

```python
# Before: High overlap
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,  # 20% overlap
)
# Total tokens for 1000-char doc: ~1200

# After: Low overlap
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=50,  # 5% overlap
)
# Total tokens for 1000-char doc: ~1050
```

**Savings:** ~12% fewer tokens

**Tradeoff:** May miss information at chunk boundaries

### 3. Filter Files Before Embedding

Skip files you don't need to search:

```python
# Only embed documentation files
await sync.sync_directory(
    "./project",
    patterns=["*.md", "*.txt"],  # Skip images, binaries, etc.
)
```

### 4. Deduplication

Skip duplicate or similar documents:

```python
import hashlib

seen_hashes = set()

def should_embed(file_path: str) -> bool:
    with open(file_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()

    if content_hash in seen_hashes:
        return False  # Skip duplicate

    seen_hashes.add(content_hash)
    return True

# Use in custom sync logic
```

---

## Strategy 5: Batch Processing

### Reduce API Overhead

```python
# Process in larger batches to reduce API calls
await sync.sync_directory(
    "./documents",
    max_workers=1,  # Process sequentially to batch API calls
)
```

### Use Rate Limit Efficiently

```python
import asyncio
from openai import RateLimitError

async def sync_with_retry(directory: str):
    while True:
        try:
            await sync.sync_directory(directory)
            break
        except RateLimitError:
            print("Rate limit hit, waiting 60s...")
            await asyncio.sleep(60)
```

---

## Strategy 6: Hybrid Approach

Use expensive embeddings for important documents, cheap for others:

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# High-quality embeddings for critical docs
embeddings_premium = OpenAIEmbeddings(model="text-embedding-3-large")

# Cheap embeddings for everything else
embeddings_basic = HuggingFaceEmbeddings()

def select_embeddings(file_path: str):
    if "critical" in file_path or file_path.endswith(".md"):
        return embeddings_premium
    else:
        return embeddings_basic

# Use in custom sync logic
```

---

## Cost Monitoring

### Track Embedding Costs

```python
import tiktoken

class CostTracker:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.total_tokens = 0
        self.encoding = tiktoken.encoding_for_model(model)

        # Pricing (per 1M tokens)
        self.prices = {
            "text-embedding-3-small": 0.02,
            "text-embedding-3-large": 0.13,
        }

    def count_tokens(self, text: str) -> int:
        tokens = len(self.encoding.encode(text))
        self.total_tokens += tokens
        return tokens

    def get_cost(self) -> float:
        price_per_token = self.prices.get(self.model, 0.02) / 1_000_000
        return self.total_tokens * price_per_token

    def report(self):
        cost = self.get_cost()
        print(f"Total tokens: {self.total_tokens:,}")
        print(f"Estimated cost: ${cost:.4f}")

# Usage
tracker = CostTracker()

# Before embedding
with open("document.txt") as f:
    content = f.read()
    tokens = tracker.count_tokens(content)

# After processing all documents
tracker.report()
```

### Set Budget Alerts

```python
MAX_MONTHLY_BUDGET = 10.00  # $10/month

async def sync_with_budget(directory: str):
    tracker = CostTracker()

    # Estimate cost before syncing
    total_tokens = 0
    for file in Path(directory).glob("**/*.txt"):
        with open(file) as f:
            total_tokens += tracker.count_tokens(f.read())

    estimated_cost = tracker.get_cost()

    if estimated_cost > MAX_MONTHLY_BUDGET:
        raise ValueError(
            f"Estimated cost ${estimated_cost:.2f} exceeds budget ${MAX_MONTHLY_BUDGET}"
        )

    # Proceed with sync
    await sync.sync_directory(directory)
```

---

## Cost Optimization Checklist

- [ ] **Enable chunk tracking** (80-95% savings)
- [ ] **Use text-embedding-3-small** instead of 3-large
- [ ] **Consider free alternatives** (HuggingFace/Ollama)
- [ ] **Reduce chunk size** to 1000 chars
- [ ] **Reduce chunk overlap** to 100-200 chars
- [ ] **Filter file types** to only necessary documents
- [ ] **Deduplicate** identical files
- [ ] **Monitor costs** with tracking code
- [ ] **Set budget alerts** to prevent overages
- [ ] **Use hybrid approach** for different document tiers

---

## Real-World Case Studies

### Case Study 1: Code Documentation Site

**Before optimization:**
- 5000 markdown files
- Updated 50 files/day
- text-embedding-3-large
- No chunk tracking
- **Cost:** $15/month

**After optimization:**
- Enabled chunk tracking
- Switched to text-embedding-3-small
- Reduced chunk size
- **Cost:** $0.50/month
- **Savings: $14.50/month (97%)**

### Case Study 2: Customer Support Knowledge Base

**Before optimization:**
- 10,000 PDF files
- Updated 100 files/day
- OpenAI embeddings
- **Cost:** $50/month

**After optimization:**
- Switched to HuggingFace (free)
- Enabled chunk tracking
- **Cost:** $0/month
- **Savings: $50/month (100%)**

### Case Study 3: Enterprise Document Search

**Before optimization:**
- 100,000 documents
- text-embedding-3-large
- Full re-embedding on updates
- **Cost:** $200/month

**After optimization:**
- Enabled chunk tracking (95% savings)
- Hybrid approach (critical docs = large, others = small)
- **Cost:** $12/month
- **Savings: $188/month (94%)**

---

## Summary: Recommended Stack by Budget

### $0/month (Free)
```python
sync = await quick_start(
    directory="./documents",
    embedding_provider="huggingface",
    vectorstore_type="chroma",
    storage_backend="sqlite",
    enable_chunk_tracking=True,
)
```

### $5/month (Budget)
```python
sync = await quick_start(
    directory="./documents",
    embedding_provider="openai",  # text-embedding-3-small
    vectorstore_type="chroma",
    enable_chunk_tracking=True,
)
```

### $20/month (Production)
```python
sync = await quick_start(
    directory="./documents",
    embedding_provider="openai",  # text-embedding-3-large for quality
    vectorstore_type="pinecone",  # Managed, scalable
    enable_chunk_tracking=True,  # Still save 80-95%!
)
```

---

## See Also

- [OpenAI + Pinecone](openai_pinecone.md) - Production setup
- [HuggingFace + Chroma](huggingface_chroma.md) - Free local setup
- [Ollama + Qdrant](ollama_qdrant.md) - Self-hosted setup

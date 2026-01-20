# REST API Guide

RAGVersion provides a comprehensive REST API built with FastAPI, enabling programmatic access to all version tracking features from any programming language or platform.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Request/Response Models](#requestresponse-models)
- [Code Examples](#code-examples)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Getting Started

### Installation

Install RAGVersion with API dependencies:

```bash
pip install ragversion[api]
```

This installs:
- `fastapi>=0.109.0` - Modern web framework
- `uvicorn[standard]>=0.27.0` - ASGI server with HTTP/2 support

### Starting the Server

Start the API server using the CLI:

```bash
# Default: http://0.0.0.0:8000
ragversion serve

# Custom host and port
ragversion serve --host localhost --port 5000

# Development mode with auto-reload
ragversion serve --reload
```

### Accessing Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json
- **Health Check**: http://localhost:8000/api/health

---

## Authentication

### Optional API Key Authentication

API key authentication is disabled by default. To enable:

**Option 1: Environment Variables**

```bash
export RAGVERSION_AUTH_ENABLED=true
export RAGVERSION_API_KEYS="key1,key2,key3"
ragversion serve
```

**Option 2: Configuration File**

Create `ragversion.yaml`:

```yaml
api:
  auth_enabled: true
  api_keys:
    - "your-secret-key-1"
    - "your-secret-key-2"
```

Then start the server:

```bash
ragversion serve --config ragversion.yaml
```

### Using API Keys

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-secret-key-1" http://localhost:8000/api/documents
```

---

## API Endpoints

### Health Check

**GET /health**

Check API server and storage backend health.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.8.0",
  "storage_backend": "SQLiteStorage",
  "storage_healthy": true,
  "timestamp": "2024-01-20T10:30:00Z"
}
```

---

### Document Management

#### List Documents

**GET /documents**

List all documents with pagination and sorting.

**Query Parameters:**
- `limit` (int, default: 100): Number of results (1-1000)
- `offset` (int, default: 0): Pagination offset
- `order_by` (string, default: "updated_at"): Sort field

**Example:**
```bash
curl "http://localhost:8000/api/documents?limit=10&offset=0&order_by=updated_at"
```

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "file_path": "/path/to/document.pdf",
    "file_name": "document.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "content_hash": "abc123...",
    "created_at": "2024-01-20T10:00:00Z",
    "updated_at": "2024-01-20T15:30:00Z",
    "version_count": 5,
    "current_version": 5,
    "metadata": {}
  }
]
```

---

#### Get Document by ID

**GET /documents/{document_id}**

Retrieve a specific document by UUID.

**Example:**
```bash
curl "http://localhost:8000/api/documents/123e4567-e89b-12d3-a456-426614174000"
```

**Response:** Same as document object above.

**Errors:**
- 404: Document not found

---

#### Get Document by Path

**GET /documents/path/{file_path:path}**

Retrieve a document by its file path.

**Example:**
```bash
curl "http://localhost:8000/api/documents/path/docs/guide.pdf"
```

**Response:** Same as document object.

---

#### Search Documents

**POST /documents/search**

Search documents by file type and metadata filters.

**Request Body:**
```json
{
  "file_type": "pdf",
  "metadata_filter": {
    "author": "John Doe",
    "category": "technical"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "pdf",
    "metadata_filter": {"author": "John Doe"}
  }'
```

**Response:** Array of document objects.

---

#### Delete Document

**DELETE /documents/{document_id}**

Delete a document and all its versions.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/documents/123e4567-e89b-12d3-a456-426614174000"
```

**Response:** 204 No Content

**Errors:**
- 404: Document not found

---

#### Get Top Documents

**GET /documents/top/by-version-count**

Get top documents by version count or other criteria.

**Query Parameters:**
- `limit` (int, default: 10): Number of results (1-100)
- `order_by` (string, default: "version_count"): Sort criteria

**Example:**
```bash
curl "http://localhost:8000/api/documents/top/by-version-count?limit=5"
```

**Response:** Array of document objects sorted by criteria.

---

### Version Management

#### Get Version by ID

**GET /versions/{version_id}**

Retrieve a specific version by UUID.

**Example:**
```bash
curl "http://localhost:8000/api/versions/789e4567-e89b-12d3-a456-426614174001"
```

**Response:**
```json
{
  "id": "789e4567-e89b-12d3-a456-426614174001",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "version_number": 3,
  "content_hash": "def456...",
  "file_size": 1024000,
  "change_type": "modified",
  "created_at": "2024-01-20T12:00:00Z",
  "created_by": "user@example.com",
  "metadata": {}
}
```

---

#### List Versions for Document

**GET /versions/document/{document_id}**

Get version history for a specific document.

**Query Parameters:**
- `limit` (int, default: 100): Number of results (1-1000)
- `offset` (int, default: 0): Pagination offset

**Example:**
```bash
curl "http://localhost:8000/api/versions/document/123e4567-e89b-12d3-a456-426614174000?limit=10"
```

**Response:** Array of version objects.

---

#### Get Version by Number

**GET /versions/document/{document_id}/number/{version_number}**

Get a specific version of a document by version number.

**Example:**
```bash
curl "http://localhost:8000/api/versions/document/123e4567-e89b-12d3-a456-426614174000/number/3"
```

**Response:** Version object.

---

#### Get Latest Version

**GET /versions/document/{document_id}/latest**

Get the most recent version of a document.

**Example:**
```bash
curl "http://localhost:8000/api/versions/document/123e4567-e89b-12d3-a456-426614174000/latest"
```

**Response:** Version object.

---

#### Get Version Content

**GET /versions/{version_id}/content**

Get the actual content of a specific version.

**Example:**
```bash
curl "http://localhost:8000/api/versions/789e4567-e89b-12d3-a456-426614174001/content"
```

**Response:** Plain text content of the version.

---

#### Restore Version

**POST /versions/restore**

Restore a document to a specific version.

**Request Body:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "version_number": 3,
  "target_path": "/path/to/restore/document.pdf"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/versions/restore \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "version_number": 3
  }'
```

**Response:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "version_id": "new-version-id",
  "change_type": "restored",
  "file_name": "document.pdf",
  "file_path": "/path/to/document.pdf",
  "file_size": 1024000,
  "content_hash": "def456...",
  "version_number": 6,
  "previous_hash": "abc123...",
  "timestamp": "2024-01-20T16:00:00Z"
}
```

---

#### Get Diff Between Versions

**GET /versions/document/{document_id}/diff/{from_version}/{to_version}**

Compare two versions of a document.

**Example:**
```bash
curl "http://localhost:8000/api/versions/document/123e4567-e89b-12d3-a456-426614174000/diff/2/4"
```

**Response:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "from_version": 2,
  "to_version": 4,
  "additions": 150,
  "deletions": 75,
  "changes": 25,
  "diff_text": "--- Version 2\n+++ Version 4\n...",
  "similarity": 0.85
}
```

---

### Tracking Operations

#### Track Single File

**POST /track/file**

Track changes to a single file.

**Request Body:**
```json
{
  "file_path": "/path/to/document.pdf",
  "metadata": {
    "author": "John Doe",
    "category": "technical"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/track/file \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.pdf",
    "metadata": {"author": "John Doe"}
  }'
```

**Response:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "version_id": "789e4567-e89b-12d3-a456-426614174001",
  "change_type": "created",
  "file_name": "document.pdf",
  "file_path": "/path/to/document.pdf",
  "file_size": 1024000,
  "content_hash": "abc123...",
  "version_number": 1,
  "previous_hash": null,
  "timestamp": "2024-01-20T10:00:00Z"
}
```

**Errors:**
- 404: File not found
- 500: Parsing or storage error

---

#### Track Directory

**POST /track/directory**

Track all files in a directory with optional pattern matching.

**Request Body:**
```json
{
  "dir_path": "/path/to/documents",
  "patterns": ["*.pdf", "*.docx"],
  "recursive": true,
  "max_workers": 4,
  "metadata": {
    "project": "Documentation"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/track/directory \
  -H "Content-Type: application/json" \
  -d '{
    "dir_path": "/path/to/documents",
    "patterns": ["*.pdf"],
    "recursive": true
  }'
```

**Response:**
```json
{
  "successful": [
    {
      "document_id": "...",
      "version_id": "...",
      "change_type": "created",
      "file_name": "doc1.pdf",
      "file_path": "/path/to/documents/doc1.pdf",
      "file_size": 1024000,
      "content_hash": "abc123...",
      "version_number": 1,
      "previous_hash": null,
      "timestamp": "2024-01-20T10:00:00Z"
    }
  ],
  "failed": [
    {
      "file_path": "/path/to/documents/corrupt.pdf",
      "error": "Failed to parse PDF",
      "error_type": "parsing",
      "exception_type": "ParsingError"
    }
  ],
  "total_files": 10,
  "duration_seconds": 2.5,
  "started_at": "2024-01-20T10:00:00Z",
  "completed_at": "2024-01-20T10:00:02Z"
}
```

---

### Statistics and Analytics

#### Get Storage Statistics

**GET /statistics**

Get overall storage statistics.

**Query Parameters:**
- `days` (int, default: 30): Number of days for recent changes (1-365)

**Example:**
```bash
curl "http://localhost:8000/api/statistics?days=7"
```

**Response:**
```json
{
  "total_documents": 1250,
  "total_versions": 5680,
  "total_size_bytes": 524288000,
  "file_types": {
    "pdf": 450,
    "docx": 320,
    "txt": 280,
    "md": 200
  },
  "recent_changes": 42,
  "oldest_document": "2023-01-15T10:00:00Z",
  "newest_document": "2024-01-20T15:30:00Z"
}
```

---

#### Get Document Statistics

**GET /statistics/document/{document_id}**

Get detailed statistics for a specific document.

**Example:**
```bash
curl "http://localhost:8000/api/statistics/document/123e4567-e89b-12d3-a456-426614174000"
```

**Response:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_versions": 15,
  "total_size_bytes": 15360000,
  "first_version_date": "2023-06-10T09:00:00Z",
  "latest_version_date": "2024-01-20T15:30:00Z",
  "change_frequency_days": 15.2,
  "change_types": {
    "created": 1,
    "modified": 13,
    "restored": 1
  }
}
```

---

## Request/Response Models

### Common Models

#### Document
```typescript
{
  id: UUID;
  file_path: string;
  file_name: string;
  file_type: string;
  file_size: number;
  content_hash: string;
  created_at: datetime;
  updated_at: datetime;
  version_count: number;
  current_version: number;
  metadata: Record<string, any>;
}
```

#### Version
```typescript
{
  id: UUID;
  document_id: UUID;
  version_number: number;
  content_hash: string;
  file_size: number;
  change_type: "created" | "modified" | "deleted" | "restored";
  created_at: datetime;
  created_by: string | null;
  metadata: Record<string, any>;
}
```

#### ChangeEvent
```typescript
{
  document_id: UUID;
  version_id: UUID;
  change_type: "created" | "modified" | "deleted" | "restored";
  file_name: string;
  file_path: string;
  file_size: number;
  content_hash: string;
  version_number: number;
  previous_hash: string | null;
  timestamp: datetime;
}
```

---

## Code Examples

### Python with requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Track a file
response = requests.post(
    f"{BASE_URL}/track/file",
    json={
        "file_path": "/path/to/document.pdf",
        "metadata": {"author": "John Doe"}
    }
)
event = response.json()
print(f"Tracked: {event['file_name']} (v{event['version_number']})")

# List documents
response = requests.get(f"{BASE_URL}/documents?limit=10")
documents = response.json()
for doc in documents:
    print(f"{doc['file_name']}: {doc['version_count']} versions")

# Get version history
doc_id = documents[0]['id']
response = requests.get(f"{BASE_URL}/versions/document/{doc_id}")
versions = response.json()
for v in versions:
    print(f"Version {v['version_number']}: {v['change_type']}")
```

---

### JavaScript with fetch

```javascript
const BASE_URL = "http://localhost:8000";

// Track a file
async function trackFile(filePath) {
  const response = await fetch(`${BASE_URL}/track/file`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_path: filePath,
      metadata: { author: "Jane Smith" }
    })
  });
  const event = await response.json();
  console.log(`Tracked: ${event.file_name} (v${event.version_number})`);
}

// Get statistics
async function getStats() {
  const response = await fetch(`${BASE_URL}/statistics?days=7`);
  const stats = await response.json();
  console.log(`Total documents: ${stats.total_documents}`);
  console.log(`Recent changes: ${stats.recent_changes}`);
}
```

---

### cURL Examples

```bash
# Track directory
curl -X POST http://localhost:8000/api/track/directory \
  -H "Content-Type: application/json" \
  -d '{
    "dir_path": "/docs",
    "patterns": ["*.md"],
    "recursive": true
  }'

# Get diff between versions
curl "http://localhost:8000/api/versions/document/<doc-id>/diff/1/3"

# Restore version
curl -X POST http://localhost:8000/api/versions/restore \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "<doc-id>",
    "version_number": 2
  }'

# Search documents
curl -X POST http://localhost:8000/api/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "pdf",
    "metadata_filter": {"category": "technical"}
  }'
```

---

## Error Handling

### Standard Error Response

```json
{
  "error": "Not Found",
  "detail": "Document 123e4567-e89b-12d3-a456-426614174000 not found",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### HTTP Status Codes

- **200 OK**: Request successful
- **204 No Content**: Successful deletion
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing API key
- **403 Forbidden**: Invalid API key
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Storage backend unavailable

---

## Rate Limiting

Currently, rate limiting is not implemented. For production deployments, consider:

- **Nginx rate limiting**: Limit requests per IP
- **API Gateway**: AWS API Gateway, Kong, or similar
- **Application-level**: Implement with `slowapi` middleware

---

## Best Practices

### 1. Use Pagination

Always paginate when listing resources:

```bash
# Good
curl "http://localhost:8000/api/documents?limit=100&offset=0"

# Avoid
curl "http://localhost:8000/api/documents?limit=10000"
```

### 2. Filter Early

Use search endpoints with filters instead of fetching all:

```bash
# Good
curl -X POST http://localhost:8000/api/documents/search \
  -d '{"file_type": "pdf"}'

# Avoid
# Fetching all documents and filtering client-side
```

### 3. Handle Errors Gracefully

Always check HTTP status codes:

```python
response = requests.post(...)
if response.status_code == 200:
    data = response.json()
elif response.status_code == 404:
    print("Resource not found")
elif response.status_code == 500:
    print("Server error")
```

### 4. Use Async Clients

For high-throughput applications, use async HTTP clients:

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(f"{BASE_URL}/documents")
    documents = response.json()
```

---

## Production Deployment

### Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .[api]

COPY . .

CMD ["ragversion", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t ragversion-api .
docker run -p 8000:8000 ragversion-api
```

### Systemd Service

Create `/etc/systemd/system/ragversion-api.service`:

```ini
[Unit]
Description=RAGVersion API Server
After=network.target

[Service]
Type=simple
User=ragversion
WorkingDirectory=/opt/ragversion
ExecStart=/opt/ragversion/.venv/bin/ragversion serve --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ragversion-api
sudo systemctl start ragversion-api
```

---

## Troubleshooting

### Server Won't Start

**Error:** `ImportError: No module named 'fastapi'`

**Solution:** Install API dependencies:
```bash
pip install ragversion[api]
```

---

### 503 Service Unavailable

**Error:** "Tracker not initialized"

**Solution:** Ensure storage backend is configured correctly in `ragversion.yaml`.

---

### CORS Issues

**Error:** Browser blocks requests due to CORS policy

**Solution:** CORS is enabled by default for all origins. To restrict:

```yaml
api:
  cors_enabled: true
  cors_origins:
    - "https://your-frontend.com"
```

---

## Next Steps

- Explore [API examples](../examples/api/)
- Read [Configuration Guide](CONFIGURATION.md)
- See [Integration Guide](INTEGRATIONS.md) for LangChain/LlamaIndex

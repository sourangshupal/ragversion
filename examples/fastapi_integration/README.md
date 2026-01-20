# RAGVersion FastAPI Integration

A production-ready FastAPI integration for RAGVersion with automatic document change tracking, real-time monitoring, and comprehensive API endpoints.

## Features

- ✅ **Automatic Change Monitoring**: Background monitoring detects file changes automatically
- ✅ **Real-time Notifications**: WebSocket support for real-time change updates
- ✅ **Comprehensive API**: RESTful endpoints for querying documents, versions, and chunks
- ✅ **Version Comparison**: Compare any two versions of a document
- ✅ **Chunk Analysis**: View chunks created from documents
- ✅ **LangChain Integration**: Built-in LangChain sync support
- ✅ **No UI Required**: Pure API-based solution - integrate with any frontend

## Architecture

```
FastAPI Server
├── RAGVersion Tracker
│   ├── Document Storage (Supabase)
│   └── Version Tracking
├── Change Monitor
│   ├── Background File Scanning
│   └── Event Callbacks
├── LangChain Sync
│   ├── Text Splitting
│   └── Vector Store Integration
└── API Endpoints
    ├── REST API
    └── WebSocket
```

## Installation

### 1. Install Dependencies

```bash
cd examples/fastapi_integration
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
DOCUMENTS_DIRECTORY=./documents
MONITOR_INTERVAL=30
SYNC_ON_STARTUP=true
```

### 3. Create Documents Directory

```bash
mkdir -p documents
```

## Running the Server

### Start the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will:
- Start automatically on startup
- Monitor the documents directory for changes
- Sync existing documents on startup (if `SYNC_ON_STARTUP=true`)
- Accept API requests on port 8000

## API Endpoints

### Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and endpoints list |
| `/api/stats` | GET | System statistics |
| `/api/changes` | GET | Get recent changes |
| `/api/documents` | GET | List all documents |
| `/api/documents/{file_path}` | GET | Get document details |
| `/api/documents/{file_path}/versions/{version_number}` | GET | Get specific version |
| `/api/documents/{file_path}/chunks` | GET | Get document chunks |
| `/api/sync` | POST | Sync all documents |
| `/api/sync/{file_path}` | POST | Sync specific file |
| `/api/compare/{file_path}` | GET | Compare two versions |
| `/api/documents/{file_path}` | DELETE | Delete document |
| `/ws/changes` | WebSocket | Real-time change notifications |

### Detailed Examples

#### 1. Get Statistics

```bash
curl http://localhost:8000/api/stats
```

Response:
```json
{
  "total_documents": 5,
  "monitored_directory": "./documents",
  "monitor_interval_seconds": 30,
  "monitor_active": true,
  "recent_changes": [
    {
      "file_path": "./documents/sample.txt",
      "current_version": 2,
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### 2. Get Recent Changes

```bash
curl "http://localhost:8000/api/changes?limit=10&file_type=.txt"
```

Response:
```json
[
  {
    "file_path": "./documents/sample.txt",
    "change_type": "MODIFIED",
    "previous_version": 1,
    "current_version": 2,
    "timestamp": "2024-01-15T10:30:00"
  }
]
```

#### 3. List All Documents

```bash
curl "http://localhost:8000/api/documents?limit=50&file_type=.txt"
```

Response:
```json
[
  {
    "file_path": "./documents/sample.txt",
    "current_version": 2,
    "content_hash": "abc123...",
    "file_size": 1024,
    "file_type": ".txt",
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

#### 4. Get Document Details with All Versions

```bash
curl http://localhost:8000/api/documents/documents/sample.txt
```

Response:
```json
{
  "file_path": "./documents/sample.txt",
  "current_version": 2,
  "file_size": 1024,
  "file_type": ".txt",
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:30:00",
  "total_versions": 2,
  "versions": [
    {
      "version_number": 1,
      "change_type": "CREATED",
      "content_hash": "hash1",
      "created_at": "2024-01-15T10:00:00"
    },
    {
      "version_number": 2,
      "change_type": "MODIFIED",
      "content_hash": "hash2",
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### 5. Get Specific Version Content

```bash
curl http://localhost:8000/api/documents/documents/sample.txt/versions/1
```

Response:
```json
{
  "file_path": "./documents/sample.txt",
  "version_number": 1,
  "change_type": "CREATED",
  "content_hash": "hash1",
  "created_at": "2024-01-15T10:00:00",
  "content": "This is the content...",
  "content_length": 1024
}
```

#### 6. Get Document Chunks

```bash
curl http://localhost:8000/api/documents/documents/sample.txt/chunks
```

Response:
```json
{
  "file_path": "./documents/sample.txt",
  "version": 2,
  "total_chunks": 5,
  "chunks": [
    {
      "index": 0,
      "content_preview": "This is the first chunk...",
      "length": 1000,
      "hash": "abc123..."
    }
  ]
}
```

#### 7. Sync All Documents

```bash
curl -X POST http://localhost:8000/api/sync
```

Response:
```json
{
  "synced_files": 3,
  "events": [
    {
      "file_path": "./documents/sample.txt",
      "change_type": "MODIFIED",
      "previous_version": 1,
      "current_version": 2
    }
  ],
  "duration_ms": 250
}
```

#### 8. Sync Specific File

```bash
curl -X POST http://localhost:8000/api/sync/sample.txt
```

#### 9. Compare Two Versions

```bash
curl "http://localhost:8000/api/compare/documents/sample.txt?v1=1&v2=2"
```

Response:
```json
{
  "file_path": "./documents/sample.txt",
  "version1": {
    "number": 1,
    "content_length": 1024,
    "total_chunks": 5
  },
  "version2": {
    "number": 2,
    "content_length": 1169,
    "total_chunks": 5
  },
  "difference": {
    "content_length_diff": 145,
    "new_chunks_count": 1,
    "removed_chunks_count": 1,
    "new_chunk_indices": [2],
    "removed_chunk_indices": [3]
  }
}
```

#### 10. Delete Document

```bash
curl -X DELETE http://localhost:8000/api/documents/documents/sample.txt
```

### WebSocket Integration

Connect to WebSocket for real-time change notifications:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/changes');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'change') {
    console.log(`File changed: ${data.file_path}`);
    console.log(`Change type: ${data.change_type}`);
    console.log(`Timestamp: ${data.timestamp}`);
    
    // Refresh your UI, re-query API, etc.
    refreshDocumentList();
  }
};

// Keep connection alive
setInterval(() => {
  ws.send('ping');
}, 30000);
```

## Background Monitoring

The server automatically monitors the documents directory for changes:

- **Default Interval**: 30 seconds (configurable via `MONITOR_INTERVAL`)
- **Automatic Detection**: New, modified, and deleted files
- **Event Callbacks**: Extensible callback system for custom actions
- **No Manual Sync Needed**: Changes detected automatically

### Custom Callbacks

You can add custom callbacks in `main.py`:

```python
@app.on_event("startup")
async def startup_event():
    # Add your custom callback
    async def my_custom_callback(file_path: str, *args):
        # Do something when file changes
        print(f"Custom handler: {file_path}")
        # Send notification, update cache, etc.
    
    monitor.on('modified', my_custom_callback)
```

## Integration with Existing RAG App

### 1. Add to Your Existing FastAPI App

Copy the relevant parts to your existing FastAPI application:

```python
# In your existing FastAPI app
from ragversion import AsyncVersionTracker
from ragversion.integrations.langchain import LangChainSync

# Initialize tracker
tracker = AsyncVersionTracker(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_KEY")
)

# Add change tracking endpoints
@app.get("/api/documents")
async def list_documents():
    documents = await tracker.storage.list_documents(limit=50)
    return {"documents": documents}

@app.post("/api/sync")
async def sync_documents():
    sync = LangChainSync(tracker, text_splitter, embeddings, vectorstore)
    events = await sync.sync_directory("./documents")
    return {"synced": len(events)}
```

### 2. Use in Your RAG Pipeline

```python
# Before querying, check for changes
async def query_with_update(query: str):
    # Sync latest changes
    sync = LangChainSync(tracker, text_splitter, embeddings, vectorstore)
    await sync.sync_directory("./documents")
    
    # Perform RAG query
    results = await rag_chain.ainvoke(query)
    return results
```

## Client Examples

### Python Client

```python
import httpx

async def get_recent_changes():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/changes?limit=10")
        return response.json()

async def get_document_chunks(file_path: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/api/documents/{file_path}/chunks")
        return response.json()
```

### JavaScript/TypeScript Client

```typescript
async function getRecentChanges() {
  const response = await fetch('http://localhost:8000/api/changes?limit=10');
  return response.json();
}

async function syncDocuments() {
  const response = await fetch('http://localhost:8000/api/sync', {
    method: 'POST'
  });
  return response.json();
}
```

## File Structure

```
fastapi_integration/
├── main.py              # Main FastAPI application
├── config.py            # Configuration management
├── monitor.py           # Background change monitoring
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
├── documents/           # Directory to monitor (create this)
└── README.md           # This file
```

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_KEY` | Supabase anon key | Required |
| `DOCUMENTS_DIRECTORY` | Directory to monitor | `./documents` |
| `MONITOR_INTERVAL` | Check interval in seconds | `30` |
| `SYNC_ON_STARTUP` | Sync on server startup | `true` |

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Using Systemd

Create `/etc/systemd/system/ragversion-api.service`:

```ini
[Unit]
Description=RAGVersion API Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/fastapi_integration
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl enable ragversion-api
sudo systemctl start ragversion-api
```

## Troubleshooting

### Issue: Documents not syncing

**Solution**: Check if the documents directory path is correct in `.env` and the directory exists.

### Issue: WebSocket not connecting

**Solution**: Ensure CORS is enabled (it is by default) and the URL is correct (`ws://localhost:8000/ws/changes`).

### Issue: Monitoring not detecting changes

**Solution**: 
- Verify `MONITOR_INTERVAL` is set correctly
- Check if the monitor is running by calling `/api/stats`
- Ensure file paths are absolute or relative to the correct directory

## Next Steps

1. **Customize the API**: Add authentication, rate limiting, etc.
2. **Add Vector Store**: Configure embeddings and vector store for full RAG
3. **Build Frontend**: Create a dashboard using React, Vue, or any framework
4. **Add Monitoring**: Integrate with Prometheus, Grafana, etc.
5. **Scale Up**: Deploy with multiple workers using Gunicorn + Uvicorn

## Support

For issues or questions, refer to the main RAGVersion documentation or create an issue in the repository.

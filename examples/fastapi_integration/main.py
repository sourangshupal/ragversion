import os
import hashlib
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from ragversion import AsyncVersionTracker
from ragversion.integrations.langchain import LangChainSync
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings
from monitor import ChangeMonitor

load_dotenv()

app = FastAPI(
    title="RAGVersion API",
    description="FastAPI integration with RAGVersion for tracking document changes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tracker = AsyncVersionTracker(
    supabase_url=settings.supabase_url,
    supabase_key=settings.supabase_key
)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
embeddings = None
vectorstore = None

monitor = ChangeMonitor(tracker, interval=settings.monitor_interval)

active_websockets: List[WebSocket] = []

class SyncResponse(BaseModel):
    synced_files: int
    events: List[dict]
    duration_ms: int

class DocumentInfo(BaseModel):
    file_path: str
    current_version: int
    content_hash: str
    file_size: int
    file_type: str
    created_at: datetime
    updated_at: datetime

class VersionInfo(BaseModel):
    version_number: int
    change_type: str
    content_hash: str
    created_at: datetime

class ChunkInfo(BaseModel):
    index: int
    content_preview: str
    length: int
    hash: str

class ChangeSummary(BaseModel):
    file_path: str
    change_type: str
    previous_version: Optional[int]
    current_version: int
    timestamp: datetime

@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.documents_directory, exist_ok=True)
    
    async def log_change_to_db(file_path: str, *args):
        print(f"📝 Change logged: {file_path}")
    
    async def notify_websockets(file_path: str, change_type: str, *args):
        message = {
            "type": "change",
            "file_path": file_path,
            "change_type": change_type,
            "timestamp": datetime.now().isoformat()
        }
        for ws in active_websockets:
            try:
                await ws.send_json(message)
            except:
                pass
    
    monitor.on('created', log_change_to_db)
    monitor.on('modified', log_change_to_db)
    monitor.on('deleted', log_change_to_db)
    monitor.on('created', lambda fp: notify_websockets(fp, 'created'))
    monitor.on('modified', lambda fp: notify_websockets(fp, 'modified'))
    monitor.on('deleted', lambda fp: notify_websockets(fp, 'deleted'))
    
    await monitor.start(settings.documents_directory)
    
    if settings.sync_on_startup:
        await sync_directory()

@app.on_event("shutdown")
async def shutdown_event():
    await monitor.stop()

@app.get("/")
async def root():
    return {
        "message": "RAGVersion API",
        "version": "1.0.0",
        "endpoints": {
            "changes": "/api/changes",
            "documents": "/api/documents",
            "sync": "/api/sync",
            "stats": "/api/stats",
            "websocket": "/ws/changes"
        }
    }

@app.get("/api/stats")
async def get_stats():
    total_docs = await tracker.storage.list_documents(limit=10000)
    documents = await tracker.storage.list_documents(limit=10, order_by="updated_at", descending=True)
    
    return {
        "total_documents": len(total_docs),
        "monitored_directory": settings.documents_directory,
        "monitor_interval_seconds": settings.monitor_interval,
        "monitor_active": monitor._running,
        "recent_changes": [
            {
                "file_path": doc.file_path,
                "current_version": doc.current_version,
                "updated_at": doc.updated_at
            }
            for doc in documents
        ]
    }

@app.get("/api/changes", response_model=List[ChangeSummary])
async def get_changes(limit: int = 20, file_type: Optional[str] = None):
    documents = await tracker.storage.list_documents(
        limit=limit,
        order_by="updated_at",
        descending=True
    )
    
    if file_type:
        documents = [doc for doc in documents if doc.file_path.endswith(file_type)]
    
    changes = []
    for doc in documents:
        latest = await tracker.storage.get_latest_version(doc.id)
        changes.append(ChangeSummary(
            file_path=doc.file_path,
            change_type=latest.change_type.value,
            previous_version=latest.version_number - 1 if latest.version_number > 1 else None,
            current_version=latest.version_number,
            timestamp=latest.created_at
        ))
    
    return changes

@app.get("/api/documents", response_model=List[DocumentInfo])
async def list_documents(limit: int = 50, file_type: Optional[str] = None):
    documents = await tracker.storage.list_documents(limit=limit)
    
    if file_type:
        documents = [doc for doc in documents if doc.file_path.endswith(file_type)]
    
    return [
        DocumentInfo(
            file_path=doc.file_path,
            current_version=doc.current_version,
            content_hash=doc.content_hash,
            file_size=doc.file_size,
            file_type=Path(doc.file_path).suffix,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        for doc in documents
    ]

@app.get("/api/documents/{file_path:path}")
async def get_document(file_path: str):
    doc = await tracker.storage.get_document_by_path(file_path)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    versions = await tracker.storage.list_versions(doc.id)
    
    return {
        "file_path": doc.file_path,
        "current_version": doc.current_version,
        "file_size": doc.file_size,
        "file_type": Path(doc.file_path).suffix,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "total_versions": len(versions),
        "versions": [
            {
                "version_number": v.version_number,
                "change_type": v.change_type.value,
                "content_hash": v.content_hash,
                "created_at": v.created_at
            }
            for v in versions
        ]
    }

@app.get("/api/documents/{file_path:path}/versions/{version_number}")
async def get_version(file_path: str, version_number: int):
    doc = await tracker.storage.get_document_by_path(file_path)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    version = await tracker.storage.get_version_by_number(doc.id, version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    content = await tracker.storage.get_content(version.id)
    
    return {
        "file_path": file_path,
        "version_number": version.version_number,
        "change_type": version.change_type.value,
        "content_hash": version.content_hash,
        "created_at": version.created_at,
        "content": content,
        "content_length": len(content)
    }

@app.get("/api/documents/{file_path:path}/chunks")
async def get_document_chunks(file_path: str):
    doc = await tracker.storage.get_document_by_path(file_path)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    latest = await tracker.storage.get_latest_version(doc.id)
    content = await tracker.storage.get_content(latest.id)
    
    chunks = text_splitter.split_text(content)
    
    return {
        "file_path": file_path,
        "version": latest.version_number,
        "total_chunks": len(chunks),
        "chunks": [
            {
                "index": i,
                "content_preview": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                "length": len(chunk),
                "hash": hashlib.sha256(chunk.encode()).hexdigest()[:16]
            }
            for i, chunk in enumerate(chunks)
        ]
    }

@app.post("/api/sync", response_model=SyncResponse)
async def sync_directory(background_tasks: BackgroundTasks):
    start_time = datetime.now()
    
    sync = LangChainSync(tracker, text_splitter, embeddings, vectorstore)
    events = await sync.sync_directory(settings.documents_directory)
    
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    background_tasks.add_task(monitor.sync_now, settings.documents_directory)
    
    return SyncResponse(
        synced_files=len(events),
        events=[
            {
                "file_path": event.file_path,
                "change_type": event.change_type.value,
                "previous_version": event.previous_version,
                "current_version": event.current_version
            }
            for event in events
        ],
        duration_ms=duration_ms
    )

@app.post("/api/sync/{file_path:path}")
async def sync_file(file_path: str, background_tasks: BackgroundTasks):
    full_path = os.path.join(settings.documents_directory, file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    start_time = datetime.now()
    
    sync = LangChainSync(tracker, text_splitter, embeddings, vectorstore)
    events = await sync.sync_file(full_path)
    
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    return {
        "file_path": file_path,
        "synced": len(events) > 0,
        "events": [
            {
                "change_type": event.change_type.value,
                "previous_version": event.previous_version,
                "current_version": event.current_version
            }
            for event in events
        ],
        "duration_ms": duration_ms
    }

@app.get("/api/compare/{file_path:path}")
async def compare_versions(file_path: str, v1: int, v2: int):
    doc = await tracker.storage.get_document_by_path(file_path)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    version1 = await tracker.storage.get_version_by_number(doc.id, v1)
    version2 = await tracker.storage.get_version_by_number(doc.id, v2)
    
    if not version1 or not version2:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    content1 = await tracker.storage.get_content(version1.id)
    content2 = await tracker.storage.get_content(version2.id)
    
    chunks1 = text_splitter.split_text(content1)
    chunks2 = text_splitter.split_text(content2)
    
    hash1 = [hashlib.sha256(c.encode()).hexdigest() for c in chunks1]
    hash2 = [hashlib.sha256(c.encode()).hexdigest() for c in chunks2]
    
    new_chunks = [i for i, h in enumerate(hash2) if h not in hash1]
    removed_chunks = [i for i, h in enumerate(hash1) if h not in hash2]
    
    return {
        "file_path": file_path,
        "version1": {
            "number": v1,
            "content_length": len(content1),
            "total_chunks": len(chunks1)
        },
        "version2": {
            "number": v2,
            "content_length": len(content2),
            "total_chunks": len(chunks2)
        },
        "difference": {
            "content_length_diff": len(content2) - len(content1),
            "new_chunks_count": len(new_chunks),
            "removed_chunks_count": len(removed_chunks),
            "new_chunk_indices": new_chunks,
            "removed_chunk_indices": removed_chunks
        }
    }

@app.websocket("/ws/changes")
async def websocket_changes(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

@app.delete("/api/documents/{file_path:path}")
async def delete_document(file_path: str):
    doc = await tracker.storage.get_document_by_path(file_path)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    await tracker.storage.delete_document(doc.id)
    
    return {"message": f"Document {file_path} deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import asyncio
import hashlib
import os
from typing import Callable, Dict, List, Optional
from datetime import datetime
from ragversion import AsyncVersionTracker, ChangeEvent

class ChangeMonitor:
    def __init__(self, tracker: AsyncVersionTracker, interval: int = 30):
        self.tracker = tracker
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.callbacks: Dict[str, List[Callable]] = {
            'created': [],
            'modified': [],
            'deleted': [],
            'restored': []
        }
        self.known_files: Dict[str, str] = {}
    
    def on(self, event_type: str, callback: Callable):
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def off(self, event_type: str, callback: Callable):
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
    
    async def _emit(self, event_type: str, *args, **kwargs):
        for callback in self.callbacks.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                print(f"Error in callback: {e}")
    
    def _compute_file_hash(self, file_path: str) -> str:
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    async def _check_file(self, file_path: str):
        existing = await self.tracker.storage.get_document_by_path(file_path)
        current_hash = self._compute_file_hash(file_path)
        
        if not existing:
            await self._emit('created', file_path, current_hash)
            self.known_files[file_path] = current_hash
        elif current_hash and current_hash != self.known_files.get(file_path, ""):
            latest = await self.tracker.storage.get_latest_version(existing.id)
            if latest.content_hash != current_hash:
                await self._emit('modified', file_path, 
                               existing.current_version, 
                               existing.current_version + 1,
                               current_hash)
                self.known_files[file_path] = current_hash
    
    async def _scan_directory(self, directory: str):
        current_files = set()
        
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.abspath(os.path.join(root, file))
                current_files.add(file_path)
                await self._check_file(file_path)
        
        deleted_files = set(self.known_files.keys()) - current_files
        for file_path in deleted_files:
            await self._emit('deleted', file_path)
            del self.known_files[file_path]
    
    async def start(self, directory: str):
        if self._running:
            return
        
        self._running = True
        
        async def monitor_loop():
            while self._running:
                await self._scan_directory(directory)
                await asyncio.sleep(self.interval)
        
        self._task = asyncio.create_task(monitor_loop())
    
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def sync_now(self, directory: str):
        await self._scan_directory(directory)

# Real-Time File Watching

Automatically track document changes without manual intervention using RAGVersion's file watching capabilities.

## Overview

The file watcher monitors directories for file system events (create, modify, delete) and automatically tracks changes in real-time. This eliminates the need for manual `ragversion track` commands.

**Key Features:**
- ✅ **Real-time monitoring** - Instantly detect file changes
- ✅ **Pattern matching** - Watch specific file types (*.md, *.txt, etc.)
- ✅ **Recursive watching** - Monitor nested directories
- ✅ **Debouncing** - Avoid duplicate tracking for rapid changes
- ✅ **Graceful shutdown** - Handle SIGINT/SIGTERM signals
- ✅ **Custom callbacks** - React to changes with custom logic
- ✅ **Low overhead** - Efficient event-driven architecture

---

## Quick Start

### CLI Usage

**Basic watching:**
```bash
# Watch a directory
ragversion watch ./docs

# Watch multiple directories
ragversion watch ./docs ./guides ./api
```

**Watch specific file types:**
```bash
# Watch only Markdown files
ragversion watch ./docs --pattern "*.md"

# Watch multiple patterns
ragversion watch ./docs -p "*.md" -p "*.txt" -p "*.pdf"
```

**Ignore patterns:**
```bash
# Ignore draft files and backups
ragversion watch ./docs --ignore "*.draft" --ignore "*.bak" --ignore "*.tmp"
```

**Non-recursive watching:**
```bash
# Watch only top-level files (not subdirectories)
ragversion watch ./docs --no-recursive
```

**Verbose logging:**
```bash
# Enable detailed logging
ragversion watch ./docs --verbose
```

---

## Python API

### Basic Usage

```python
import asyncio
from ragversion import AsyncVersionTracker, watch_directory
from ragversion.storage import SQLiteStorage

async def main():
    storage = SQLiteStorage()
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    # Start watching (blocks until stopped)
    await watch_directory(tracker, "./docs")

    await tracker.close()

asyncio.run(main())
```

### Watch Multiple Paths

```python
from ragversion import watch_paths

async def main():
    async with AsyncVersionTracker(storage=storage) as tracker:
        await watch_paths(
            tracker,
            paths=["./docs", "./guides", "README.md"],
            patterns=["*.md", "*.txt"],
            recursive=True
        )

asyncio.run(main())
```

### With Custom Callback

```python
from ragversion import watch_directory

async def on_change(change):
    """Custom callback for change events."""
    print(f"📄 {change.change_type.value}: {change.file_name}")
    print(f"   Version: {change.version_number}")
    print(f"   Hash: {change.content_hash[:8]}...")

async def main():
    async with AsyncVersionTracker(storage=storage) as tracker:
        await watch_directory(
            tracker,
            "./docs",
            patterns=["*.md"],
            on_change=on_change
        )

asyncio.run(main())
```

### FileWatcher Class

For more control, use the `FileWatcher` class directly:

```python
from ragversion import FileWatcher

async def main():
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    watcher = FileWatcher(
        tracker=tracker,
        paths=["./docs", "./guides"],
        patterns=["*.md", "*.txt"],
        ignore_patterns=["*.draft", "*.tmp"],
        recursive=True,
        on_change=lambda change: print(f"Changed: {change.file_name}")
    )

    # Start watching
    watcher.start()

    try:
        # Process events
        await watcher.process_events()
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        watcher.stop()
        await tracker.close()

asyncio.run(main())
```

### Background Watching

Run watcher in the background while doing other work:

```python
async def main():
    async with AsyncVersionTracker(storage=storage) as tracker:
        watcher = FileWatcher(
            tracker=tracker,
            paths=["./docs"],
            patterns=["*.md"]
        )

        # Start in background
        watcher_task = await watcher.watch_in_background()

        # Do other work
        await asyncio.sleep(60)  # Watch for 60 seconds

        # Stop watcher
        watcher.stop()
        await watcher_task  # Wait for cleanup

asyncio.run(main())
```

---

## Configuration

### File Patterns

Control which files are watched using glob patterns:

```python
patterns = [
    "*.md",      # All Markdown files
    "*.txt",     # All text files
    "*.pdf",     # All PDF files
    "README.*",  # Any README file
]
```

### Ignore Patterns

Exclude files from watching:

```python
ignore_patterns = [
    "*.tmp",           # Temporary files
    "*.swp",           # Vim swap files
    "*~",              # Backup files
    ".git/*",          # Git directory
    ".DS_Store",       # macOS metadata
    "*.pyc",           # Python bytecode
    "__pycache__/*",   # Python cache
    ".ragversion/*",   # RAGVersion data
    "ragversion.db*",  # SQLite database files
]
```

**Note:** These patterns are built-in defaults and are always ignored.

### Debouncing

The watcher automatically debounces rapid file changes (default: 1 second). This prevents tracking the same file multiple times in quick succession.

**Example scenario:**
```
00:00.000 - File modified
00:00.100 - File modified (ignored - within 1s)
00:00.500 - File modified (ignored - within 1s)
00:01.100 - File modified (tracked - >1s elapsed)
```

---

## Use Cases

### 1. Development Environment

Automatically track documentation changes during development:

```bash
# Terminal 1: Start watcher
ragversion watch ./docs -p "*.md" --verbose

# Terminal 2: Edit documentation
vim docs/api.md
# Changes automatically tracked!
```

### 2. Continuous Monitoring

Monitor documentation directories 24/7:

```python
import asyncio
from ragversion import AsyncVersionTracker, FileWatcher
from ragversion.storage import SQLiteStorage

async def main():
    storage = SQLiteStorage(db_path="/var/lib/ragversion/ragversion.db")
    tracker = AsyncVersionTracker(storage=storage)
    await tracker.initialize()

    watcher = FileWatcher(
        tracker=tracker,
        paths=["/data/documents", "/data/manuals"],
        patterns=["*.pdf", "*.docx", "*.md"],
        recursive=True,
    )

    print("🔄 RAGVersion Watcher started - monitoring 24/7")
    await watcher.watch()  # Runs indefinitely

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Custom Notifications

Send notifications when documents change:

```python
import asyncio
from ragversion import watch_directory

async def send_slack_notification(change):
    """Send Slack notification on change."""
    import httpx

    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    message = {
        "text": f"📄 Document {change.change_type.value}: {change.file_name}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Document Change Detected*\n"
                        f"• File: `{change.file_name}`\n"
                        f"• Type: {change.change_type.value}\n"
                        f"• Version: {change.version_number}\n"
                        f"• Time: {change.timestamp}"
                    )
                }
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=message)

async def main():
    async with AsyncVersionTracker(storage=storage) as tracker:
        await watch_directory(
            tracker,
            "./critical-docs",
            patterns=["*.md", "*.pdf"],
            on_change=send_slack_notification
        )

asyncio.run(main())
```

### 4. Integration with RAG Systems

Automatically update vector stores when documents change:

```python
import asyncio
from ragversion import watch_directory
from langchain.vectorstores import Qdrant
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vectorstore = Qdrant(...)

async def update_vectorstore(change):
    """Update vector store on document change."""
    if change.change_type.value in ["created", "modified"]:
        # Load document
        with open(change.file_path, 'r') as f:
            content = f.read()

        # Update vector store
        vectorstore.add_texts([content], metadatas=[{
            "file_name": change.file_name,
            "version": change.version_number,
            "hash": change.content_hash
        }])

        print(f"✅ Updated vector store: {change.file_name}")

    elif change.change_type.value == "deleted":
        # Remove from vector store
        vectorstore.delete(filter={"file_name": change.file_name})
        print(f"🗑️ Removed from vector store: {change.file_name}")

async def main():
    async with AsyncVersionTracker(storage=storage) as tracker:
        await watch_directory(
            tracker,
            "./docs",
            patterns=["*.md"],
            on_change=update_vectorstore
        )

asyncio.run(main())
```

---

## Daemon Mode

Run watcher as a background daemon (Unix systems):

### Using systemd

Create `/etc/systemd/system/ragversion-watcher.service`:

```ini
[Unit]
Description=RAGVersion File Watcher
After=network.target

[Service]
Type=simple
User=ragversion
WorkingDirectory=/var/lib/ragversion
ExecStart=/usr/local/bin/ragversion watch /data/documents -p "*.md" -p "*.txt"
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable ragversion-watcher
sudo systemctl start ragversion-watcher
sudo systemctl status ragversion-watcher
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install RAGVersion
RUN pip install ragversion[all]

# Create data directory
RUN mkdir -p /data/documents /var/lib/ragversion

# Set working directory
WORKDIR /app

# Run watcher
CMD ["ragversion", "watch", "/data/documents", "-p", "*.md", "-p", "*.txt"]
```

**Run container:**
```bash
docker build -t ragversion-watcher .

docker run -d \
  --name ragversion-watcher \
  -v /path/to/docs:/data/documents:ro \
  -v ragversion-data:/var/lib/ragversion \
  --restart unless-stopped \
  ragversion-watcher
```

---

## Performance

### Resource Usage

**Typical resource usage (watching 1000 files):**
- CPU: <1% (idle), ~5% (active tracking)
- Memory: ~50-100 MB
- Disk I/O: Minimal (event-driven)

### Scaling

**Small scale (<1000 files):**
- Watch all files directly
- Debouncing handles occasional bursts

**Medium scale (1000-10,000 files):**
- Use specific patterns to reduce watch count
- Consider multiple watchers for different directories
- Increase debounce time if needed

**Large scale (>10,000 files):**
- Use multiple watcher processes
- Consider hierarchical watching (per-project watchers)
- Monitor system file descriptor limits

**System limits:**
```bash
# Check current limit
ulimit -n

# Increase limit (temporary)
ulimit -n 10000

# Increase limit (permanent, add to /etc/security/limits.conf)
* soft nofile 10000
* hard nofile 100000
```

---

## Troubleshooting

### Issue: Watcher Not Detecting Changes

**Symptoms:**
- Files change but watcher doesn't detect them
- No output from watcher

**Solutions:**

1. **Check patterns:**
   ```bash
   ragversion watch ./docs -p "*.md" --verbose
   # Verify your files match the pattern
   ```

2. **Check ignore patterns:**
   ```bash
   # Temporarily disable ignore patterns for debugging
   # (edit ragversion/watcher.py and set ignore_patterns=[])
   ```

3. **Verify file system events:**
   ```bash
   # Use inotify-tools to verify OS generates events
   inotifywait -m -r ./docs
   ```

### Issue: High CPU Usage

**Symptoms:**
- Watcher uses excessive CPU
- System becomes slow

**Solutions:**

1. **Reduce watch scope:**
   ```bash
   # Watch specific directories instead of root
   ragversion watch ./docs/api ./docs/guides
   ```

2. **Use non-recursive watching:**
   ```bash
   ragversion watch ./docs --no-recursive
   ```

3. **Increase debounce time:**
   ```python
   # Edit watcher code to increase debounce
   self._debounce_seconds = 2.0  # Default: 1.0
   ```

### Issue: Too Many Open Files

**Symptoms:**
- Error: "Too many open files"
- Watcher crashes

**Solutions:**

1. **Increase file descriptor limit:**
   ```bash
   ulimit -n 10000
   ```

2. **Watch fewer directories:**
   ```bash
   # Split into multiple watchers
   ragversion watch ./docs/section1 &
   ragversion watch ./docs/section2 &
   ```

### Issue: Watcher Stops After Inactivity

**Symptoms:**
- Watcher stops responding after idle period

**Solution:**

This should not happen as the watcher runs continuously. If it does:

1. Check for system sleep/hibernation
2. Verify network storage is not timing out
3. Check system logs for errors
4. Use `--verbose` to see detailed activity

---

## Best Practices

### ✅ DO

1. **Use specific patterns** to reduce overhead:
   ```bash
   ragversion watch ./docs -p "*.md" -p "*.txt"
   ```

2. **Set up proper logging** for production:
   ```python
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('/var/log/ragversion-watcher.log'),
           logging.StreamHandler()
       ]
   )
   ```

3. **Handle signals gracefully** in custom implementations:
   ```python
   import signal

   def shutdown(signum, frame):
       watcher.stop()

   signal.signal(signal.SIGINT, shutdown)
   signal.signal(signal.SIGTERM, shutdown)
   ```

4. **Monitor watcher health** in production:
   ```python
   # Add heartbeat/health check
   last_heartbeat = time.time()

   def on_change(change):
       global last_heartbeat
       last_heartbeat = time.time()
   ```

### ❌ DON'T

1. **Don't watch too many files** without patterns
2. **Don't watch network drives** (high latency)
3. **Don't watch temp directories** or caches
4. **Don't run multiple watchers** on same directory
5. **Don't forget to handle shutdown** signals

---

## API Reference

### `watch_directory()`

```python
async def watch_directory(
    tracker: AsyncVersionTracker,
    path: str,
    patterns: Optional[List[str]] = None,
    ignore_patterns: Optional[List[str]] = None,
    recursive: bool = True,
    on_change: Optional[Callable[[ChangeEvent], None]] = None,
) -> None
```

Watch a directory for changes and automatically track them.

**Parameters:**
- `tracker` - AsyncVersionTracker instance
- `path` - Directory path to watch
- `patterns` - File patterns to watch (e.g., ["*.md", "*.txt"])
- `ignore_patterns` - Patterns to ignore (e.g., ["*.tmp", ".git/*"])
- `recursive` - Watch subdirectories recursively
- `on_change` - Optional callback for change events

### `watch_paths()`

```python
async def watch_paths(
    tracker: AsyncVersionTracker,
    paths: List[str],
    patterns: Optional[List[str]] = None,
    ignore_patterns: Optional[List[str]] = None,
    recursive: bool = True,
    on_change: Optional[Callable[[ChangeEvent], None]] = None,
) -> None
```

Watch multiple paths for changes and automatically track them.

**Parameters:**
- `tracker` - AsyncVersionTracker instance
- `paths` - List of paths to watch (files or directories)
- `patterns` - File patterns to watch
- `ignore_patterns` - Patterns to ignore
- `recursive` - Watch subdirectories recursively
- `on_change` - Optional callback for change events

### `FileWatcher` Class

```python
class FileWatcher:
    def __init__(
        self,
        tracker: AsyncVersionTracker,
        paths: List[str],
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        recursive: bool = True,
        on_change: Optional[Callable[[ChangeEvent], None]] = None,
    ) -> None

    def start(self) -> None
    def stop(self) -> None
    async def watch(self) -> None
    async def watch_in_background(self) -> asyncio.Task
```

---

## Further Reading

- [RAGVersion Documentation](../DOCUMENTATION.md) - Full API reference
- [CLI Guide](guide/cli.md) - Command-line usage
- [Python API](api/tracker.md) - AsyncVersionTracker API
- [Integration Examples](examples/basic.md) - Real-world examples

---

**Last Updated:** January 20, 2026 (v0.5.0)

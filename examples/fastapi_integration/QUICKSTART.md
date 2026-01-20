# Quick Start Guide

Get up and running with RAGVersion FastAPI integration in 5 minutes!

## Step 1: Install Dependencies

```bash
cd examples/fastapi_integration
pip install -r requirements.txt
```

## Step 2: Configure Environment

Copy the example environment file and add your Supabase credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your Supabase URL and key:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

## Step 3: Start the Server

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Test the API

Open a new terminal and try these commands:

### Check system stats
```bash
curl http://localhost:8000/api/stats
```

### List documents
```bash
curl http://localhost:8000/api/documents
```

### Get document chunks
```bash
curl http://localhost:8000/api/documents/documents/sample.txt/chunks
```

### Sync all documents
```bash
curl -X POST http://localhost:8000/api/sync
```

## Step 5: Run the Python Client

```bash
python client_example.py
```

This will demonstrate all the API features with example output.

## Step 6: Try Real-Time Updates

1. Start the server: `python main.py`
2. Open another terminal and create a WebSocket client:
```python
import asyncio
import websockets
import json

async def listen():
    async with websockets.connect("ws://localhost:8000/ws/changes") as ws:
        print("Connected to change notifications...")
        while True:
            message = await ws.recv()
            data = json.loads(message)
            print(f"📢 Change: {data['file_path']} - {data['change_type']}")

asyncio.run(listen())
```

3. Modify a file in the `documents/` directory
4. Watch the real-time notification!

## Common Issues

### "Document not found" error
Make sure the file path includes the full path from the project root, e.g., `documents/sample.txt` not just `sample.txt`.

### "Supabase connection failed"
Check your `.env` file has the correct `SUPABASE_URL` and `SUPABASE_KEY`.

### "Module not found" errors
Make sure you've installed all dependencies: `pip install -r requirements.txt`

## Next Steps

- Read the full [README.md](./README.md) for detailed documentation
- Explore the API endpoints using the interactive docs at `http://localhost:8000/docs`
- Integrate with your existing FastAPI application
- Build a custom dashboard using the API

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

These provide a web interface to test all endpoints!

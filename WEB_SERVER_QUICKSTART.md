# RAGVersion Web Server - Quick Start Guide

Get the RAGVersion web dashboard up and running in 3 simple steps.

---

## Prerequisites

- Python 3.12+ installed
- RAGVersion project cloned
- Virtual environment set up

---

## Step 1: Install Dependencies

```bash
cd /Users/sourangshupal/Downloads/ragversion

# Activate virtual environment
source .venv/bin/activate

# Install API dependencies (if not already installed)
pip install -e ".[api]"
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Jinja2 (templating)

---

## Step 2: Start the Server

```bash
python -m uvicorn ragversion.api.main:app --host 0.0.0.0 --port 6699
```

You should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:6699 (Press CTRL+C to quit)
```

---

## Step 3: Access the Web Interface

Open your browser and navigate to:

### 🌐 Web Dashboard
- **Home:** http://localhost:6699/
- **Documents:** http://localhost:6699/documents
- **Track Files:** http://localhost:6699/track
- **Analytics:** http://localhost:6699/analytics
- **Integrations:** http://localhost:6699/integrations

### 📚 API Documentation
- **Swagger UI:** http://localhost:6699/api/docs
- **ReDoc:** http://localhost:6699/api/redoc
- **Health Check:** http://localhost:6699/api/health

---

## Optional: Development Mode (Auto-Reload)

For development, enable auto-reload to automatically restart the server when code changes:

```bash
python -m uvicorn ragversion.api.main:app --host 0.0.0.0 --port 6699 --reload
```

---

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## Troubleshooting

### Port Already in Use

If you see `Address already in use`, kill the process using port 6699:

```bash
# Find and kill process on port 6699
lsof -ti:6699 | xargs kill -9
```

Then start the server again.

### Module Not Found Errors

If you see `ModuleNotFoundError: No module named 'fastapi'`:

```bash
# Make sure you installed the API dependencies
pip install -e ".[api]"
```

### Storage Backend Issues

If the health check shows `storage_healthy: false`:

- **Using SQLite (default):** The database will be created automatically. This warning is normal on first run.
- **Using Supabase:** Check your `.env` file has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.

---

## Configuration

The server reads configuration from `.env` file. Key settings:

```bash
# Storage Backend
RAGVERSION_STORAGE_BACKEND=sqlite  # or "supabase"
RAGVERSION_SQLITE_PATH=./ragversion.db

# API Settings
RAGVERSION_API_HOST=0.0.0.0
RAGVERSION_API_PORT=6699
RAGVERSION_API_CORS_ENABLED=true
```

---

## What's Included

### Phase 1 Features ✅
- ✅ Modern UI with Tailwind CSS
- ✅ Real-time updates with HTMX
- ✅ Interactive components with Alpine.js
- ✅ Data visualizations with Chart.js
- ✅ Document tracking from web UI
- ✅ Advanced search and filtering
- ✅ WebSocket live activity feed

### Phase 2 Features ✅
- ✅ Advanced analytics dashboard
- ✅ Timeline charts and trends
- ✅ Activity calendar (GitHub-style)
- ✅ Enhanced diff viewer with syntax highlighting
- ✅ Integration management UI (LangChain/LlamaIndex)
- ✅ Storage growth visualization

---

## Next Steps

1. **Track Some Documents:**
   - Click "Track" in the navigation
   - Enter a file path or directory
   - Watch the dashboard update in real-time

2. **View Analytics:**
   - Navigate to "Analytics"
   - See charts and visualizations of your data

3. **Explore API:**
   - Visit http://localhost:6699/api/docs
   - Try out API endpoints interactively

4. **Check Integrations:**
   - Navigate to "Integrations"
   - Set up LangChain or LlamaIndex sync

---

## Production Deployment

For production use, see the full deployment guide in `WEB_UI_ENHANCEMENTS.md` which covers:

- Using Gunicorn with multiple workers
- Setting up HTTPS
- Configuring reverse proxy
- Enabling security features
- Performance optimization

---

## Getting Help

- **Documentation:** See `WEB_UI_ENHANCEMENTS.md` for detailed implementation docs
- **Test Report:** See `WEB_SERVER_TEST_REPORT.md` for verification results
- **API Guide:** See `docs/API_GUIDE.md` for API documentation
- **Issues:** Report bugs at https://github.com/yourusername/ragversion/issues

---

**Server Version:** 0.11.0
**Last Updated:** 2026-01-20

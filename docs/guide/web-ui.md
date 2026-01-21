# Web UI Guide

RAGVersion includes a modern web-based dashboard that provides a visual interface for managing document tracking, viewing analytics, and monitoring changes in real-time.

!!! success "🎉 New in v0.11.0: Modern Web Dashboard"
    **Complete web UI** with real-time updates, advanced analytics, and integration management!

## Overview

The RAGVersion Web UI provides:

- 📊 **Interactive Dashboard** - Real-time statistics and visualizations
- 📁 **Document Management** - Browse, search, and filter tracked documents
- 🔍 **Version Comparison** - Visual diff viewer with syntax highlighting
- 📈 **Advanced Analytics** - Timeline charts, activity calendars, and insights
- 🔗 **Integration Management** - Configure and monitor LangChain/LlamaIndex sync
- ⚡ **Real-Time Updates** - WebSocket-powered live activity feed

## Starting the Web Server

### Quick Start

```bash
# Install API dependencies
pip install "ragversion[api]"

# Start the server
python -m uvicorn ragversion.api.main:app --host 0.0.0.0 --port 6699
```

The web interface will be available at **http://localhost:6699**

### Using the CLI (Alternative)

```bash
# Start server with default settings
ragversion serve

# Custom host and port
ragversion serve --host 0.0.0.0 --port 8080

# Development mode with auto-reload
ragversion serve --reload
```

### Configuration

The web server uses environment variables from `.env`:

```bash
# Storage Backend
RAGVERSION_STORAGE_BACKEND=sqlite  # or "supabase"
RAGVERSION_SQLITE_PATH=./ragversion.db

# Supabase (if using)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# API Configuration
RAGVERSION_API_HOST=0.0.0.0
RAGVERSION_API_PORT=6699
RAGVERSION_API_CORS_ENABLED=true
RAGVERSION_API_CORS_ORIGINS=*
```

## Dashboard

The dashboard provides an at-a-glance view of your document tracking system.

![Dashboard Overview](../images/dashboard.png)

### Features

#### Statistics Cards
Four key metrics displayed prominently:

- **Total Documents** - Number of tracked documents
- **Total Versions** - All versions across documents
- **Storage Used** - Total storage consumed
- **Average Versions** - Mean versions per document

#### File Type Distribution
Interactive doughnut chart showing document breakdown by file type (PDF, DOCX, Markdown, etc.)

#### Recent Activity
Real-time feed of document changes:

- 🟢 Created - New documents tracked
- 🔵 Modified - Existing documents updated
- 🔴 Deleted - Documents removed
- 🟡 Restored - Previously deleted documents restored

The activity feed updates automatically via WebSocket connection.

#### Top Documents
Table showing most active documents sorted by:

- Version count
- Last updated
- File size
- Change frequency

## Document Management

Navigate to **Documents** to browse and manage all tracked files.

### Search and Filter

**Search Bar:**
- Real-time search (500ms debounce)
- Searches filename and path
- Case-insensitive matching

**File Type Filter:**
```
- All Types
- PDF
- DOCX
- TXT
- MD (Markdown)
- [Custom types from your data]
```

**Sort Options:**
- Last Updated (default)
- Date Created
- File Name (alphabetical)
- Version Count
- File Size

### Document List View

Each document displays:

- **File Name** - Clickable to view details
- **File Path** - Full path to document
- **Type Badge** - Color-coded file type
- **Version Badge** - Current version number (v1, v2, etc.)
- **Size** - File size in KB/MB
- **Last Updated** - Timestamp
- **Actions** - View or Delete

### Pagination

Navigate large document sets with:
- Previous/Next buttons
- Page indicators
- Configurable items per page (default: 50)

## Document Details

Click any document to view comprehensive details and version history.

### Overview Section

- **File Information** - Name, path, type, size
- **Current Version** - Latest version number
- **Total Versions** - Version count
- **Created/Updated** - Timestamps
- **Metadata** - Custom key-value pairs

### Version History Timeline

Chronological list of all versions:

```
v3 - Modified  2026-01-20 15:30:22  (Current)
v2 - Modified  2026-01-20 12:15:10
v1 - Created   2026-01-19 09:00:00
```

Each version shows:
- Version number
- Change type (Created/Modified/Deleted/Restored)
- Timestamp
- Content hash (for verification)
- Actions (View Content, Compare)

### Version Comparison

**Compare Button** - Select two versions to view differences

The diff viewer provides:

#### Unified View (Default)
Traditional diff format with:
- 🟢 Green lines - Added content
- 🔴 Red lines - Removed content
- ⚪ Gray lines - Context (unchanged)

#### Side-by-Side View
Split view showing:
- Left panel: Older version
- Right panel: Newer version
- Synchronized scrolling
- Highlighted changes

#### Features
- **Syntax Highlighting** - Automatic language detection (via Prism.js)
- **Line Numbers** - Toggle on/off
- **Change Statistics** - Additions, deletions, changes count
- **Similarity Score** - Percentage match between versions

## Tracking Documents

Navigate to **Track** to add new documents to the system.

### Tab Interface

#### Single File Tracking

Track individual files:

```
File Path: /path/to/document.pdf
Metadata (Optional): {"author": "John Doe", "category": "reports"}

[Track File Button]
```

**Metadata Format:** JSON key-value pairs for custom attributes

#### Directory Tracking

Track entire directories:

```
Directory Path: /path/to/documents/
File Patterns: *.pdf, *.docx, *.md
☑️ Recursive (search subdirectories)
Max Workers: 4 [slider: 1-16]

[Track Directory Button]
```

**Options:**
- **Recursive** - Include subdirectories
- **File Patterns** - Comma-separated glob patterns (e.g., `*.pdf, *.docx`)
- **Max Workers** - Parallel processing (1-16 workers)

### Real-Time Progress

When tracking directories, see:
- Progress bar with percentage
- Files processed count
- Success/failure indicators
- Error messages (if any)

### Results Display

After tracking completes:

```
✅ Successfully tracked 45 documents
   - 30 created
   - 12 modified
   - 3 unchanged

❌ Failed: 2 documents
   - /path/file1.pdf - Parse error
   - /path/file2.docx - Permission denied
```

## Analytics Dashboard

Navigate to **Analytics** for comprehensive insights and visualizations.

### Key Metrics Cards

- **Total Changes** - All modifications across time period
- **Active Documents** - Documents with multiple versions
- **Avg Changes/Day** - Daily change rate
- **Peak Activity** - Busiest day and count

### Timeline Charts

#### Version Growth
Line chart showing cumulative versions over time:
- X-axis: Date range (7, 30, 90, 365 days)
- Y-axis: Total version count
- Trend line with area fill

#### Storage Growth
Bar chart showing storage consumption:
- Weekly/monthly snapshots
- Size in MB/GB
- Growth rate indicators

### Change Type Distribution

Pie chart breaking down changes by type:
- 🟢 Created (new documents)
- 🔵 Modified (updates)
- 🔴 Deleted (removals)
- 🟡 Restored (recoveries)

### Activity Calendar

GitHub-style contribution heatmap showing:
- 365-day history
- Color intensity by activity level:
  - No activity (light gray)
  - 1-2 changes (light green)
  - 3-5 changes (medium green)
  - 6-10 changes (dark green)
  - 10+ changes (darkest green)
- Hover for daily totals

### Top Modified Documents

Leaderboard showing:
- Document name
- Total change count
- Visual bar chart
- Link to document details

### File Type Activity

Table breakdown by file type:
- Document count
- Total changes
- Average changes per document
- Activity percentage

### Time Range Selector

Filter analytics by period:
```
[7 Days] [30 Days] [90 Days] [365 Days] [All Time]
```

## Integration Management

Navigate to **Integrations** to configure framework synchronization.

### LangChain Integration

#### Status Card

```
┌─────────────────────────────┐
│ 🔗 LangChain                │
│ Vector store synchronization│
│                             │
│ Status: [Active/Inactive]   │
│                             │
│ Total Syncs: 127            │
│ Last Sync: 2m ago           │
│ Documents Synced: 1,234     │
│ Sync Status: ✓ Healthy     │
│                             │
│ [Trigger Sync] [Configure]  │
└─────────────────────────────┘
```

#### Quick Start Code

```python
from ragversion.integrations.langchain import LangChainSync

# Initialize sync
sync = LangChainSync(
    tracker=tracker,
    vector_store=your_vector_store
)

# Auto-sync on changes
tracker.on_change(sync.sync_on_change)
```

### LlamaIndex Integration

#### Status Card

```
┌─────────────────────────────┐
│ 🦙 LlamaIndex               │
│ Node-level tracking         │
│                             │
│ Status: [Active/Inactive]   │
│                             │
│ Total Syncs: 89             │
│ Last Sync: 5m ago           │
│ Nodes Synced: 5,678         │
│ Sync Status: ✓ Healthy     │
│                             │
│ [Trigger Sync] [Configure]  │
└─────────────────────────────┘
```

#### Quick Start Code

```python
from ragversion.integrations.llamaindex import LlamaIndexSync

# Initialize sync
sync = LlamaIndexSync(
    tracker=tracker,
    index=your_index
)

# Auto-sync on changes
tracker.on_change(sync.sync_on_change)
```

### Sync History

Table showing recent synchronization events:

| Integration | Type | Status | Items | Timestamp | Duration |
|------------|------|--------|-------|-----------|----------|
| LangChain | Auto | ✓ Success | 12 docs | 2m ago | 1.2s |
| LlamaIndex | Manual | ✓ Success | 45 nodes | 5m ago | 3.5s |
| LangChain | Auto | ❌ Failed | - | 10m ago | 0.5s |

**Columns:**
- **Integration** - Framework name with color badge
- **Type** - Auto (triggered) or Manual (user-initiated)
- **Status** - Success, Failed, or In Progress
- **Items Synced** - Document/node count
- **Timestamp** - When sync occurred
- **Duration** - How long it took

### Manual Sync Triggers

Click **Trigger Sync** to manually initiate synchronization:

1. Button press sends API request
2. Background task starts
3. Progress indicator appears
4. Completion notification shown
5. Sync history updates

## Real-Time Features

### WebSocket Connection

The dashboard maintains a persistent WebSocket connection at:
```
ws://localhost:6699/ws/changes
```

**Connection Status Indicator:**
- 🟢 Green dot - Connected
- 🔴 Red dot - Disconnected
- 🟡 Yellow dot - Reconnecting

**Auto-Reconnect:**
If connection drops, automatic reconnect attempts every 5 seconds.

### Live Activity Feed

Real-time notifications appear as changes occur:

```
┌────────────────────────────────────┐
│ 🟢 report.pdf                      │
│ Created · Version 1 · 2s ago       │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ 🔵 notes.md                        │
│ Modified · Version 3 · 10s ago     │
└────────────────────────────────────┘
```

Each notification shows:
- Change type icon and color
- File name
- Change description
- Version number
- Time elapsed

**Feed Controls:**
- Auto-scroll to latest
- Pause/resume updates
- Clear all notifications
- Filter by change type

## API Documentation

Navigate to **API Docs** (http://localhost:6699/api/docs) for interactive Swagger UI.

### Features

- **Interactive Testing** - Try API endpoints directly
- **Request/Response Examples** - See exact formats
- **Authentication** - Test with API keys
- **Schema Documentation** - All models documented

### Alternative: ReDoc

Visit **ReDoc** (http://localhost:6699/api/redoc) for a cleaner, read-only documentation format.

## Keyboard Shortcuts

### Global
- `Ctrl/Cmd + K` - Focus search
- `Escape` - Close modals
- `?` - Show keyboard shortcuts help

### Dashboard
- `R` - Refresh statistics
- `D` - Go to Documents
- `T` - Go to Track

### Documents List
- `↑ ↓` - Navigate rows
- `Enter` - Open selected document
- `/` - Focus search

### Document Details
- `V` - View current version
- `C` - Compare versions
- `←` - Back to list

## Mobile Support

The web UI is fully responsive and mobile-friendly:

### Tablet (768px+)
- 2-column stat grid
- Collapsible navigation
- Touch-friendly buttons
- Horizontal scroll tables

### Mobile (< 768px)
- 1-column layout
- Hamburger menu
- Swipe gestures
- Simplified charts

## Browser Compatibility

**Supported Browsers:**
- ✅ Chrome/Edge (latest 2 versions)
- ✅ Firefox (latest 2 versions)
- ✅ Safari (latest 2 versions)

**Required Features:**
- ES6+ JavaScript
- WebSocket support
- CSS Grid
- Fetch API

## Performance

### Optimization Tips

**Large Datasets (10,000+ documents):**
- Use search filters to narrow results
- Adjust pagination size
- Enable server-side pagination (future feature)

**Slow Charts:**
- Reduce time range in analytics
- Disable real-time updates if not needed
- Use Chrome DevTools for profiling

**Network:**
- All libraries loaded via CDN (cached after first load)
- Gzip compression enabled
- Minimal API calls with caching

### Metrics

**Typical Performance:**
- Dashboard load: < 500ms
- Search response: < 300ms
- Chart render: < 200ms
- WebSocket latency: < 100ms

## Troubleshooting

### Server Won't Start

**Error:** `Address already in use`

```bash
# Kill process on port 6699
lsof -ti:6699 | xargs kill -9

# Or use different port
python -m uvicorn ragversion.api.main:app --port 8080
```

**Error:** `Module 'fastapi' not found`

```bash
# Install API dependencies
pip install "ragversion[api]"
```

### Dashboard Shows No Data

**Issue:** Statistics cards show 0

**Solution:** Track some documents first:
1. Go to Track page
2. Enter a file or directory path
3. Click Track button
4. Return to Dashboard

### WebSocket Connection Failed

**Issue:** Red dot, no real-time updates

**Causes:**
- Firewall blocking WebSocket
- HTTPS/HTTP mismatch
- Server not running

**Solutions:**
```bash
# Check server is running
curl http://localhost:6699/api/health

# Check WebSocket in browser console
ws = new WebSocket('ws://localhost:6699/ws/changes')

# If using HTTPS, use WSS
wss://your-domain.com/ws/changes
```

### Charts Not Rendering

**Issue:** Blank chart areas

**Causes:**
- Chart.js not loaded
- No data to display
- Browser compatibility

**Solutions:**
1. Check browser console for errors
2. Verify Chart.js CDN loaded
3. Track documents to generate data
4. Try different browser

### Slow Performance

**Issue:** Pages load slowly

**Solutions:**
1. Check database size and optimize
2. Reduce pagination limit
3. Clear browser cache
4. Use production build (not dev mode)
5. Enable database indexes

## Production Deployment

### Security Checklist

- [ ] Enable API key authentication
- [ ] Configure CORS origins (not `*`)
- [ ] Use HTTPS with SSL certificates
- [ ] Add rate limiting
- [ ] Implement CSP headers
- [ ] Sanitize user inputs
- [ ] Enable audit logging

### Performance Checklist

- [ ] Use Gunicorn with Uvicorn workers
- [ ] Enable HTTP/2
- [ ] Add response caching
- [ ] Configure CDN for static assets
- [ ] Set up database connection pooling
- [ ] Enable gzip compression

### Monitoring Checklist

- [ ] Set up application logging
- [ ] Configure error tracking (Sentry)
- [ ] Add performance monitoring (Prometheus)
- [ ] Set up uptime monitoring
- [ ] Configure health check alerts

### Example Production Setup

```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn ragversion.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:6699 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:6699;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Advanced Features

### Custom Themes

The UI uses CSS variables - customize the theme by overriding:

```css
:root {
    --primary: #3b82f6;        /* Blue */
    --success: #10b981;        /* Green */
    --danger: #ef4444;         /* Red */
    --warning: #f59e0b;        /* Orange */
    --bg: #f8fafc;            /* Background */
    --surface: #ffffff;        /* Cards */
    --text: #1e293b;          /* Text */
    --text-muted: #64748b;    /* Muted text */
    --border: #e2e8f0;        /* Borders */
}
```

### API Integration

Use the REST API for programmatic access:

```javascript
// Fetch statistics
const stats = await fetch('http://localhost:6699/api/statistics/overall')
    .then(r => r.json());

// Track directory
const result = await fetch('http://localhost:6699/api/tracking/track-directory', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        directory_path: '/path/to/docs',
        patterns: ['*.pdf', '*.md'],
        recursive: true
    })
}).then(r => r.json());
```

### Webhooks (Coming Soon)

Configure webhooks to receive notifications:

```json
{
    "url": "https://your-app.com/webhook",
    "events": ["document.created", "document.modified"],
    "secret": "your-secret-key"
}
```

## Next Steps

- [:octicons-arrow-right-24: API Reference](../API_GUIDE.md)
- [:octicons-arrow-right-24: CLI Guide](cli.md)
- [:octicons-arrow-right-24: Integration Guides](../integrations/langchain.md)
- [:octicons-arrow-right-24: Troubleshooting](../TROUBLESHOOTING.md)

---

**Built with:** FastAPI, HTMX, Alpine.js, Chart.js, Tailwind CSS

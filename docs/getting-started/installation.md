# Installation

## Prerequisites

- Python 3.9 or higher
- Supabase account (free tier works fine)
- Basic understanding of async/await in Python

## Installation Options

### Basic Installation

Install the core package:

```bash
pip install ragversion
```

This includes:
- Core tracking functionality
- Supabase storage backend
- Basic file type support

### With Document Parsers

Install with support for various document formats:

```bash
pip install "ragversion[parsers]"
```

Adds support for:
- PDF files (pypdf)
- DOCX files (python-docx)
- PPTX files (python-pptx)
- Excel files (openpyxl)
- Enhanced Markdown parsing

### With LangChain Integration

Install with LangChain compatibility:

```bash
pip install "ragversion[langchain]"
```

Includes:
- LangChain compatibility helpers
- Document loader integration
- Vector store sync utilities

### With LlamaIndex Integration

Install with LlamaIndex compatibility:

```bash
pip install "ragversion[llamaindex]"
```

Includes:
- LlamaIndex compatibility helpers
- Node parser integration
- Index sync utilities

### Complete Installation (Recommended)

Install everything including development tools:

```bash
pip install "ragversion[all]"
```

Includes:
- All parsers
- All integrations
- Development tools (pytest, black, ruff, mypy)

## Verify Installation

Check that RAGVersion is installed correctly:

```bash
ragversion --version
```

You should see:
```
ragversion, version 0.1.0
```

## Supabase Setup

RAGVersion uses Supabase (PostgreSQL) as its primary storage backend.

### Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a free account
3. Create a new project
4. Note your project URL and service key

### Step 2: Initialize RAGVersion

Initialize RAGVersion in your project:

```bash
ragversion init
```

This creates a `ragversion.yaml` configuration file.

### Step 3: Configure Credentials

Edit `ragversion.yaml` with your Supabase credentials:

```yaml
storage:
  backend: supabase
  supabase:
    url: https://your-project.supabase.co
    key: your-service-key
```

Or use environment variables:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

### Step 4: Run Database Migration

Get the migration SQL:

```bash
ragversion migrate
```

Copy the SQL output and run it in your Supabase SQL Editor:
1. Go to SQL Editor in Supabase dashboard
2. Paste the migration SQL
3. Run the query

### Step 5: Verify Setup

Check that everything is configured correctly:

```bash
ragversion health
```

You should see:
```
✓ Storage backend is healthy
```

## Environment Variables

For production deployments, use environment variables instead of YAML:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

Add to your `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

## Docker Installation

If you're using Docker, add RAGVersion to your `requirements.txt`:

```text
ragversion[all]>=0.1.0
```

And set environment variables in your `docker-compose.yml`:

```yaml
environment:
  SUPABASE_URL: https://your-project.supabase.co
  SUPABASE_SERVICE_KEY: your-service-key
```

## Troubleshooting

### "No module named 'ragversion'"

Make sure you've installed the package:

```bash
pip install ragversion
```

### "Supabase connection failed"

Check your credentials:

```bash
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY
```

Verify your Supabase project is active and the credentials are correct.

### "Table 'documents' does not exist"

You need to run the database migration. See Step 4 above.

## Next Steps

- [Quick Start Guide](quickstart.md) - Track your first document
- [Configuration](configuration.md) - Learn about configuration options
- [Core Concepts](../guide/core-concepts.md) - Understand how RAGVersion works

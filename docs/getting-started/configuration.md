# Configuration

RAGVersion can be configured using YAML files or environment variables.

## Configuration File

Create a `ragversion.yaml` file in your project root:

```yaml
storage:
  backend: supabase
  supabase:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_SERVICE_KEY}

tracking:
  store_content: true
  max_file_size_mb: 50
  batch:
    max_workers: 4
    on_error: continue

content:
  compression: gzip
  ttl_days: 365
```

## Configuration Options

### Storage Configuration

#### `storage.backend`

Storage backend to use.

- **Type**: `string`
- **Default**: `supabase`
- **Options**: `supabase`

#### `storage.supabase.url`

Supabase project URL.

- **Type**: `string`
- **Required**: Yes
- **Example**: `https://your-project.supabase.co`

#### `storage.supabase.key`

Supabase service key.

- **Type**: `string`
- **Required**: Yes
- **Example**: `your-service-key`

### Tracking Configuration

#### `tracking.store_content`

Whether to store document content in the database.

- **Type**: `boolean`
- **Default**: `true`
- **Description**: When `true`, document content is stored (compressed). When `false`, only metadata is tracked.

#### `tracking.max_file_size_mb`

Maximum file size to process (in MB).

- **Type**: `integer`
- **Default**: `100`
- **Description**: Files larger than this will be skipped.

#### `tracking.batch.max_workers`

Number of parallel workers for batch processing.

- **Type**: `integer`
- **Default**: `4`
- **Description**: Higher values = faster processing but more resource usage.

#### `tracking.batch.on_error`

Behavior when a file fails to process.

- **Type**: `string`
- **Default**: `continue`
- **Options**: `continue`, `stop`
- **Description**: `continue` = keep processing other files. `stop` = abort batch on first error.

### Content Configuration

#### `content.compression`

Compression algorithm for stored content.

- **Type**: `string`
- **Default**: `gzip`
- **Options**: `gzip`, `none`
- **Description**: `gzip` compresses content before storage. `none` stores raw content.

#### `content.ttl_days`

Time-to-live for old versions (in days).

- **Type**: `integer`
- **Default**: `365`
- **Description**: Versions older than this may be archived or deleted (future feature).

## Environment Variables

You can use environment variables instead of or in addition to YAML configuration:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

### Variable Substitution

Use `${VAR_NAME}` in YAML to reference environment variables:

```yaml
storage:
  supabase:
    url: ${SUPABASE_URL}
    key: ${SUPABASE_SERVICE_KEY}
```

## Python Configuration

You can also configure RAGVersion programmatically:

```python
from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage

# Using environment variables
storage = SupabaseStorage.from_env()

# Or explicit configuration
storage = SupabaseStorage(
    url="https://your-project.supabase.co",
    key="your-service-key"
)

# Create tracker with options
tracker = AsyncVersionTracker(
    storage=storage,
    store_content=True,
    max_file_size_mb=50,
    compression="gzip"
)
```

## Configuration Loading

RAGVersion loads configuration in this order (later overrides earlier):

1. Default values
2. `ragversion.yaml` in current directory
3. Custom config file (if specified)
4. Environment variables

### Loading Custom Config

```python
from ragversion.config import RAGVersionConfig

# Load specific config file
config = RAGVersionConfig.load("path/to/config.yaml")

# Access settings
print(config.supabase.url)
print(config.tracking.max_file_size_mb)
```

### CLI with Custom Config

```bash
ragversion track ./docs --config my-config.yaml
```

## Example Configurations

### Development

```yaml
storage:
  backend: supabase
  supabase:
    url: ${DEV_SUPABASE_URL}
    key: ${DEV_SUPABASE_KEY}

tracking:
  store_content: true
  max_file_size_mb: 10  # Smaller limit for dev
  batch:
    max_workers: 2       # Fewer workers for dev

content:
  compression: none      # No compression for easier debugging
```

### Production

```yaml
storage:
  backend: supabase
  supabase:
    url: ${PROD_SUPABASE_URL}
    key: ${PROD_SUPABASE_KEY}

tracking:
  store_content: true
  max_file_size_mb: 100
  batch:
    max_workers: 8       # More workers for production

content:
  compression: gzip      # Enable compression for production
  ttl_days: 365
```

### Testing

```python
from ragversion.testing import MockStorage

# Use mock storage for testing
tracker = AsyncVersionTracker(
    storage=MockStorage(),
    store_content=False  # Don't store content in tests
)
```

## Security Best Practices

### 1. Use Environment Variables

Never commit secrets to version control:

```yaml
# ❌ BAD - secrets in YAML
storage:
  supabase:
    key: "actual-secret-key"

# ✅ GOOD - use environment variables
storage:
  supabase:
    key: ${SUPABASE_SERVICE_KEY}
```

### 2. Use .env Files

Add `.env` to `.gitignore`:

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-secret-key
```

```gitignore
# .gitignore
.env
ragversion.yaml
```

### 3. Use Secrets Managers

For production, use a secrets manager:

- AWS Secrets Manager
- Google Cloud Secret Manager
- HashiCorp Vault
- Azure Key Vault

## Next Steps

- [Core Concepts](../guide/core-concepts.md) - Understand how RAGVersion works
- [Tracking Documents](../guide/tracking.md) - Learn about tracking options
- [Best Practices](../advanced/best-practices.md) - Follow best practices

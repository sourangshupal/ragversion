# GitHub Actions Integration

Automatically track documentation changes in your CI/CD pipeline with RAGVersion's GitHub Actions integration.

## Overview

RAGVersion provides a reusable GitHub Action that makes it easy to:
- ✅ Track documentation changes on every commit
- ✅ Validate documentation in pull requests
- ✅ Run scheduled tracking jobs
- ✅ Monitor documentation history over time
- ✅ Support both SQLite and Supabase backends
- ✅ Upload tracking artifacts for later analysis

---

## Quick Start

### 1. Basic Setup

Add this workflow to `.github/workflows/ragversion.yml`:

```yaml
name: Track Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - '*.md'

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Track docs with RAGVersion
        uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/ README.md'
```

That's it! RAGVersion will now track your documentation on every push.

---

## Action Inputs

### Required Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `paths` | Paths to track (space-separated) | `docs/` |

### Optional Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `storage-backend` | Storage backend: `sqlite` or `supabase` | `sqlite` |
| `sqlite-db-path` | SQLite database path | `ragversion.db` |
| `supabase-url` | Supabase URL (required for supabase backend) | `""` |
| `supabase-key` | Supabase service key (required for supabase backend) | `""` |
| `file-patterns` | File patterns to track (e.g., `*.md *.txt`) | `""` (all files) |
| `max-workers` | Maximum concurrent workers | `4` |
| `python-version` | Python version to use | `3.11` |
| `ragversion-version` | RAGVersion version to install | `latest` |
| `fail-on-error` | Fail workflow if tracking fails | `false` |
| `install-parsers` | Install optional parser dependencies | `true` |

### Action Outputs

| Output | Description |
|--------|-------------|
| `tracked-files` | Number of files tracked |
| `changes-detected` | Number of changes detected |
| `success` | Whether tracking succeeded (true/false) |

---

## Common Use Cases

### 1. Track Docs on Push

Track documentation changes on every push to main:

```yaml
name: Track Documentation

on:
  push:
    branches: [main, master]
    paths:
      - 'docs/**'
      - '*.md'

jobs:
  track-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history

      - name: Track documentation
        uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/ README.md CHANGELOG.md'
          storage-backend: 'sqlite'
          file-patterns: '*.md *.txt'

      - name: Upload database
        uses: actions/upload-artifact@v4
        with:
          name: ragversion-db-${{ github.sha }}
          path: ragversion.db
```

### 2. PR Documentation Check

Validate documentation changes in pull requests:

```yaml
name: PR Documentation Check

on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'docs/**'

jobs:
  check-docs:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha }}

      - name: Track documentation
        id: track
        uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/'
          fail-on-error: true  # Fail PR if tracking fails

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const tracked = '${{ steps.track.outputs.tracked-files }}';
            const changes = '${{ steps.track.outputs.changes-detected }}';

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `## 📝 Documentation Tracking Results

              - **Files Tracked:** ${tracked}
              - **Changes Detected:** ${changes}

              All documentation changes have been tracked successfully!`
            });
```

### 3. Scheduled Tracking

Run periodic tracking jobs (e.g., daily):

```yaml
name: Scheduled Documentation Tracking

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  workflow_dispatch:

jobs:
  scheduled-track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Track all documents
        uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/ examples/'
          max-workers: 8
          sqlite-db-path: 'ragversion-scheduled.db'

      - name: Upload tracking history
        uses: actions/upload-artifact@v4
        with:
          name: ragversion-daily-${{ github.run_number }}
          path: ragversion-scheduled.db
          retention-days: 90
```

### 4. Multi-Path Tracking

Track multiple directories with different patterns:

```yaml
name: Track Multiple Directories

on:
  push:
    branches: [main]

jobs:
  track-all:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Track documentation
        uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/ api/ guides/ README.md'
          file-patterns: '*.md *.txt *.pdf'
          max-workers: 8
```

### 5. Supabase Backend

Use Supabase for cloud storage and team collaboration:

```yaml
name: Track with Supabase

on:
  push:
    branches: [main]

jobs:
  track-supabase:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Track with Supabase
        uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/'
          storage-backend: 'supabase'
          supabase-url: ${{ secrets.SUPABASE_URL }}
          supabase-key: ${{ secrets.SUPABASE_SERVICE_KEY }}
          fail-on-error: true
```

**Setup:**
1. Create Supabase project at https://supabase.com
2. Run migrations (see [docs/SQLITE_BACKEND.md](SQLITE_BACKEND.md))
3. Add secrets to repository:
   - `SUPABASE_URL`: Your project URL
   - `SUPABASE_SERVICE_KEY`: Service role key (Settings → API)

---

## Configuration

### SQLite Backend (Default)

**Advantages:**
- ✅ Zero-configuration setup
- ✅ No external dependencies
- ✅ Perfect for single-repository tracking
- ✅ Fast for small to medium datasets
- ✅ Easy to archive as artifacts

**Configuration:**

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    storage-backend: 'sqlite'
    sqlite-db-path: '.ragversion/ragversion.db'
```

### Supabase Backend

**Advantages:**
- ✅ Cloud storage (no artifacts needed)
- ✅ Multi-repository tracking
- ✅ Team collaboration
- ✅ Real-time queries
- ✅ Scalable for large datasets

**Configuration:**

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    storage-backend: 'supabase'
    supabase-url: ${{ secrets.SUPABASE_URL }}
    supabase-key: ${{ secrets.SUPABASE_SERVICE_KEY }}
```

**Required Secrets:**
- `SUPABASE_URL`: `https://your-project.supabase.co`
- `SUPABASE_SERVICE_KEY`: Service role key from Supabase dashboard

---

## File Patterns

Control which files are tracked using glob patterns:

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    paths: 'docs/'
    file-patterns: '*.md *.txt *.pdf *.docx'
```

**Common Patterns:**

| Pattern | Matches |
|---------|---------|
| `*.md` | All Markdown files |
| `*.txt` | All text files |
| `*.pdf` | All PDF files |
| `*.md *.txt` | Markdown and text files |
| `README.* CHANGELOG.*` | README and CHANGELOG in any format |

**Parsers Required:**

| File Type | Pattern | Parsers Needed |
|-----------|---------|----------------|
| Markdown | `*.md` | No (built-in) |
| Text | `*.txt` | No (built-in) |
| PDF | `*.pdf` | Yes (`install-parsers: true`) |
| DOCX | `*.docx` | Yes (`install-parsers: true`) |
| PPTX | `*.pptx` | Yes (`install-parsers: true`) |
| XLSX | `*.xlsx` | Yes (`install-parsers: true`) |

---

## Performance Tuning

### Max Workers

Control concurrent file processing:

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    max-workers: 8  # Default: 4
```

**Guidelines:**
- **Small repos (<100 files):** 2-4 workers
- **Medium repos (100-1000 files):** 4-8 workers
- **Large repos (>1000 files):** 8-16 workers

### Optimize Checkout

For faster tracking, only fetch necessary history:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 1  # Shallow clone (faster)
```

**Trade-offs:**
- `fetch-depth: 1` - Fastest, but only tracks current state
- `fetch-depth: 0` - Full history, better for change detection

---

## Artifacts

### Upload Database

Archive SQLite database for later analysis:

```yaml
- name: Upload RAGVersion database
  uses: actions/upload-artifact@v4
  with:
    name: ragversion-db-${{ github.sha }}
    path: ragversion.db
    retention-days: 30
```

### Download and Query

Download archived databases:

```bash
# Download artifact via GitHub CLI
gh run download <run-id> -n ragversion-db-<sha>

# Query locally
ragversion list --limit 100
ragversion stats
```

---

## Error Handling

### Fail on Error

Fail the workflow if tracking fails:

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    fail-on-error: true
```

**Use Cases:**
- ✅ PR checks (ensure all docs are trackable)
- ✅ Critical documentation tracking
- ❌ Optional tracking (don't block deployments)

### Continue on Error

Continue even if some files fail:

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    fail-on-error: false  # Default
```

### Check Outputs

Use action outputs to handle errors:

```yaml
- name: Track docs
  id: track
  uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0

- name: Handle failure
  if: steps.track.outputs.success != 'true'
  run: |
    echo "Tracking failed!"
    echo "Files tracked: ${{ steps.track.outputs.tracked-files }}"
    exit 1
```

---

## Notifications

### Slack Notifications

Send Slack notifications on tracking completion:

```yaml
- name: Track docs
  id: track
  uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0

- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "📝 Documentation tracked",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*RAGVersion Tracking Complete*\n• Files: ${{ steps.track.outputs.tracked-files }}\n• Changes: ${{ steps.track.outputs.changes-detected }}"
            }
          }
        ]
      }
```

### Email Notifications

Send email on failures:

```yaml
- name: Send failure notification
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: 'RAGVersion tracking failed'
    to: team@example.com
    from: noreply@example.com
    body: |
      RAGVersion tracking failed in ${{ github.repository }}

      Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

---

## Versioning

### Pin to Specific Version

Recommended for production:

```yaml
uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
```

### Use Latest

Always use latest features (may break):

```yaml
uses: sourangshupal/ragversion/.github/actions/ragversion-track@main
```

### Install Specific RAGVersion Version

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    ragversion-version: '0.3.0'  # Specific version
```

---

## Troubleshooting

### Action Not Found

**Error:** `Unable to resolve action sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0`

**Solutions:**
1. Check version tag exists: `v0.4.0`, `v0.3.0`, etc.
2. Use `@main` for latest code
3. For local testing, use relative path: `./.github/actions/ragversion-track`

### Parser Errors

**Error:** `Failed to parse PDF file`

**Solution:** Ensure parsers are installed:

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    install-parsers: true  # Install PDF, DOCX, etc. parsers
```

### Database Lock Errors (SQLite)

**Error:** `database is locked`

**Solutions:**
1. Reduce max workers: `max-workers: 2`
2. Use separate database files for concurrent jobs
3. Consider using Supabase for multi-job workflows

### Out of Memory

**Error:** OOM when tracking large directories

**Solutions:**
1. Reduce max workers: `max-workers: 2`
2. Track directories separately:
   ```yaml
   - uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
     with:
       paths: 'docs/section1/'

   - uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
     with:
       paths: 'docs/section2/'
   ```
3. Exclude large files with patterns

### Supabase Connection Errors

**Error:** `Failed to connect to Supabase`

**Solutions:**
1. Verify secrets are set correctly:
   - `SUPABASE_URL` should start with `https://`
   - `SUPABASE_SERVICE_KEY` should be service role key (not anon key)
2. Check Supabase project is running
3. Verify migrations have been run
4. Test connection locally first

---

## Best Practices

### ✅ DO

1. **Pin action versions** in production workflows
2. **Upload artifacts** for SQLite databases
3. **Use specific file patterns** to avoid unnecessary tracking
4. **Set retention policies** for artifacts (30-90 days)
5. **Test locally first** before deploying workflows
6. **Use Supabase for team collaboration**
7. **Add PR comments** to show tracking results
8. **Monitor workflow run times** and optimize

### ❌ DON'T

1. **Don't commit sensitive data** to workflow files
2. **Don't track binary files** unnecessarily (images, videos)
3. **Don't use anon keys** for Supabase (use service key)
4. **Don't set workers >16** (diminishing returns)
5. **Don't track .git directory** or node_modules
6. **Don't use shallow clones** if you need full history
7. **Don't forget to set fail-on-error** for PR checks

---

## Examples Repository

See full working examples in:
- [`.github/workflows/ragversion-example-basic.yml`](../.github/workflows/ragversion-example-basic.yml)
- [`.github/workflows/ragversion-example-pr.yml`](../.github/workflows/ragversion-example-pr.yml)
- [`.github/workflows/ragversion-example-scheduled.yml`](../.github/workflows/ragversion-example-scheduled.yml)
- [`.github/workflows/ragversion-example-supabase.yml`](../.github/workflows/ragversion-example-supabase.yml)

---

## Further Reading

- [RAGVersion Documentation](../DOCUMENTATION.md) - Full API reference
- [CLI Guide](guide/cli.md) - Command-line usage
- [SQLite Backend](SQLITE_BACKEND.md) - SQLite configuration
- [Performance Guide](PERFORMANCE.md) - Optimization tips

---

## Support

- **Issues:** https://github.com/sourangshupal/ragversion/issues
- **Discussions:** https://github.com/sourangshupal/ragversion/discussions
- **Documentation:** https://github.com/sourangshupal/ragversion

---

**Last Updated:** January 20, 2026 (v0.4.0)

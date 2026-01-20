# RAGVersion Track Action

Automatically track documentation changes in your CI/CD pipeline with RAGVersion.

## Quick Start

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    paths: 'docs/ README.md'
```

## Inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `paths` | Paths to track (space-separated) | `docs/` | Yes |
| `storage-backend` | Storage backend: sqlite or supabase | `sqlite` | No |
| `sqlite-db-path` | SQLite database path | `ragversion.db` | No |
| `supabase-url` | Supabase URL | `""` | No |
| `supabase-key` | Supabase service key | `""` | No |
| `file-patterns` | File patterns to track | `""` | No |
| `max-workers` | Maximum concurrent workers | `4` | No |
| `python-version` | Python version to use | `3.11` | No |
| `ragversion-version` | RAGVersion version to install | `latest` | No |
| `fail-on-error` | Fail workflow if tracking fails | `false` | No |
| `install-parsers` | Install optional parser dependencies | `true` | No |

## Outputs

| Output | Description |
|--------|-------------|
| `tracked-files` | Number of files tracked |
| `changes-detected` | Number of changes detected |
| `success` | Whether tracking succeeded (true/false) |

## Examples

### Basic Usage

Track documentation on every push:

```yaml
name: Track Documentation

on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/'
```

### PR Check

Validate documentation in pull requests:

```yaml
name: PR Documentation Check

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - id: track
        uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
        with:
          paths: 'docs/'
          fail-on-error: true

      - name: Comment results
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `✅ Tracked ${{ steps.track.outputs.tracked-files }} files, detected ${{ steps.track.outputs.changes-detected }} changes`
            })
```

### Supabase Backend

Use Supabase for cloud storage:

```yaml
- uses: sourangshupal/ragversion/.github/actions/ragversion-track@v0.4.0
  with:
    paths: 'docs/'
    storage-backend: 'supabase'
    supabase-url: ${{ secrets.SUPABASE_URL }}
    supabase-key: ${{ secrets.SUPABASE_SERVICE_KEY }}
```

## Documentation

Full documentation: [docs/GITHUB_ACTIONS.md](../../../docs/GITHUB_ACTIONS.md)

## Support

- Issues: https://github.com/sourangshupal/ragversion/issues
- Docs: https://github.com/sourangshupal/ragversion

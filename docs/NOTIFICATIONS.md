# Notifications System

RAGVersion includes a flexible notification system that can alert you when documents change. Get real-time notifications via Slack, Discord, Email, or custom webhooks.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Notification Providers](#notification-providers)
  - [Slack](#slack)
  - [Discord](#discord)
  - [Email](#email)
  - [Webhook](#webhook)
- [Programmatic Usage](#programmatic-usage)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The notification system sends alerts when documents are created, modified, deleted, or restored. Each notification includes:

- Change type (created, modified, deleted, restored)
- Document information (name, path, size, hash)
- Version information (number, timestamp)
- Optional custom metadata

Notifications can be sent to multiple providers simultaneously, with support for parallel or sequential delivery.

## Quick Start

1. **Create a configuration file** (`ragversion.yaml`):

```yaml
notifications:
  enabled: true
  notifiers:
    - type: slack
      name: team-slack
      enabled: true
      webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

2. **Use with CLI** (file watching):

```bash
ragversion watch ./documents --patterns "*.pdf" "*.docx"
```

3. **Use programmatically**:

```python
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.config import RAGVersionConfig
from ragversion.notifications import create_notification_manager

# Load config
config = RAGVersionConfig.load("ragversion.yaml")

# Create notification manager
notification_manager = None
if config.notifications.enabled:
    notification_manager = create_notification_manager(
        config.notifications.notifiers
    )

# Create tracker with notifications
storage = SQLiteStorage("ragversion.db")
tracker = AsyncVersionTracker(
    storage=storage,
    notification_manager=notification_manager
)

async with tracker:
    await tracker.track("./documents/report.pdf")
```

## Configuration

### YAML Configuration

```yaml
notifications:
  enabled: true  # Enable/disable all notifications
  notifiers:
    - type: slack
      name: team-alerts
      enabled: true
      webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      channel: "#documents"
      username: RAGVersion
      mention_users: ["U123456"]
      mention_on_types: ["deleted"]

    - type: discord
      name: dev-discord
      enabled: true
      webhook_url: https://discord.com/api/webhooks/YOUR/WEBHOOK
      username: RAGVersion
      mention_users: ["123456789"]
      mention_on_types: ["deleted"]

    - type: email
      name: admin-email
      enabled: true
      smtp_host: smtp.gmail.com
      smtp_port: 587
      smtp_username: your-email@gmail.com
      smtp_password: your-app-password
      use_tls: true
      from_address: ragversion@yourcompany.com
      to_addresses:
        - admin@yourcompany.com
        - team@yourcompany.com
      subject_prefix: "[RAGVersion]"

    - type: webhook
      name: custom-webhook
      enabled: true
      url: https://your-api.com/webhooks/documents
      method: POST
      headers:
        Authorization: Bearer YOUR_TOKEN
```

### Environment Variables

You can also configure notifications via environment variables:

```bash
# Enable notifications
export RAGVERSION_NOTIFICATIONS_ENABLED=true

# Configure individual notifiers in YAML or programmatically
```

## Notification Providers

### Slack

Send notifications to Slack channels via incoming webhooks.

**Configuration:**

```yaml
- type: slack
  name: team-slack
  enabled: true
  webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
  channel: "#documents"  # Optional: override default channel
  username: RAGVersion  # Optional: bot display name
  icon_emoji: ":file_folder:"  # Optional: bot icon
  mention_users: ["U123456"]  # Optional: user IDs to mention
  mention_on_types: ["deleted"]  # Optional: when to mention
  timeout_seconds: 30  # Optional: request timeout
```

**Setup:**

1. Go to https://api.slack.com/apps
2. Create a new app or use existing
3. Enable "Incoming Webhooks"
4. Create a webhook for your desired channel
5. Copy the webhook URL to your config

**Features:**

- Rich message formatting with colors
- User mentions for important changes
- File metadata in structured fields
- Clickable links (if you provide URLs in metadata)

### Discord

Send notifications to Discord channels via webhooks.

**Configuration:**

```yaml
- type: discord
  name: dev-discord
  enabled: true
  webhook_url: https://discord.com/api/webhooks/YOUR/WEBHOOK
  username: RAGVersion  # Optional: bot display name
  avatar_url: https://example.com/avatar.png  # Optional: bot avatar
  mention_users: ["123456789"]  # Optional: user IDs to mention
  mention_roles: ["987654321"]  # Optional: role IDs to mention
  mention_on_types: ["deleted"]  # Optional: when to mention
  timeout_seconds: 30  # Optional: request timeout
```

**Setup:**

1. Go to Discord channel settings
2. Navigate to "Integrations" → "Webhooks"
3. Click "New Webhook"
4. Copy the webhook URL to your config

**Features:**

- Embed-based messages with color coding
- User and role mentions
- Timestamp display
- File metadata in embed fields

### Email

Send notifications via SMTP email.

**Configuration:**

```yaml
- type: email
  name: admin-email
  enabled: true
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_username: your-email@gmail.com
  smtp_password: your-app-password
  use_tls: true
  from_address: ragversion@yourcompany.com
  to_addresses:
    - admin@yourcompany.com
    - team@yourcompany.com
  cc_addresses: []  # Optional: CC addresses
  subject_prefix: "[RAGVersion]"  # Optional: email subject prefix
  timeout_seconds: 30  # Optional: SMTP timeout
```

**Setup (Gmail example):**

1. Enable 2-factor authentication on your Google account
2. Generate an app password: https://myaccount.google.com/apppasswords
3. Use the app password in `smtp_password`

**Setup (Generic SMTP):**

1. Get SMTP credentials from your email provider
2. Configure `smtp_host`, `smtp_port`, and credentials
3. For TLS: use port 587 with `use_tls: true`
4. For SSL: use port 465 with `use_tls: false`

**Features:**

- HTML and plain text multipart messages
- CC support
- Customizable subject prefix
- Professional formatting with colors

### Webhook

Send notifications to custom HTTP endpoints.

**Configuration:**

```yaml
- type: webhook
  name: custom-api
  enabled: true
  url: https://your-api.com/webhooks/documents
  method: POST  # Optional: POST, PUT, PATCH
  headers:  # Optional: custom headers
    Authorization: Bearer YOUR_TOKEN
    Content-Type: application/json
  include_metadata: true  # Optional: include metadata in payload
  timeout_seconds: 30  # Optional: request timeout
```

**Payload Format:**

```json
{
  "event": "document_change",
  "change_type": "modified",
  "document": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "report.pdf",
    "file_path": "/path/to/report.pdf",
    "file_size": 102400,
    "content_hash": "sha256:abc123..."
  },
  "version": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "number": 3,
    "previous_hash": "sha256:def456..."
  },
  "timestamp": "2025-01-20T10:30:00Z",
  "metadata": {
    "custom_field": "custom_value"
  }
}
```

**Use Cases:**

- Integration with custom APIs
- Triggering automation workflows
- Logging to external systems
- Custom notification logic

## Programmatic Usage

### Basic Setup

```python
from ragversion import AsyncVersionTracker
from ragversion.storage.sqlite import SQLiteStorage
from ragversion.notifications import (
    NotificationManager,
    SlackNotifier,
    SlackConfig,
)

# Create notifier
slack_config = SlackConfig(
    name="team-slack",
    enabled=True,
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
)
slack_notifier = SlackNotifier(slack_config)

# Create manager
notification_manager = NotificationManager([slack_notifier])

# Create tracker with notifications
storage = SQLiteStorage("ragversion.db")
tracker = AsyncVersionTracker(
    storage=storage,
    notification_manager=notification_manager
)

async with tracker:
    result = await tracker.track("./documents/report.pdf")
    # Notification sent automatically
```

### Multiple Notifiers

```python
from ragversion.notifications import (
    NotificationManager,
    SlackNotifier,
    SlackConfig,
    DiscordNotifier,
    DiscordConfig,
    EmailNotifier,
    EmailConfig,
)

# Create multiple notifiers
slack = SlackNotifier(SlackConfig(...))
discord = DiscordNotifier(DiscordConfig(...))
email = EmailNotifier(EmailConfig(...))

# Add to manager
manager = NotificationManager([slack, discord, email])

# Send in parallel (default)
results = await manager.notify(change_event)

# Send sequentially
results = await manager.notify(change_event, parallel=False)
```

### Dynamic Control

```python
# Disable specific notifier
manager.disable_notifier("team-slack")

# Enable specific notifier
manager.enable_notifier("team-slack")

# List all notifiers
notifiers = manager.list_notifiers()
for notifier in notifiers:
    print(f"{notifier['name']}: {notifier['enabled']}")

# Get specific notifier
notifier = manager.get_notifier("team-slack")
if notifier:
    notifier.enabled = False
```

### Custom Metadata

```python
# Track with custom metadata
metadata = {
    "environment": "production",
    "triggered_by": "automated_sync",
    "project": "customer-docs",
}

result = await tracker.track(
    "./documents/report.pdf",
    metadata=metadata
)
```

## Examples

### Example 1: Slack Notifications for Document Deletions

Only notify Slack when documents are deleted, with user mentions:

```yaml
notifications:
  enabled: true
  notifiers:
    - type: slack
      name: critical-alerts
      enabled: true
      webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      mention_users: ["U123456", "U789012"]
      mention_on_types: ["deleted"]  # Only mention for deletions
```

### Example 2: Email Alerts for Production Changes

Send email alerts with production environment metadata:

```python
from ragversion.notifications import EmailNotifier, EmailConfig

email_config = EmailConfig(
    name="production-alerts",
    enabled=True,
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="alerts@company.com",
    smtp_password="app-password",
    use_tls=True,
    from_address="ragversion@company.com",
    to_addresses=["team@company.com"],
    subject_prefix="[PRODUCTION]",
)

notifier = EmailNotifier(email_config)
manager = NotificationManager([notifier])

# Track with environment metadata
metadata = {"environment": "production"}
await tracker.track("./docs/critical.pdf", metadata=metadata)
```

### Example 3: Custom Webhook Integration

Integrate with a custom automation system:

```yaml
notifications:
  enabled: true
  notifiers:
    - type: webhook
      name: automation-trigger
      enabled: true
      url: https://automation.company.com/api/document-changed
      method: POST
      headers:
        Authorization: Bearer YOUR_API_TOKEN
        X-Environment: production
```

### Example 4: Multi-Provider Notifications

Send critical changes to multiple channels:

```yaml
notifications:
  enabled: true
  notifiers:
    # Slack for immediate alerts
    - type: slack
      name: dev-team
      enabled: true
      webhook_url: ${SLACK_WEBHOOK_URL}
      channel: "#documents"

    # Email for compliance team
    - type: email
      name: compliance
      enabled: true
      smtp_host: smtp.gmail.com
      smtp_port: 587
      smtp_username: ${EMAIL_USERNAME}
      smtp_password: ${EMAIL_PASSWORD}
      use_tls: true
      from_address: ragversion@company.com
      to_addresses:
        - compliance@company.com

    # Webhook for automation
    - type: webhook
      name: automation
      enabled: true
      url: ${WEBHOOK_URL}
      headers:
        Authorization: Bearer ${API_TOKEN}
```

### Example 5: Real-time File Watching with Notifications

Monitor a directory and get instant notifications:

```bash
# Start file watcher with notifications
ragversion watch ./documents \
  --patterns "*.pdf" "*.docx" \
  --recursive \
  --verbose
```

With configuration in `ragversion.yaml`:

```yaml
notifications:
  enabled: true
  notifiers:
    - type: discord
      name: dev-discord
      enabled: true
      webhook_url: ${DISCORD_WEBHOOK_URL}
```

## Troubleshooting

### Notifications Not Sending

1. **Check configuration:**
   ```python
   config = RAGVersionConfig.load()
   print(config.notifications.enabled)
   print(config.notifications.notifiers)
   ```

2. **Verify notifier is enabled:**
   ```python
   manager.list_notifiers()
   ```

3. **Check logs:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Slack Webhook Errors

- **"invalid_payload"**: Check webhook URL and message format
- **"channel_not_found"**: Ensure channel override is valid
- **Timeout errors**: Increase `timeout_seconds`

### Discord Webhook Errors

- **"Unknown Webhook"**: Verify webhook URL is correct
- **"Invalid Form Body"**: Check embed format and field limits
- **Rate limiting**: Discord limits to 30 requests per minute

### Email Errors

- **Authentication failed**:
  - Gmail: Use app password, not account password
  - Enable "Less secure app access" or use OAuth
- **Connection timeout**: Check SMTP host/port and firewall
- **TLS errors**: Try `use_tls: false` for SSL ports

### Webhook Errors

- **Connection refused**: Verify URL and network connectivity
- **401 Unauthorized**: Check Authorization header
- **Timeout**: Increase `timeout_seconds` or check endpoint

### Performance Considerations

- **Parallel vs Sequential**: Use `parallel=True` for faster delivery
- **Timeouts**: Set appropriate `timeout_seconds` for each notifier
- **Failed notifications**: Don't block tracking, logged as errors
- **Rate limits**: Be aware of provider limits (Discord, Slack)

## Advanced Topics

### Custom Notifier Implementation

Create your own notification provider:

```python
from ragversion.notifications.base import BaseNotifier, NotificationConfig
from pydantic import Field

class CustomConfig(NotificationConfig):
    api_key: str = Field(..., description="API key")
    endpoint: str = Field(..., description="API endpoint")

class CustomNotifier(BaseNotifier):
    def __init__(self, config: CustomConfig):
        super().__init__(config)
        self.config = config

    async def send(self, change: ChangeEvent, metadata=None) -> bool:
        # Implement your notification logic
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.endpoint,
                headers={"X-API-Key": self.config.api_key},
                json=self._build_payload(change, metadata)
            )
            return response.is_success

    def _build_payload(self, change, metadata):
        return {
            "event": "change",
            "file": change.file_name,
            # ... custom format
        }
```

### Error Handling

Notifications use fire-and-forget error handling:

- Failed notifications are logged but don't stop tracking
- Each notifier is independent (one failure doesn't affect others)
- Use logging to debug notification issues
- Monitor notification success via `NotificationManager.notify()` return value

### Security Best Practices

1. **Store credentials securely:**
   ```yaml
   # Use environment variables
   smtp_password: ${EMAIL_PASSWORD}
   webhook_url: ${SLACK_WEBHOOK_URL}
   ```

2. **Use HTTPS/TLS:**
   - Always use HTTPS for webhooks
   - Enable TLS for email (port 587)

3. **Limit exposed information:**
   - Don't include sensitive content in notifications
   - Use metadata filtering for sensitive fields

4. **Rotate credentials regularly:**
   - Regenerate webhook URLs periodically
   - Update SMTP passwords

## Next Steps

- [File Watching Guide](./WATCHING.md) - Real-time monitoring
- [Configuration Reference](./CONFIGURATION.md) - Full config options
- [API Documentation](./API.md) - Programmatic usage
- [Examples](../examples/) - More code examples

# Notifications Examples

This directory contains example configurations for RAGVersion's notification system.

## Quick Start

1. **Choose an example** based on your notification provider:
   - `slack_example.yaml` - Slack notifications
   - `discord_example.yaml` - Discord notifications
   - `email_example.yaml` - Email notifications via SMTP
   - `webhook_example.yaml` - Custom webhook integrations
   - `multi_provider_example.yaml` - Multiple providers simultaneously

2. **Copy and customize** the example:
   ```bash
   cp slack_example.yaml my-notifications.yaml
   # Edit my-notifications.yaml with your credentials
   ```

3. **Use with CLI**:
   ```bash
   # Watch directory with notifications
   ragversion watch ./documents --config my-notifications.yaml
   ```

4. **Use programmatically**:
   ```python
   from ragversion import AsyncVersionTracker
   from ragversion.storage.sqlite import SQLiteStorage
   from ragversion.config import RAGVersionConfig
   from ragversion.notifications import create_notification_manager

   config = RAGVersionConfig.load("my-notifications.yaml")
   notification_manager = create_notification_manager(
       config.notifications.notifiers
   )

   storage = SQLiteStorage(config.sqlite.db_path)
   tracker = AsyncVersionTracker(
       storage=storage,
       notification_manager=notification_manager
   )

   async with tracker:
       await tracker.track("./documents/report.pdf")
   ```

## Examples Overview

### Slack Example
- **File**: `slack_example.yaml`
- **Use case**: Team notifications in Slack channels
- **Features**: Rich formatting, user mentions, channel overrides
- **Setup**: Create Slack incoming webhook

### Discord Example
- **File**: `discord_example.yaml`
- **Use case**: Community or dev team notifications in Discord
- **Features**: Embeds, user/role mentions, avatars
- **Setup**: Create Discord webhook

### Email Example
- **File**: `email_example.yaml`
- **Use case**: Formal notifications to email recipients
- **Features**: HTML/plain text, CC, multiple SMTP providers
- **Setup**: Configure SMTP credentials

### Webhook Example
- **File**: `webhook_example.yaml`
- **Use case**: Custom API integrations
- **Features**: Flexible HTTP method, custom headers, standardized payload
- **Setup**: Create API endpoint to receive webhooks

### Multi-Provider Example
- **File**: `multi_provider_example.yaml`
- **Use case**: Enterprise setup with multiple teams and systems
- **Features**: All providers combined, environment variables, redundancy
- **Setup**: Configure multiple providers

## Security Best Practices

### 1. Use Environment Variables

Instead of hardcoding credentials in YAML:

```yaml
notifications:
  notifiers:
    - type: slack
      webhook_url: ${SLACK_WEBHOOK_URL}  # From environment
```

Create a `.env` file:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
```

### 2. Protect Configuration Files

```bash
# Set restrictive permissions
chmod 600 my-notifications.yaml

# Add to .gitignore
echo "my-notifications.yaml" >> .gitignore
echo ".env" >> .gitignore
```

### 3. Rotate Credentials Regularly

- Regenerate webhook URLs periodically
- Update SMTP passwords
- Rotate API tokens

## Common Patterns

### Pattern 1: Critical Alerts Only

Only send notifications for deletions:

```yaml
notifications:
  notifiers:
    - type: slack
      name: critical-alerts
      webhook_url: ${SLACK_WEBHOOK_URL}
      mention_users: ["U123456"]
      mention_on_types: ["deleted"]  # Only deletions
```

### Pattern 2: Environment-Specific

Different notifications per environment:

```python
# Load different configs per environment
env = os.getenv("ENVIRONMENT", "development")
config = RAGVersionConfig.load(f"notifications-{env}.yaml")
```

### Pattern 3: Conditional Notifications

Enable/disable notifiers dynamically:

```python
# Disable during maintenance
if maintenance_mode:
    manager.disable_notifier("team-slack")

# Re-enable after maintenance
manager.enable_notifier("team-slack")
```

### Pattern 4: Metadata-Rich Notifications

Include context in notifications:

```python
metadata = {
    "environment": "production",
    "triggered_by": "automated_sync",
    "project": "customer-docs",
    "criticality": "high"
}

await tracker.track("./docs/important.pdf", metadata=metadata)
```

## Testing Notifications

### Test Individual Notifier

```python
from ragversion.notifications import SlackNotifier, SlackConfig
from ragversion.models import ChangeEvent, ChangeType
from datetime import datetime
from uuid import uuid4

# Create test event
event = ChangeEvent(
    document_id=uuid4(),
    version_id=uuid4(),
    change_type=ChangeType.MODIFIED,
    file_name="test.pdf",
    file_path="/path/to/test.pdf",
    file_size=1024,
    content_hash="test-hash",
    version_number=2,
    previous_hash="old-hash",
    timestamp=datetime.utcnow()
)

# Test notifier
config = SlackConfig(
    name="test",
    enabled=True,
    webhook_url="YOUR_WEBHOOK_URL"
)
notifier = SlackNotifier(config)

success = await notifier.send(event)
print(f"Notification {'sent' if success else 'failed'}")
```

### Test Multi-Provider Setup

```python
from ragversion.config import RAGVersionConfig
from ragversion.notifications import create_notification_manager

config = RAGVersionConfig.load("multi_provider_example.yaml")
manager = create_notification_manager(config.notifications.notifiers)

# Test with mock event
results = await manager.notify(event)

# Check results
for notifier_name, success in results.items():
    status = "✓" if success else "✗"
    print(f"{status} {notifier_name}")
```

## Troubleshooting

### Issue: Notifications not sending

**Check 1: Verify configuration**
```python
config = RAGVersionConfig.load("my-notifications.yaml")
print(config.notifications.enabled)
print(config.notifications.notifiers)
```

**Check 2: Enable debug logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check 3: Test individual notifier**
```python
# Test each notifier separately
for notifier in manager.notifiers:
    print(f"Testing {notifier.config.name}...")
    success = await notifier.send(test_event)
    print(f"Result: {success}")
```

### Issue: Webhook authentication errors

- Verify Authorization header format
- Check API token validity
- Confirm endpoint URL

### Issue: Email sending failures

- Gmail: Use app password, not account password
- Check SMTP host and port
- Verify TLS/SSL settings

## Next Steps

- [Full Documentation](../../docs/NOTIFICATIONS.md)
- [Configuration Guide](../../docs/CONFIGURATION.md)
- [API Reference](../../docs/API.md)

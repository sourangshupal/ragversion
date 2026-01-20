"""Email notification provider."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from pydantic import Field

from ragversion.models import ChangeEvent
from ragversion.notifications.base import BaseNotifier, NotificationConfig

logger = logging.getLogger(__name__)


class EmailConfig(NotificationConfig):
    """Email notification configuration."""

    smtp_host: str = Field(..., description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(..., description="SMTP username")
    smtp_password: str = Field(..., description="SMTP password")
    use_tls: bool = Field(default=True, description="Use TLS encryption")
    from_address: str = Field(..., description="Sender email address")
    to_addresses: list[str] = Field(..., description="Recipient email addresses")
    cc_addresses: list[str] = Field(default_factory=list, description="CC addresses")
    subject_prefix: str = Field(
        default="[RAGVersion]", description="Email subject prefix"
    )


class EmailNotifier(BaseNotifier):
    """Send notifications via email (SMTP)."""

    def __init__(self, config: EmailConfig) -> None:
        """Initialize email notifier.

        Args:
            config: Email configuration
        """
        super().__init__(config)
        self.config: EmailConfig = config

    async def send(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send email notification.

        Args:
            change: The change event
            metadata: Optional additional metadata

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug(f"Email notifier '{self.config.name}' is disabled")
            return False

        try:
            # Build email
            msg = self._build_email(change, metadata)

            # Send via SMTP
            self._send_smtp(msg)

            logger.info(f"Sent email notification for {change.file_name}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email notification: {e}")
            return False

    def _build_email(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> MIMEMultipart:
        """Build email message.

        Args:
            change: The change event
            metadata: Optional metadata

        Returns:
            Email message
        """
        # Create message
        msg = MIMEMultipart("alternative")

        # Subject
        icon = {
            "created": "✨",
            "modified": "📝",
            "deleted": "🗑️",
            "restored": "♻️",
        }.get(change.change_type.value, "📄")

        msg["Subject"] = (
            f"{self.config.subject_prefix} {icon} "
            f"{change.change_type.value.title()}: {change.file_name}"
        )
        msg["From"] = self.config.from_address
        msg["To"] = ", ".join(self.config.to_addresses)

        if self.config.cc_addresses:
            msg["Cc"] = ", ".join(self.config.cc_addresses)

        # Plain text version
        text_body = self._build_text_body(change, metadata)
        msg.attach(MIMEText(text_body, "plain"))

        # HTML version
        html_body = self._build_html_body(change, metadata)
        msg.attach(MIMEText(html_body, "html"))

        return msg

    def _build_text_body(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build plain text email body."""
        lines = [
            f"Document {change.change_type.value.upper()}: {change.file_name}",
            "=" * 60,
            "",
            f"File: {change.file_name}",
            f"Path: {change.file_path}",
            f"Version: {change.version_number}",
            f"Size: {self._format_size(change.file_size)}",
            f"Hash: {change.content_hash[:16]}...",
            f"Time: {change.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]

        if metadata:
            lines.append("")
            lines.append("Additional Information:")
            for key, value in metadata.items():
                lines.append(f"  {key.title()}: {value}")

        lines.extend(
            [
                "",
                "---",
                "Powered by RAGVersion",
                "https://github.com/sourangshupal/ragversion",
            ]
        )

        return "\n".join(lines)

    def _build_html_body(
        self, change: ChangeEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build HTML email body."""
        # Color for change type
        color = {
            "created": "#36a64f",
            "modified": "#ff9900",
            "deleted": "#ff0000",
            "restored": "#2196F3",
        }.get(change.change_type.value, "#cccccc")

        # Icon
        icon = {
            "created": "✨",
            "modified": "📝",
            "deleted": "🗑️",
            "restored": "♻️",
        }.get(change.change_type.value, "📄")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
                .field {{ margin-bottom: 10px; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; font-family: monospace; }}
                .footer {{ margin-top: 20px; text-align: center; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{icon} Document {change.change_type.value.title()}</h2>
                </div>
                <div class="content">
                    <div class="field">
                        <span class="label">File:</span>
                        <span class="value">{change.file_name}</span>
                    </div>
                    <div class="field">
                        <span class="label">Path:</span>
                        <span class="value">{change.file_path}</span>
                    </div>
                    <div class="field">
                        <span class="label">Version:</span>
                        <span class="value">{change.version_number}</span>
                    </div>
                    <div class="field">
                        <span class="label">Size:</span>
                        <span class="value">{self._format_size(change.file_size)}</span>
                    </div>
                    <div class="field">
                        <span class="label">Hash:</span>
                        <span class="value">{change.content_hash[:16]}...</span>
                    </div>
                    <div class="field">
                        <span class="label">Time:</span>
                        <span class="value">{change.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
                    </div>
        """

        if metadata:
            html += '<hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">'
            html += '<h3 style="color: #555;">Additional Information</h3>'
            for key, value in metadata.items():
                html += f"""
                    <div class="field">
                        <span class="label">{key.title()}:</span>
                        <span class="value">{value}</span>
                    </div>
                """

        html += """
                </div>
                <div class="footer">
                    <p>Powered by <a href="https://github.com/sourangshupal/ragversion">RAGVersion</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _send_smtp(self, msg: MIMEMultipart) -> None:
        """Send email via SMTP.

        Args:
            msg: Email message to send
        """
        # Get all recipients
        recipients = self.config.to_addresses + self.config.cc_addresses

        # Connect to SMTP server
        if self.config.use_tls:
            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=self.config.timeout_seconds)
            server.starttls()
        else:
            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=self.config.timeout_seconds)

        try:
            # Login
            server.login(self.config.smtp_username, self.config.smtp_password)

            # Send email
            server.send_message(msg, to_addrs=recipients)

        finally:
            server.quit()

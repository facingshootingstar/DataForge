"""
DataForge - Notifier
=====================
Multi-channel notification system.
Supports Slack webhooks and email (SMTP).
"""

from __future__ import annotations

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

import requests
from loguru import logger

from config import NOTIFICATIONS


class Notifier:
    """
    Send notifications via Slack and/or email.

    Usage:
        notifier = Notifier()
        notifier.send_slack("Pipeline completed! ✅")
        notifier.send_email(
            subject="Daily Report",
            body="Your report is ready.",
            attachments=["output/report.html"],
        )
    """

    # ── Slack ────────────────────────────────────────────────

    @staticmethod
    def send_slack(
        message: str,
        webhook_url: str | None = None,
        blocks: list[dict] | None = None,
    ) -> bool:
        """Send a Slack notification via webhook."""
        url = webhook_url or NOTIFICATIONS.slack_webhook
        if not url:
            logger.warning("Slack webhook URL not configured – skipping notification")
            return False

        payload: dict = {"text": message}
        if blocks:
            payload["blocks"] = blocks

        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Slack notification failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return False

    @staticmethod
    def send_slack_report(
        title: str,
        summary: str,
        stats: dict[str, str],
        status: str = "success",
    ) -> bool:
        """Send a rich Slack report with blocks."""
        emoji = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
        color = "#22c55e" if status == "success" else "#ef4444" if status == "error" else "#f59e0b"

        stats_text = "\n".join(f"• *{k}*: {v}" for k, v in stats.items())

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} {title}"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": summary},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Pipeline Stats:*\n{stats_text}"},
            },
        ]

        return Notifier.send_slack(f"{emoji} {title}", blocks=blocks)

    # ── Email ────────────────────────────────────────────────

    @staticmethod
    def send_email(
        subject: str,
        body: str,
        to: str | None = None,
        attachments: list[str | Path] | None = None,
        html: bool = False,
    ) -> bool:
        """Send an email notification with optional attachments."""
        cfg = NOTIFICATIONS
        if not cfg.smtp_user:
            logger.warning("SMTP not configured – skipping email notification")
            return False

        recipient = to or cfg.notify_email
        if not recipient:
            logger.warning("No email recipient configured")
            return False

        msg = MIMEMultipart()
        msg["From"] = cfg.smtp_user
        msg["To"] = recipient
        msg["Subject"] = subject

        # Body
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))

        # Attachments
        if attachments:
            for filepath in attachments:
                filepath = Path(filepath)
                if not filepath.exists():
                    logger.warning(f"Attachment not found: {filepath}")
                    continue

                part = MIMEBase("application", "octet-stream")
                part.set_payload(filepath.read_bytes())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filepath.name}",
                )
                msg.attach(part)
                logger.debug(f"Attached: {filepath.name}")

        try:
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
                server.starttls()
                server.login(cfg.smtp_user, cfg.smtp_password)
                server.send_message(msg)
            logger.info(f"Email sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False

    # ── Convenience ──────────────────────────────────────────

    @staticmethod
    def notify_all(
        message: str,
        subject: str | None = None,
    ) -> dict[str, bool]:
        """Send notification via all configured channels."""
        results = {}
        results["slack"] = Notifier.send_slack(message)
        if subject:
            results["email"] = Notifier.send_email(subject=subject, body=message)
        return results

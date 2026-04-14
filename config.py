"""
DataForge - Configuration Management
=====================================
Centralized configuration with environment variable support,
validation, and sensible defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(Path(__file__).parent / ".env")


def _env(key: str, default: str = "") -> str:
    """Read an environment variable with fallback."""
    return os.getenv(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("true", "1", "yes")


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


# ── Paths ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = Path(_env("DATA_DIR", str(BASE_DIR / "data")))
OUTPUT_DIR = Path(_env("OUTPUT_DIR", str(BASE_DIR / "output")))
TEMPLATES_DIR = BASE_DIR / "templates"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
for _dir in (DATA_DIR, OUTPUT_DIR, LOG_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# ── API Keys ─────────────────────────────────────────────────
OPENAI_API_KEY: str = _env("OPENAI_API_KEY")
ANTHROPIC_API_KEY: str = _env("ANTHROPIC_API_KEY")


# ── Scraping ─────────────────────────────────────────────────
@dataclass(frozen=True)
class ScrapingConfig:
    headless: bool = _env_bool("SCRAPE_HEADLESS", True)
    timeout_ms: int = _env_int("SCRAPE_TIMEOUT", 30_000)
    user_agent: str = _env(
        "SCRAPE_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )
    max_retries: int = 3
    retry_delay: float = 2.0  # seconds


SCRAPING = ScrapingConfig()


# ── Notifications ────────────────────────────────────────────
@dataclass(frozen=True)
class NotificationConfig:
    slack_webhook: str = _env("SLACK_WEBHOOK_URL")
    smtp_host: str = _env("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = _env_int("SMTP_PORT", 587)
    smtp_user: str = _env("SMTP_USER")
    smtp_password: str = _env("SMTP_PASSWORD")
    notify_email: str = _env("NOTIFY_EMAIL")


NOTIFICATIONS = NotificationConfig()


# ── AI / LLM ────────────────────────────────────────────────
@dataclass(frozen=True)
class AIConfig:
    model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    temperature: float = 0.3


AI = AIConfig()


# ── Cleaning Rules ───────────────────────────────────────────
@dataclass
class CleaningConfig:
    """Default rules applied during data cleaning."""
    strip_whitespace: bool = True
    remove_duplicates: bool = True
    fill_missing_strategy: str = "smart"  # smart | drop | ffill | bfill | value
    fill_value: str | None = None
    normalize_dates: bool = True
    date_format: str = "%Y-%m-%d"
    normalize_currency: bool = True
    currency_locale: str = "en_US"
    standardize_phone: bool = True
    phone_country: str = "US"
    email_validation: bool = True
    case_normalization: str = "none"  # none | lower | upper | title


CLEANING = CleaningConfig()


# ── Logging ──────────────────────────────────────────────────
LOG_LEVEL: str = _env("LOG_LEVEL", "INFO")


# ── Quick Validation ────────────────────────────────────────
def validate_config() -> list[str]:
    """Return a list of configuration warnings (empty = all good)."""
    warnings: list[str] = []
    if not OPENAI_API_KEY:
        warnings.append("OPENAI_API_KEY not set – AI analysis will be unavailable.")
    if not NOTIFICATIONS.slack_webhook:
        warnings.append("SLACK_WEBHOOK_URL not set – Slack notifications disabled.")
    if not NOTIFICATIONS.smtp_user:
        warnings.append("SMTP_USER not set – email notifications disabled.")
    return warnings

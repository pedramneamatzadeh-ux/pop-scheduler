"""
Configuration management for Pop Scheduler Bot.
Loads settings from .env file and provides centralized access.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ── Required ────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
DATABASE: str = os.getenv("DATABASE", "scheduler.db")

# ── Optional (with defaults) ────────────────────────────────────────────────
ADMIN_IDS: list[int] = []
_raw_admins = os.getenv("ADMIN_IDS", "")
if _raw_admins.strip():
    ADMIN_IDS = [int(x.strip()) for x in _raw_admins.split(",") if x.strip().isdigit()]

CHANNELS: list[int] = []
_raw_channels = os.getenv("CHANNELS", "")
if _raw_channels.strip():
    CHANNELS = [int(x.strip()) for x in _raw_channels.split(",") if x.strip().lstrip("-").isdigit()]

# ── Default posting hours (24h format) ──────────────────────────────────────
DEFAULT_HOURS: list[int] = [8, 11, 14, 17, 20, 23]

# ── Timezone ────────────────────────────────────────────────────────────────
TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Berlin")

# ── Validation ──────────────────────────────────────────────────────────────
def validate() -> list[str]:
    """Return list of missing required settings."""
    errors = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is required in .env")
    if not OWNER_ID:
        errors.append("OWNER_ID is required in .env")
    return errors

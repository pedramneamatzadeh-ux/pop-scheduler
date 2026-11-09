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
# NOTE: Channels and admins are managed from settings panel (DB), not env.

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

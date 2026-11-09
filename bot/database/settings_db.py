"""
Database operations for settings — channels, admins, default hours.
"""
import json
import logging
from .core import DatabaseCore

logger = logging.getLogger(__name__)


class SettingsDB:
    """Manage channels, admins, and app settings."""

    def __init__(self, core: DatabaseCore):
        self.core = core

    # ── Channels ────────────────────────────────────────────────────────────

    def get_channels(self, active_only: bool = True) -> list[dict]:
        """Get all channels."""
        with self.core.connection() as conn:
            if active_only:
                rows = conn.execute(
                    "SELECT * FROM channels WHERE is_active = 1 ORDER BY added_at"
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM channels ORDER BY added_at").fetchall()
            return [dict(r) for r in rows]

    def get_channel(self, channel_id: str) -> dict | None:
        """Get a single channel."""
        with self.core.connection() as conn:
            row = conn.execute(
                "SELECT * FROM channels WHERE channel_id = ?", (channel_id,)
            ).fetchone()
            return dict(row) if row else None

    def add_channel(self, channel_id: str, title: str = "", username: str = "") -> bool:
        """Add a channel. Returns True if added, False if already exists."""
        with self.core.connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO channels (channel_id, title, username) VALUES (?, ?, ?)",
                    (channel_id, title, username)
                )
                return True
            except Exception:
                return False

    def remove_channel(self, channel_id: str) -> bool:
        """Remove a channel. Returns True if removed."""
        with self.core.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM channels WHERE channel_id = ?", (channel_id,)
            )
            return cursor.rowcount > 0

    def update_channel(self, channel_id: str, title: str = None, username: str = None):
        """Update channel info."""
        with self.core.connection() as conn:
            if title is not None and username is not None:
                conn.execute(
                    "UPDATE channels SET title = ?, username = ? WHERE channel_id = ?",
                    (title, username, channel_id)
                )
            elif title is not None:
                conn.execute(
                    "UPDATE channels SET title = ? WHERE channel_id = ?",
                    (title, channel_id)
                )
            elif username is not None:
                conn.execute(
                    "UPDATE channels SET username = ? WHERE channel_id = ?",
                    (username, channel_id)
                )

    # ── Admins ──────────────────────────────────────────────────────────────

    def get_admins(self) -> list[dict]:
        """Get all admins."""
        with self.core.connection() as conn:
            rows = conn.execute("SELECT * FROM admins ORDER BY added_at").fetchall()
            return [dict(r) for r in rows]

    def get_admin(self, user_id: int) -> dict | None:
        """Get a single admin."""
        with self.core.connection() as conn:
            row = conn.execute(
                "SELECT * FROM admins WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def add_admin(self, user_id: int, username: str = "", first_name: str = "") -> bool:
        """Add an admin. Returns True if added, False if already exists."""
        with self.core.connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO admins (user_id, username, first_name) VALUES (?, ?, ?)",
                    (user_id, username, first_name)
                )
                return True
            except Exception:
                return False

    def remove_admin(self, user_id: int) -> bool:
        """Remove an admin. Returns True if removed."""
        with self.core.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM admins WHERE user_id = ?", (user_id,)
            )
            return cursor.rowcount > 0

    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin (in DB or is owner)."""
        admin = self.get_admin(user_id)
        return admin is not None

    # ── Default Hours ───────────────────────────────────────────────────────

    def get_default_hours(self) -> list[int]:
        """Get default posting hours."""
        raw = self.core.get_setting("default_hours", None)
        if raw:
            return json.loads(raw)
        from ..config import DEFAULT_HOURS
        return DEFAULT_HOURS

    def set_default_hours(self, hours: list[int]):
        """Set default posting hours."""
        self.core.set_setting("default_hours", json.dumps(sorted(hours)))

    def add_hour(self, hour: int) -> bool:
        """Add an hour to default hours. Returns True if added."""
        hours = self.get_default_hours()
        if hour in hours:
            return False
        hours.append(hour)
        self.set_default_hours(hours)
        return True

    def remove_hour(self, hour: int) -> bool:
        """Remove an hour from default hours. Returns True if removed."""
        hours = self.get_default_hours()
        if hour not in hours:
            return False
        hours.remove(hour)
        self.set_default_hours(hours)
        return True

    # ── History Log ─────────────────────────────────────────────────────────

    def add_history_log(self, post_id: int, action: str, details: str = None, user_id: int = None):
        """Add a history log entry."""
        with self.core.connection() as conn:
            conn.execute(
                "INSERT INTO post_history (post_id, action, details, user_id) VALUES (?, ?, ?, ?)",
                (post_id, action, details, user_id)
            )

    def get_history_logs(self, post_id: int = None, limit: int = 50) -> list[dict]:
        """Get history log entries."""
        with self.core.connection() as conn:
            if post_id:
                rows = conn.execute(
                    "SELECT * FROM post_history WHERE post_id = ? ORDER BY created_at DESC LIMIT ?",
                    (post_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM post_history ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

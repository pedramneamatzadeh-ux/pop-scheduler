"""
Database operations for scheduled posts.
"""
import json
import logging
from datetime import datetime
from .core import DatabaseCore
from ..constants import STATUS_PENDING, STATUS_SENT, STATUS_FAILED, STATUS_CANCELLED

logger = logging.getLogger(__name__)


class SchedulerDB:
    """CRUD operations for scheduled posts."""

    def __init__(self, core: DatabaseCore):
        self.core = core

    # ── Create ──────────────────────────────────────────────────────────────

    def add_post(self, chat_id: int, user_id: int,
                 source_channel: str, source_channel_title: str,
                 message_ids: list[int],
                 target_channel: str, target_channel_title: str,
                 schedule_date: str, schedule_time: str,
                 schedule_timestamp: float) -> int:
        """Add a new scheduled post. Returns the post id."""
        with self.core.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO scheduled_posts
                   (chat_id, user_id, source_channel, source_channel_title,
                    message_ids, target_channel, target_channel_title,
                    schedule_date, schedule_time, schedule_timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chat_id, user_id, source_channel, source_channel_title,
                 json.dumps(message_ids), target_channel, target_channel_title,
                 schedule_date, schedule_time, schedule_timestamp)
            )
            post_id = cursor.lastrowid
            # Add history entry
            conn.execute(
                "INSERT INTO post_history (post_id, action, details, user_id) VALUES (?, ?, ?, ?)",
                (post_id, "created",
                 f"Scheduled {len(message_ids)} message(s) for {schedule_date} {schedule_time}",
                 user_id)
            )
            return post_id

    # ── Read ────────────────────────────────────────────────────────────────

    def get_post(self, post_id: int) -> dict | None:
        """Get a single post by ID."""
        with self.core.connection() as conn:
            row = conn.execute(
                "SELECT * FROM scheduled_posts WHERE id = ?", (post_id,)
            ).fetchone()
            if row:
                return self._row_to_post(row)
            return None

    def get_pending_posts(self) -> list[dict]:
        """Get all pending posts ordered by schedule timestamp."""
        with self.core.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_posts WHERE status = ? ORDER BY schedule_timestamp",
                (STATUS_PENDING,)
            ).fetchall()
            return [self._row_to_post(r) for r in rows]

    def get_posts_by_status(self, status: str, limit: int = 50, offset: int = 0) -> list[dict]:
        """Get posts filtered by status."""
        with self.core.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_posts WHERE status = ? ORDER BY schedule_timestamp DESC LIMIT ? OFFSET ?",
                (status, limit, offset)
            ).fetchall()
            return [self._row_to_post(r) for r in rows]

    def get_posts_by_channel(self, channel_id: str, status: str = None) -> list[dict]:
        """Get posts for a specific target channel."""
        with self.core.connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM scheduled_posts WHERE target_channel = ? AND status = ? ORDER BY schedule_timestamp",
                    (channel_id, status)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM scheduled_posts WHERE target_channel = ? ORDER BY schedule_timestamp",
                    (channel_id,)
                ).fetchall()
            return [self._row_to_post(r) for r in rows]

    def get_history(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """Get sent/failed posts (history)."""
        with self.core.connection() as conn:
            rows = conn.execute(
                """SELECT * FROM scheduled_posts
                   WHERE status IN (?, ?)
                   ORDER BY COALESCE(sent_at, updated_at) DESC
                   LIMIT ? OFFSET ?""",
                (STATUS_SENT, STATUS_FAILED, limit, offset)
            ).fetchall()
            return [self._row_to_post(r) for r in rows]

    def count_by_status(self, status: str) -> int:
        """Count posts with given status."""
        with self.core.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM scheduled_posts WHERE status = ?", (status,)
            ).fetchone()
            return row[0]

    def count_history(self) -> int:
        """Count total history entries."""
        with self.core.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM scheduled_posts WHERE status IN (?, ?)",
                (STATUS_SENT, STATUS_FAILED)
            ).fetchone()
            return row[0]

    def get_due_posts(self, current_timestamp: float) -> list[dict]:
        """Get all pending posts that are due for delivery."""
        with self.core.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_posts WHERE status = ? AND schedule_timestamp <= ? ORDER BY schedule_timestamp",
                (STATUS_PENDING, current_timestamp)
            ).fetchall()
            return [self._row_to_post(r) for r in rows]

    # ── Update ──────────────────────────────────────────────────────────────

    def update_schedule(self, post_id: int, schedule_date: str, schedule_time: str,
                        schedule_timestamp: float):
        """Update post schedule date/time."""
        with self.core.connection() as conn:
            conn.execute(
                """UPDATE scheduled_posts
                   SET schedule_date = ?, schedule_time = ?, schedule_timestamp = ?,
                       updated_at = datetime('now')
                   WHERE id = ?""",
                (schedule_date, schedule_time, schedule_timestamp, post_id)
            )

    def update_status(self, post_id: int, status: str, failed_reason: str = None):
        """Update post status."""
        with self.core.connection() as conn:
            if status == STATUS_SENT:
                conn.execute(
                    """UPDATE scheduled_posts
                       SET status = ?, sent_at = datetime('now'), updated_at = datetime('now')
                       WHERE id = ?""",
                    (status, post_id)
                )
            else:
                conn.execute(
                    """UPDATE scheduled_posts
                       SET status = ?, failed_reason = ?, updated_at = datetime('now')
                       WHERE id = ?""",
                    (status, failed_reason, post_id)
                )
            # Add history entry
            action = "sent" if status == STATUS_SENT else "failed"
            details = failed_reason if failed_reason else None
            conn.execute(
                "INSERT INTO post_history (post_id, action, details) VALUES (?, ?, ?)",
                (post_id, action, details)
            )

    def update_target_channel(self, post_id: int, channel_id: str, channel_title: str):
        """Update target channel for a post."""
        with self.core.connection() as conn:
            conn.execute(
                """UPDATE scheduled_posts
                   SET target_channel = ?, target_channel_title = ?, updated_at = datetime('now')
                   WHERE id = ?""",
                (channel_id, channel_title, post_id)
            )

    # ── Delete ──────────────────────────────────────────────────────────────

    def delete_post(self, post_id: int) -> bool:
        """Delete a post. Returns True if deleted."""
        with self.core.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM scheduled_posts WHERE id = ?", (post_id,)
            )
            return cursor.rowcount > 0

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_post(row) -> dict:
        """Convert a database row to a post dict."""
        post = dict(row)
        post["message_ids"] = json.loads(post["message_ids"])
        return post

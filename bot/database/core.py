"""
Database core — connection management, initialization and migrations.
"""
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseCore:
    """Manages SQLite connection and schema."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    @contextmanager
    def connection(self):
        """Get a database connection with proper settings."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init(self):
        """Initialize database schema and run migrations."""
        with self.connection() as conn:
            # Core schema
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS scheduled_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_data TEXT NOT NULL,
                    content_type TEXT NOT NULL DEFAULT 'text',
                    target_channel TEXT NOT NULL,
                    target_channel_title TEXT DEFAULT '',
                    schedule_date TEXT NOT NULL,
                    schedule_time TEXT NOT NULL,
                    schedule_timestamp REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    sent_at TEXT,
                    failed_reason TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY,
                    title TEXT DEFAULT '',
                    username TEXT DEFAULT '',
                    added_at TEXT NOT NULL DEFAULT (datetime('now')),
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT DEFAULT '',
                    first_name TEXT DEFAULT '',
                    added_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS post_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    user_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (post_id) REFERENCES scheduled_posts(id) ON DELETE SET NULL
                );
            """)

            # Indexes
            conn.executescript("""
                CREATE INDEX IF NOT EXISTS idx_posts_status ON scheduled_posts(status);
                CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON scheduled_posts(schedule_timestamp);
                CREATE INDEX IF NOT EXISTS idx_posts_channel ON scheduled_posts(target_channel);
                CREATE INDEX IF NOT EXISTS idx_posts_created ON scheduled_posts(created_at);
                CREATE INDEX IF NOT EXISTS idx_history_post ON post_history(post_id);
            """)

            logger.info("Database initialized at %s", self.db_path)

    def get_setting(self, key: str, default=None):
        """Get a setting value."""
        with self.connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row[0] if row else default

    def set_setting(self, key: str, value):
        """Set a setting value."""
        with self.connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value))
            )

    def delete_setting(self, key: str):
        """Delete a setting."""
        with self.connection() as conn:
            conn.execute("DELETE FROM settings WHERE key = ?", (key,))

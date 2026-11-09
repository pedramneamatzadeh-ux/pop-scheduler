"""
Database package — provides the unified Database class.
"""
from .core import DatabaseCore
from .scheduler_db import SchedulerDB
from .settings_db import SettingsDB, CHANNEL_SOURCE, CHANNEL_DESTINATION


class Database:
    """Unified database interface combining all mixins."""

    def __init__(self, db_path: str):
        self._core = DatabaseCore(db_path)
        self.scheduler = SchedulerDB(self._core)
        self.settings = SettingsDB(self._core)

    def init(self):
        """Initialize the database schema."""
        self._core.init()

    # ── Convenience proxies ─────────────────────────────────────────────────

    def get_setting(self, key: str, default=None):
        return self._core.get_setting(key, default)

    def set_setting(self, key: str, value):
        self._core.set_setting(key, value)

    def delete_setting(self, key: str):
        self._core.delete_setting(key)

    # Proxy scheduler methods
    def add_post(self, **kwargs):
        return self.scheduler.add_post(**kwargs)

    def get_post(self, post_id: int):
        return self.scheduler.get_post(post_id)

    def get_pending_posts(self):
        return self.scheduler.get_pending_posts()

    def get_posts_by_status(self, status: str, **kwargs):
        return self.scheduler.get_posts_by_status(status, **kwargs)

    def get_history(self, **kwargs):
        return self.scheduler.get_history(**kwargs)

    def count_by_status(self, status: str):
        return self.scheduler.count_by_status(status)

    def count_history(self):
        return self.scheduler.count_history()

    def get_due_posts(self, timestamp: float):
        return self.scheduler.get_due_posts(timestamp)

    def update_schedule(self, post_id: int, **kwargs):
        return self.scheduler.update_schedule(post_id, **kwargs)

    def update_status(self, post_id: int, **kwargs):
        return self.scheduler.update_status(post_id, **kwargs)

    def update_target_channel(self, post_id: int, **kwargs):
        return self.scheduler.update_target_channel(post_id, **kwargs)

    def delete_post(self, post_id: int):
        return self.scheduler.delete_post(post_id)

    # Proxy settings methods
    def get_channels(self, **kwargs):
        return self.settings.get_channels(**kwargs)

    def get_channel(self, channel_id: str):
        return self.settings.get_channel(channel_id)

    def add_channel(self, **kwargs):
        return self.settings.add_channel(**kwargs)

    def remove_channel(self, channel_id: str):
        return self.settings.remove_channel(channel_id)

    def update_channel(self, channel_id: str, **kwargs):
        return self.settings.update_channel(channel_id, **kwargs)

    def get_admins(self):
        return self.settings.get_admins()

    def get_admin(self, user_id: int):
        return self.settings.get_admin(user_id)

    def add_admin(self, **kwargs):
        return self.settings.add_admin(**kwargs)

    def remove_admin(self, user_id: int):
        return self.settings.remove_admin(user_id)

    def is_admin(self, user_id: int):
        return self.settings.is_admin(user_id)

    def get_default_hours(self):
        return self.settings.get_default_hours()

    def set_default_hours(self, hours: list[int]):
        return self.settings.set_default_hours(hours)

    def add_hour(self, hour: int):
        return self.settings.add_hour(hour)

    def remove_hour(self, hour: int):
        return self.settings.remove_hour(hour)

    def add_history_log(self, **kwargs):
        return self.settings.add_history_log(**kwargs)

    # Channel type constants
    CHANNEL_SOURCE = "source"
    CHANNEL_DESTINATION = "destination"


# Singleton instance (initialized in main.py)
db: Database = None  # type: ignore

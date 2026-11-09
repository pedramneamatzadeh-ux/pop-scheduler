"""
Test database operations with a temporary database.
"""
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import Database


def _make_db():
    """Create a temporary database for testing."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = Database(tmp.name)
    db.init()
    return db, tmp.name


def _cleanup(path):
    os.unlink(path)


def test_init_creates_tables():
    db, path = _make_db()
    try:
        from bot.database.core import DatabaseCore
        core = DatabaseCore(path)
        with core.connection() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            table_names = {r[0] for r in tables}
            assert "scheduled_posts" in table_names
            assert "settings" in table_names
            assert "channels" in table_names
            assert "admins" in table_names
            assert "post_history" in table_names
    finally:
        _cleanup(path)


def test_add_and_get_post():
    db, path = _make_db()
    try:
        post_id = db.add_post(
            chat_id=123,
            user_id=456,
            message_data={"text": "Hello World"},
            content_type="text",
            target_channel="-100123",
            target_channel_title="Test Channel",
            schedule_date="2026-12-01",
            schedule_time="14:00",
            schedule_timestamp=1796212800.0,
        )
        assert post_id > 0

        post = db.get_post(post_id)
        assert post is not None
        assert post["id"] == post_id
        assert post["target_channel"] == "-100123"
        assert post["target_channel_title"] == "Test Channel"
        assert post["schedule_date"] == "2026-12-01"
        assert post["schedule_time"] == "14:00"
        assert post["status"] == "pending"
        assert post["message_data"]["text"] == "Hello World"
    finally:
        _cleanup(path)


def test_get_pending_posts():
    db, path = _make_db()
    try:
        # Add two pending posts
        id1 = db.add_post(
            chat_id=123, user_id=456,
            message_data={"text": "Post 1"},
            content_type="text",
            target_channel="-100123",
            target_channel_title="Ch",
            schedule_date="2026-12-01",
            schedule_time="14:00",
            schedule_timestamp=1796212800.0,
        )
        id2 = db.add_post(
            chat_id=123, user_id=456,
            message_data={"text": "Post 2"},
            content_type="text",
            target_channel="-100123",
            target_channel_title="Ch",
            schedule_date="2026-12-02",
            schedule_time="08:00",
            schedule_timestamp=1796198400.0,
        )

        pending = db.get_pending_posts()
        assert len(pending) == 2
        # Should be ordered by timestamp (earlier first)
        assert pending[0]["id"] == id2  # 08:00 < 14:00
        assert pending[1]["id"] == id1
    finally:
        _cleanup(path)


def test_update_status():
    db, path = _make_db()
    try:
        post_id = db.add_post(
            chat_id=123, user_id=456,
            message_data={"text": "Test"},
            content_type="text",
            target_channel="-100123",
            target_channel_title="Ch",
            schedule_date="2026-12-01",
            schedule_time="14:00",
            schedule_timestamp=1796212800.0,
        )

        # Update to sent
        db.update_status(post_id, status="sent")
        post = db.get_post(post_id)
        assert post["status"] == "sent"

        # Pending count should be 0
        assert db.count_by_status("pending") == 0
        assert db.count_by_status("sent") == 1
    finally:
        _cleanup(path)


def test_delete_post():
    db, path = _make_db()
    try:
        post_id = db.add_post(
            chat_id=123, user_id=456,
            message_data={"text": "To delete"},
            content_type="text",
            target_channel="-100123",
            target_channel_title="Ch",
            schedule_date="2026-12-01",
            schedule_time="14:00",
            schedule_timestamp=1796212800.0,
        )

        assert db.delete_post(post_id) is True
        assert db.get_post(post_id) is None
        assert db.delete_post(99999) is False
    finally:
        _cleanup(path)


def test_channels():
    db, path = _make_db()
    try:
        assert db.add_channel(channel_id="-100111", title="Channel 1") is True
        assert db.add_channel(channel_id="-100222", title="Channel 2") is True
        assert db.add_channel(channel_id="-100111") is False  # Duplicate

        channels = db.get_channels()
        assert len(channels) == 2

        ch = db.get_channel("-100111")
        assert ch is not None
        assert ch["title"] == "Channel 1"

        assert db.remove_channel("-100111") is True
        assert db.remove_channel("-100111") is False

        channels = db.get_channels()
        assert len(channels) == 1
    finally:
        _cleanup(path)


def test_admins():
    db, path = _make_db()
    try:
        assert db.add_admin(user_id=111, first_name="Admin 1") is True
        assert db.add_admin(user_id=222, first_name="Admin 2") is True
        assert db.add_admin(user_id=111) is False  # Duplicate

        admins = db.get_admins()
        assert len(admins) == 2

        assert db.is_admin(111) is True
        assert db.is_admin(999) is False

        assert db.remove_admin(111) is True
        assert db.is_admin(111) is False
    finally:
        _cleanup(path)


def test_default_hours():
    db, path = _make_db()
    try:
        hours = db.get_default_hours()
        # Should return DEFAULT_HOURS from config since no setting exists yet
        assert hours == [8, 11, 14, 17, 20, 23]

        db.add_hour(10)
        hours = db.get_default_hours()
        assert 10 in hours

        db.remove_hour(10)
        hours = db.get_default_hours()
        assert 10 not in hours

        # Duplicate add should fail
        assert db.add_hour(8) is False
    finally:
        _cleanup(path)


def test_settings():
    db, path = _make_db()
    try:
        assert db.get_setting("test_key") is None
        assert db.get_setting("test_key", "default") == "default"

        db.set_setting("test_key", "test_value")
        assert db.get_setting("test_key") == "test_value"

        db.delete_setting("test_key")
        assert db.get_setting("test_key") is None
    finally:
        _cleanup(path)


def test_get_due_posts():
    db, path = _make_db()
    try:
        # Add posts with different timestamps
        now = 1700000000.0

        db.add_post(
            chat_id=1, user_id=1,
            message_data={"text": "Past"},
            content_type="text",
            target_channel="-100", target_channel_title="Ch",
            schedule_date="2023-01-01", schedule_time="00:00",
            schedule_timestamp=now - 3600,  # 1 hour ago
        )
        db.add_post(
            chat_id=1, user_id=1,
            message_data={"text": "Now"},
            content_type="text",
            target_channel="-100", target_channel_title="Ch",
            schedule_date="2023-01-01", schedule_time="00:00",
            schedule_timestamp=now,  # Now
        )
        db.add_post(
            chat_id=1, user_id=1,
            message_data={"text": "Future"},
            content_type="text",
            target_channel="-100", target_channel_title="Ch",
            schedule_date="2030-01-01", schedule_time="00:00",
            schedule_timestamp=now + 86400,  # 1 day later
        )

        due = db.get_due_posts(now)
        assert len(due) == 2  # Past and Now, not Future
    finally:
        _cleanup(path)


def test_history():
    db, path = _make_db()
    try:
        post_id = db.add_post(
            chat_id=1, user_id=1,
            message_data={"text": "Test"},
            content_type="text",
            target_channel="-100", target_channel_title="Ch",
            schedule_date="2026-12-01", schedule_time="14:00",
            schedule_timestamp=1796212800.0,
        )

        # Initially no history (status is pending)
        history = db.get_history()
        assert len(history) == 0

        # Mark as sent
        db.update_status(post_id, status="sent")
        history = db.get_history()
        assert len(history) == 1
        assert history[0]["status"] == "sent"
        assert db.count_history() == 1
    finally:
        _cleanup(path)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    sys.exit(1 if failed else 0)

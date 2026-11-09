"""
Test that all modules can be imported without errors.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import_config():
    from bot.config import config, Config
    assert isinstance(config, Config)
    assert hasattr(config, "BOT_TOKEN")
    assert hasattr(config, "OWNER_ID")
    assert hasattr(config, "validate")
    assert hasattr(Config, "DEFAULT_HOURS")
    assert Config.DEFAULT_HOURS == [8, 11, 14, 17, 20, 23]


def test_import_constants():
    from bot import constants
    assert hasattr(constants, "MAIN_MENU")
    assert hasattr(constants, "SELECT_SOURCE_CHANNEL")
    assert hasattr(constants, "Msg")
    assert hasattr(constants, "STATUS_PENDING")
    assert hasattr(constants, "MONTH_NAMES")
    assert hasattr(constants, "INPUT_HOUR")


def test_import_database_core():
    from bot.database import core
    assert hasattr(core, "DatabaseCore")


def test_import_database_scheduler():
    from bot.database import scheduler_db
    assert hasattr(scheduler_db, "SchedulerDB")


def test_import_database_settings():
    from bot.database import settings_db
    assert hasattr(settings_db, "SettingsDB")
    assert hasattr(settings_db, "CHANNEL_SOURCE")
    assert hasattr(settings_db, "CHANNEL_DESTINATION")


def test_import_database_init():
    from bot.database import Database
    assert hasattr(Database, "init")
    assert hasattr(Database, "add_post")
    assert hasattr(Database, "get_channels")
    # Channel types are class attributes
    assert Database.CHANNEL_SOURCE == "source"
    assert Database.CHANNEL_DESTINATION == "destination"


def test_import_utils():
    from bot import utils
    assert hasattr(utils, "normalize_digits")
    assert hasattr(utils, "parse_message_ids")
    assert hasattr(utils, "validate_hour_input")
    assert hasattr(utils, "get_month_days")
    assert hasattr(utils, "to_timestamp")
    assert hasattr(utils, "paginate")
    assert hasattr(utils, "is_admin_or_owner")


def test_import_keyboards():
    from bot import keyboards
    assert hasattr(keyboards, "ib")
    assert hasattr(keyboards, "main_menu")
    assert hasattr(keyboards, "source_channels_keyboard")
    assert hasattr(keyboards, "dest_channels_keyboard")
    assert hasattr(keyboards, "datetime_keyboard")
    assert hasattr(keyboards, "months_keyboard")
    assert hasattr(keyboards, "hours_keyboard")
    assert hasattr(keyboards, "inline_cancel_keyboard")


def test_import_decorators():
    from bot import decorators
    assert hasattr(decorators, "owner_only")
    assert hasattr(decorators, "admin_required")


def test_import_services_scheduler():
    from bot.services.scheduler import SchedulerService
    assert hasattr(SchedulerService, "schedule_post")
    assert hasattr(SchedulerService, "start")
    assert hasattr(SchedulerService, "stop")


def test_import_services_delivery():
    from bot.services import delivery
    assert hasattr(delivery, "deliver_post")


def test_import_handlers():
    from bot.handlers import base
    from bot.handlers import schedule
    from bot.handlers import posts
    from bot.handlers import settings
    from bot.handlers import history
    assert hasattr(base, "start_command")
    assert hasattr(schedule, "start_schedule")
    assert hasattr(posts, "show_active_posts")
    assert hasattr(settings, "show_settings")
    assert hasattr(history, "show_history")


def test_import_application():
    from bot import application
    assert hasattr(application, "build_application")


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

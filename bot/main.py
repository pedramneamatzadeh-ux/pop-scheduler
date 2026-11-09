"""
Main entry point for Pop Scheduler Bot.
"""
import logging
import sys
import os

# Set up project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import validate, BOT_TOKEN, DATABASE, OWNER_ID, ADMIN_IDS, CHANNELS, TIMEZONE
from bot.database import Database, db as _db_ref
import bot.database as db_module

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# Reduce httpx noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Validate configuration
    errors = validate()
    if errors:
        for err in errors:
            logger.error("Config error: %s", err)
        sys.exit(1)

    logger.info("Starting Pop Scheduler Bot...")
    logger.info("Owner ID: %d", OWNER_ID)
    logger.info("Admins: %s", ADMIN_IDS)
    logger.info("Database: %s", DATABASE)
    logger.info("Timezone: %s", TIMEZONE)

    # Initialize database
    database = Database(DATABASE)
    database.init()
    db_module.db = database

    # Import initial channels from env if DB is empty
    _import_env_channels(database, CHANNELS)
    _import_env_admins(database, ADMIN_IDS)

    # Build application
    from bot.application import build_application
    app = build_application()

    # Define post_init callback to start scheduler after event loop is ready
    async def post_init(application):
        """Start scheduler after event loop is running."""
        from bot.services.scheduler import scheduler
        scheduler.start()
        count = scheduler.reschedule_all_pending()
        logger.info("Re-scheduled %d pending posts", count)

    app.post_init = post_init

    # Run the bot
    logger.info("Bot is running!")
    app.run_polling(allowed_updates=None, drop_pending_updates=True)


def _import_env_channels(database: Database, channels: list[int]):
    """Import channels from env on first run."""
    existing = database.get_channels(active_only=False)
    if existing:
        return  # Already has channels

    for ch_id in channels:
        try:
            database.add_channel(channel_id=str(ch_id))
            logger.info("Imported channel %s from env", ch_id)
        except Exception:
            pass


def _import_env_admins(database: Database, admin_ids: list[int]):
    """Import admins from env on first run."""
    existing = database.get_admins()
    if existing:
        return  # Already has admins

    for admin_id in admin_ids:
        try:
            database.add_admin(user_id=admin_id)
            logger.info("Imported admin %s from env", admin_id)
        except Exception:
            pass


if __name__ == "__main__":
    main()

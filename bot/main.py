"""
Main entry point for Pop Scheduler Bot.
"""
import logging
import sys
import os

# Set up project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import validate, BOT_TOKEN, DATABASE, OWNER_ID, TIMEZONE
from bot.database import Database
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
    logger.info("Database: %s", DATABASE)
    logger.info("Timezone: %s", TIMEZONE)

    # Initialize database
    database = Database(DATABASE)
    database.init()
    db_module.db = database

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


if __name__ == "__main__":
    main()

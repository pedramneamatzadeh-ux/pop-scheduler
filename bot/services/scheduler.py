"""
Scheduler service — manages APScheduler for post delivery.
"""
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
    """Manages scheduled jobs for post delivery."""

    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._started = False

    def start(self):
        """Start the scheduler."""
        if not self._started:
            self._scheduler.start()
            self._started = True
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Scheduler stopped")

    def schedule_post(self, post_id: int, schedule_timestamp: float, tz_name: str = None):
        """
        Schedule a post for delivery at the given timestamp.
        The job will call delivery.deliver_post when triggered.
        """
        from .delivery import deliver_post

        job_id = f"post_{post_id}"

        # Convert timestamp to datetime
        if tz_name:
            tz = ZoneInfo(tz_name)
        else:
            from ..config import config
            tz = ZoneInfo(config.TIMEZONE)

        target_dt = datetime.fromtimestamp(schedule_timestamp, tz=tz)

        # Remove existing job if any
        self.remove_post(post_id)

        # Add new job
        self._scheduler.add_job(
            deliver_post,
            trigger=DateTrigger(run_date=target_dt),
            args=[post_id],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=60  # 1 minute grace period
        )
        logger.info("Scheduled post %d for %s", post_id, target_dt.isoformat())

    def remove_post(self, post_id: int) -> bool:
        """Remove a scheduled post job. Returns True if removed."""
        job_id = f"post_{post_id}"
        try:
            self._scheduler.remove_job(job_id)
            logger.info("Removed job for post %d", post_id)
            return True
        except Exception:
            return False

    def reschedule_post(self, post_id: int, new_timestamp: float, tz_name: str = None):
        """Reschedule a post to a new time."""
        self.schedule_post(post_id, new_timestamp, tz_name)

    def get_job(self, post_id: int):
        """Get a scheduled job."""
        job_id = f"post_{post_id}"
        return self._scheduler.get_job(job_id)

    def get_all_jobs(self) -> list:
        """Get all scheduled jobs."""
        return self._scheduler.get_jobs()

    def reschedule_all_pending(self):
        """
        Re-schedule all pending posts from the database.
        Called on bot startup to restore jobs.
        """
        from ..database import db
        pending = db.get_pending_posts()
        count = 0
        for post in pending:
            self.schedule_post(post["id"], post["schedule_timestamp"])
            count += 1
        logger.info("Re-scheduled %d pending posts", count)
        return count


# Singleton instance
scheduler = SchedulerService()

"""
Scheduler service — manages APScheduler for post delivery.
Also includes a fallback check on every update for reliability.
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
            # Set job defaults to allow late execution
            self._scheduler.configure(
                job_defaults={
                    'misfire_grace_time': None,  # No limit on lateness
                    'coalesce': True,            # Combine missed runs into one
                }
            )
            self._scheduler.start()
            self._started = True
            logger.info("Scheduler started with misfire_grace_time=None")

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

        # Safety check: refuse to schedule in the past
        now = datetime.now(tz=tz)
        if target_dt <= now:
            logger.warning(
                "Refusing to schedule post %d for past time %s (now is %s)",
                post_id, target_dt.isoformat(), now.isoformat()
            )
            return False

        # Remove existing job if any
        self.remove_post(post_id)

        # Add new job
        # misfire_grace_time=None means the job will be executed no matter how late it is
        # This ensures posts are delivered even after connection issues
        self._scheduler.add_job(
            deliver_post,
            trigger=DateTrigger(run_date=target_dt),
            args=[post_id],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=None  # No grace time limit - deliver even if late
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
            if self.schedule_post(post["id"], post["schedule_timestamp"]):
                count += 1
        logger.info("Re-scheduled %d pending posts", count)
        return count

    async def check_due_posts_fallback(self):
        """
        Fallback: Check and deliver any overdue posts that APScheduler missed.
        Called on every update for reliability.
        """
        from ..database import db
        from .delivery import deliver_post
        from ..constants import STATUS_PENDING

        try:
            current_time = datetime.now(timezone.utc).timestamp()
            pending = db.get_pending_posts()
            
            for post in pending:
                if post["schedule_timestamp"] <= current_time:
                    logger.info("Fallback: Post %d is overdue, delivering now", post["id"])
                    try:
                        await deliver_post(post["id"])
                    except Exception as e:
                        logger.error("Fallback delivery failed for post %d: %s", post["id"], e)
        except Exception as e:
            logger.error("check_due_posts_fallback error: %s", e)


# Singleton instance
scheduler = SchedulerService()

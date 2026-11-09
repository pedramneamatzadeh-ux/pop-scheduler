"""
Utility functions for Pop Scheduler Bot.
"""
import re
import logging
from datetime import datetime, date, time, timezone
from zoneinfo import ZoneInfo
from telegram import Update

logger = logging.getLogger(__name__)


def get_tz(tz_name: str = None) -> ZoneInfo:
    """Get timezone object."""
    if not tz_name:
        from .config import TIMEZONE
        tz_name = TIMEZONE
    return ZoneInfo(tz_name)


def now_tz(tz_name: str = None) -> datetime:
    """Get current datetime in the configured timezone."""
    return datetime.now(get_tz(tz_name))


def fmt_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format a datetime."""
    return dt.strftime(fmt)


def fmt_date(d: date) -> str:
    """Format a date as YYYY-MM-DD."""
    return d.strftime("%Y-%m-%d")


def fmt_time(t: time) -> str:
    """Format a time as HH:MM."""
    return t.strftime("%H:%M")


def parse_date(text: str) -> date | None:
    """Parse a date string (YYYY-MM-DD). Returns None on failure."""
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_time(text: str) -> time | None:
    """Parse a time string (HH:MM). Returns None on failure."""
    text = text.strip()
    for fmt in ("%H:%M", "%H:%M:%S", "%H"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def parse_message_ids(text: str) -> list[int] | None:
    """
    Parse message IDs from text input.
    Supports: single (10), range (10-15), multiple (10,13,17), combined (10,13-15,17)
    Returns sorted unique list of IDs, or None if invalid.
    """
    text = text.strip()
    if not text:
        return None

    # Normalize separators: comma, Persian comma, space
    text = text.replace("،", ",").replace(" ", ",")

    ids = set()

    # Split by comma
    parts = text.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check for range (e.g., "10-15")
        if "-" in part:
            range_match = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                if start > end:
                    return None  # Invalid range
                if start < 1 or end < 1:
                    return None  # IDs must be positive
                # Limit range size to prevent abuse
                if end - start > 1000:
                    return None
                ids.update(range(start, end + 1))
            else:
                return None  # Invalid format
        else:
            # Single ID
            try:
                msg_id = int(part)
                if msg_id < 1:
                    return None
                ids.add(msg_id)
            except ValueError:
                return None

    if not ids:
        return None

    return sorted(ids)


def format_message_ids(ids: list[int], max_display: int = 10) -> str:
    """Format message IDs for display, with compression for ranges."""
    if not ids:
        return ""

    if len(ids) <= max_display:
        return ", ".join(str(i) for i in ids)

    # Show first few and last few
    shown = ids[:max_display // 2] + ids[-(max_display // 2):]
    return ", ".join(str(i) for i in shown) + f" ... ({len(ids)} total)"


def to_timestamp(year: int, month: int, day: int, hour: int, tz_name: str = None) -> float:
    """Convert date components to Unix timestamp."""
    tz = get_tz(tz_name)
    dt = datetime(year, month, day, hour, 0, 0, tzinfo=tz)
    return dt.timestamp()


def format_schedule_display(post: dict) -> str:
    """Format a post for display in lists."""
    from .constants import STATUS_LABELS
    status = STATUS_LABELS.get(post["status"], post["status"])
    target = post.get("target_channel_title") or post["target_channel"]
    msg_ids = post.get("message_ids", [])
    msg_count = len(msg_ids)
    return (
        f"🆔 <code>{post['id']}</code> — {target}\n"
        f"📅 {post['schedule_date']} — {post['schedule_time']} — {status}\n"
        f"📨 {msg_count} پیام"
    )


def format_history_item(post: dict) -> str:
    """Format a history item for display."""
    from .constants import STATUS_LABELS
    status = STATUS_LABELS.get(post["status"], post["status"])
    target = post.get("target_channel_title") or post["target_channel"]
    msg_ids = post.get("message_ids", [])
    msg_count = len(msg_ids)
    sent_at = post.get("sent_at") or post.get("updated_at") or "نامشخص"
    return (
        f"🆔 <code>{post['id']}</code> — {target}\n"
        f"📅 {post['schedule_date']} — {post['schedule_time']}\n"
        f"📨 {msg_count} پیام — {status}\n"
        f"🕐 {sent_at}"
    )


def is_admin_or_owner(user_id: int) -> bool:
    """Check if user is owner or admin."""
    from .config import OWNER_ID
    from .database import db
    if user_id == OWNER_ID:
        return True
    return db.is_admin(user_id)


def owner_only(func):
    """Decorator: only owner can use this handler."""
    from functools import wraps
    from .config import OWNER_ID

    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id != OWNER_ID:
            if update.callback_query:
                await update.callback_query.answer("❌ فقط مالک ربات", show_alert=True)
            elif update.effective_message:
                await update.effective_message.reply_text("❌ فقط مالک ربات")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def admin_required(func):
    """Decorator: only admin/owner can use this handler."""
    from functools import wraps

    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if not is_admin_or_owner(user_id):
            if update.callback_query:
                await update.callback_query.answer("❌ دسترسی غیرمجاز", show_alert=True)
            elif update.effective_message:
                await update.effective_message.reply_text("❌ دسترسی غیرمجاز")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def paginate(items: list, page: int, per_page: int = 5) -> tuple[list, int]:
    """Paginate a list. Returns (page_items, total_pages)."""
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    return items[start:end], total_pages


def truncate_text(text: str, max_len: int = 50) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return "(بدون متن)"
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."

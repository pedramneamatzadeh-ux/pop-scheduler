"""
Utility functions for Pop Scheduler Bot.
"""
import re
import logging
from datetime import datetime, date, time, timezone
from zoneinfo import ZoneInfo
from telegram import Update, Message
from typing import Any

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
    # Try multiple formats
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


def to_timestamp(d: date, t: time, tz_name: str = None) -> float:
    """Convert date + time to Unix timestamp in the configured timezone."""
    tz = get_tz(tz_name)
    dt = datetime.combine(d, t, tzinfo=tz)
    return dt.timestamp()


def format_schedule_display(post: dict) -> str:
    """Format a post for display in lists."""
    from .constants import STATUS_LABELS, CONTENT_TYPE_LABELS
    status = STATUS_LABELS.get(post["status"], post["status"])
    content = CONTENT_TYPE_LABELS.get(post["content_type"], post["content_type"])
    channel = post.get("target_channel_title") or post["target_channel"]
    return (
        f"🆔 <code>{post['id']}</code> — {channel}\n"
        f"📅 {post['schedule_date']} — {post['schedule_time']} — {status}\n"
        f"📄 {content}"
    )


def format_history_item(post: dict) -> str:
    """Format a history item for display."""
    from .constants import STATUS_LABELS, CONTENT_TYPE_LABELS
    status = STATUS_LABELS.get(post["status"], post["status"])
    content = CONTENT_TYPE_LABELS.get(post["content_type"], post["content_type"])
    channel = post.get("target_channel_title") or post["target_channel"]
    sent_at = post.get("sent_at") or post.get("updated_at") or "نامشخص"
    return (
        f"🆔 <code>{post['id']}</code> — {channel}\n"
        f"📅 {post['schedule_date']} — {post['schedule_time']}\n"
        f"📄 {content} — {status}\n"
        f"🕐 {sent_at}"
    )


def extract_message_data(message: Message) -> tuple[dict, str]:
    """
    Extract message data for storage.
    Returns (message_data dict, content_type string).
    """
    data = {
        "text": message.text or message.caption or "",
        "parse_mode": message.parse_mode,
        "entities": [e.to_dict() for e in (message.entities or [])] if message.entities else [],
        "caption_entities": [e.to_dict() for e in (message.caption_entities or [])] if message.caption_entities else [],
    }

    if message.photo:
        # Take the largest photo
        photo = message.photo[-1]
        data["file_id"] = photo.file_id
        data["file_unique_id"] = photo.file_unique_id
        data["width"] = photo.width
        data["height"] = photo.height
        return data, "photo"

    elif message.video:
        data["file_id"] = message.video.file_id
        data["file_unique_id"] = message.video.file_unique_id
        data["duration"] = message.video.duration
        data["width"] = message.video.width
        data["height"] = message.video.height
        return data, "video"

    elif message.document:
        data["file_id"] = message.document.file_id
        data["file_unique_id"] = message.document.file_unique_id
        data["file_name"] = message.document.file_name
        data["mime_type"] = message.document.mime_type
        return data, "document"

    elif message.animation:
        data["file_id"] = message.animation.file_id
        data["file_unique_id"] = message.animation.file_unique_id
        data["duration"] = message.animation.duration
        return data, "animation"

    elif message.audio:
        data["file_id"] = message.audio.file_id
        data["file_unique_id"] = message.audio.file_unique_id
        data["duration"] = message.audio.duration
        data["title"] = message.audio.title
        return data, "audio"

    elif message.voice:
        data["file_id"] = message.voice.file_id
        data["file_unique_id"] = message.voice.file_unique_id
        data["duration"] = message.voice.duration
        return data, "voice"

    elif message.video_note:
        data["file_id"] = message.video_note.file_id
        data["file_unique_id"] = message.video_note.file_unique_id
        data["duration"] = message.video_note.duration
        return data, "video_note"

    elif message.sticker:
        data["file_id"] = message.sticker.file_id
        data["file_unique_id"] = message.sticker.file_unique_id
        return data, "sticker"

    elif message.text:
        return data, "text"

    else:
        # Fallback
        data["message_id"] = message.message_id
        data["chat_id"] = message.chat_id if message.chat else None
        return data, "text"


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

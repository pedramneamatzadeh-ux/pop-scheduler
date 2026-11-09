"""
توابع کمکی و utilities.
"""
import re
import calendar
from datetime import datetime, date, time
from typing import Optional, Tuple, List, Any
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from .config import config


# ============================================================================
# بررسی دسترسی
# ============================================================================

def is_admin_or_owner(user_id: int) -> bool:
    """بررسی اینکه کاربر ادمین یا مالک است."""
    if user_id == config.OWNER_ID:
        return True
    
    from .database import db
    return db.is_admin(user_id)


# ============================================================================
# تبدیل ارقام
# ============================================================================

_DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


def normalize_digits(text: Optional[str]) -> str:
    """تبدیل ارقام فارسی/عربی به انگلیسی."""
    return (text or "").translate(_DIGIT_TRANSLATION)


# ============================================================================
# اعتبارسنجی
# ============================================================================

def parse_message_ids(text: Optional[str]) -> Optional[List[int]]:
    """
    تجزیه آیدی پیام‌ها از متن ورودی.
    
    فرمت‌های پشتیبانی شده:
    - تکی: "10" -> [10]
    - بازه: "10-15" -> [10, 11, 12, 13, 14, 15]
    - چندتایی: "10,13,17" -> [10, 13, 17]
    - ترکیبی: "10,13-15,17" -> [10, 13, 14, 15, 17]
    
    Returns:
        لیست مرتب‌شده از آیدی‌ها، یا None اگر فرمت نامعتبر باشد.
    """
    if not text:
        return None

    # نرمال‌سازی ارقام فارسی/عربی
    clean_text = normalize_digits(text.strip())
    
    # نرمال‌سازی جداکننده‌ها
    clean_text = clean_text.replace("،", ",").replace(" ", ",")
    
    ids = set()
    parts = clean_text.split(",")
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # بررسی بازه (مثل "10-15")
        if "-" in part:
            range_match = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                if start > end or start < 1:
                    return None
                if end - start > 1000:  # محدودیت برای جلوگیری از سوءاستفاده
                    return None
                ids.update(range(start, end + 1))
            else:
                return None
        else:
            # آیدی تکی
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


def format_message_ids(ids: List[int], max_display: int = 10) -> str:
    """فرمت‌بندی آیدی پیام‌ها برای نمایش."""
    if not ids:
        return ""
    
    if len(ids) <= max_display:
        return ", ".join(str(i) for i in ids)
    
    # نمایش چند مورد اول و آخر
    shown = ids[:max_display // 2] + ids[-(max_display // 2):]
    return ", ".join(str(i) for i in shown) + f" ... ({len(ids)} total)"


def validate_hour_input(text: Optional[str]) -> Tuple[bool, int, int]:
    """
    اعتبارسنجی ورودی ساعت.
    
    فرمت‌های پشتیبانی شده:
    - "14" -> (True, 14, 0)
    - "14:30" -> (True, 14, 30)
    - "08:05" -> (True, 8, 5)
    
    Returns:
        (is_valid, hour, minute)
    """
    if not text:
        return False, 0, 0
    
    clean_text = normalize_digits(text.strip())
    
    try:
        if ":" in clean_text:
            parts = clean_text.split(":")
            if len(parts) != 2:
                return False, 0, 0
            hour = int(parts[0])
            minute = int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return False, 0, 0
            return True, hour, minute
        else:
            hour = int(clean_text)
            if not (0 <= hour <= 23):
                return False, 0, 0
            return True, hour, 0
    except ValueError:
        return False, 0, 0


def get_month_days(year: int, month: int) -> int:
    """تعداد روزهای یک ماه."""
    return calendar.monthrange(year, month)[1]


# ============================================================================
# تبدیل زمان
# ============================================================================

def get_tz() -> ZoneInfo:
    """دریافت شی timezone."""
    return ZoneInfo(config.TIMEZONE)


def now_tz() -> datetime:
    """زمان فعلی با timezone تنظیم‌شده."""
    return datetime.now(get_tz())


def to_timestamp(year: int, month: int, day: int, hour: int, minute: int = 0) -> float:
    """تبدیل اجزای تاریخ به timestamp."""
    tz = get_tz()
    dt = datetime(year, month, day, hour, minute, 0, tzinfo=tz)
    return dt.timestamp()


# ============================================================================
# صفحه‌بندی
# ============================================================================

def paginate(items: List[Any], page: int, per_page: int = 5) -> Tuple[List[Any], int]:
    """
    صفحه‌بندی لیست.
    
    Returns:
        (page_items, total_pages)
    """
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    return items[start:end], total_pages


# ============================================================================
# فرمت‌بندی
# ============================================================================

def fmt_date(d: date) -> str:
    """فرمت تاریخ به صورت YYYY-MM-DD."""
    return d.strftime("%Y-%m-%d")


def fmt_time(t: time) -> str:
    """فرمت ساعت به صورت HH:MM."""
    return t.strftime("%H:%M")


def format_schedule_display(post: dict) -> str:
    """فرمت‌بندی پست برای نمایش در لیست."""
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
    """فرمت‌بندی آیتم تاریخچه."""
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

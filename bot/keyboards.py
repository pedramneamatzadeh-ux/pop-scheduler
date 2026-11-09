"""
سازنده‌های کیبورد (Reply و Inline).
"""
import calendar
from typing import List, Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from .constants import MONTH_NAMES, MONTH_NAMES_SHORT
from .utils import get_month_days


# ============================================================================
# Helper برای ساخت دکمه‌ها با رنگ
# ============================================================================

def ib(
    text: str,
    style: Optional[str] = None,
    **kwargs,
) -> InlineKeyboardButton:
    """
    ساخت InlineKeyboardButton با رنگ خودکار.
    
    رنگ‌ها:
    - danger (قرمز): لغو، حذف، بازگشت
    - success (سبز): تأیید، ثبت
    - primary (آبی): پیش‌فرض
    """
    # استنتاج رنگ از متن اگر style صریح نباشد
    if style is None:
        danger_words = ("لغو", "حذف", "بازگشت", "❌")
        success_words = ("تأیید", "ثبت", "✅")
        
        if any(word in text for word in danger_words):
            style = "danger"
        elif any(word in text for word in success_words):
            style = "success"
        else:
            style = "success"  # پیش‌فرض
    
    if style:
        kwargs["style"] = style
    
    return InlineKeyboardButton(text, **kwargs)


# ============================================================================
# منوی اصلی (Reply Keyboard)
# ============================================================================

def main_menu(user_id: int, is_owner: bool = False) -> ReplyKeyboardMarkup:
    """منوی اصلی ربات."""
    keyboard = [
        [
            KeyboardButton(text="📅 زمان‌بندی جدید", style="success"),
            KeyboardButton(text="📋 پست‌های فعال", style="primary"),
        ],
        [
            KeyboardButton(text="📊 تاریخچه", style="primary"),
            KeyboardButton(text="⚙️ تنظیمات", style="primary"),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ============================================================================
# کیبوردهای Inline برای لغو
# ============================================================================

def inline_cancel_keyboard() -> InlineKeyboardMarkup:
    """دکمه لغو به صورت Inline (برای edit_message_text)."""
    return InlineKeyboardMarkup([
        [ib("❌ لغو", callback_data="cancel", style="danger")]
    ])


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """دکمه لغو به صورت Reply (برای send_message)."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text="❌ لغو", style="danger")]],
        resize_keyboard=True,
    )


# ============================================================================
# کیبوردهای انتخاب کانال
# ============================================================================

def source_channels_keyboard(channels: list) -> InlineKeyboardMarkup:
    """کیبورد انتخاب کانال مبدأ."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            ib(f"📥 {title}", callback_data=f"src:{ch['channel_id']}")
        ])
    buttons.append([ib("❌ لغو", callback_data="cancel", style="danger")])
    return InlineKeyboardMarkup(buttons)


def dest_channels_keyboard(channels: list) -> InlineKeyboardMarkup:
    """کیبورد انتخاب کانال مقصد."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            ib(f"📤 {title}", callback_data=f"dst:{ch['channel_id']}")
        ])
    buttons.append([ib("❌ لغو", callback_data="cancel", style="danger")])
    return InlineKeyboardMarkup(buttons)


# ============================================================================
# کیبوردهای تاریخ و ساعت
# ============================================================================

def datetime_keyboard(
    year: int, 
    month: int, 
    day: int, 
    hour: int,
    minute: int = 0,
    prefix: str = "dt"
) -> InlineKeyboardMarkup:
    """
    کیبورد اصلی انتخاب تاریخ و ساعت.
    
    Args:
        prefix: پیشوند callback ('dt' برای زمان‌بندی، 'edt' برای ویرایش)
    """
    month_name = MONTH_NAMES.get(month, str(month))
    max_day = get_month_days(year, month)
    
    buttons = [
        [
            ib(f"🗓 {month_name}", callback_data=f"{prefix}:month"),
            ib(f"📅 {year}", callback_data=f"{prefix}:year"),
        ],
        [
            ib(f"📆 {day} (از 1 تا {max_day})", callback_data=f"{prefix}:day"),
        ],
        [
            ib(f"🕐 {hour:02d}:{minute:02d}", callback_data=f"{prefix}:hour"),
        ],
        [
            ib("✅ ثبت", callback_data=f"{prefix}:submit", style="success"),
        ],
        [
            ib("❌ لغو", callback_data="cancel", style="danger"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def months_keyboard(
    current_month: int, 
    prefix: str = "m",
    back_callback: str = "dt:back"
) -> InlineKeyboardMarkup:
    """کیبورد انتخاب ماه (3 تا در هر ردیف)."""
    buttons = []
    row = []
    
    for m in range(1, 13):
        month_name = MONTH_NAMES_SHORT[m]
        mark = "✅ " if m == current_month else ""
        row.append(ib(f"{mark}{month_name}", callback_data=f"{prefix}:{m}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([ib("🔙 بازگشت", callback_data=back_callback, style="danger")])
    return InlineKeyboardMarkup(buttons)


def hours_keyboard(
    hours: List[int], 
    current_hour: Optional[int] = None,
    prefix: str = "h",
    back_callback: str = "dt:back"
) -> InlineKeyboardMarkup:
    """کیبورد انتخاب ساعت."""
    buttons = []
    row = []
    
    for h in sorted(hours):
        mark = "✅ " if h == current_hour else ""
        row.append(ib(f"{mark}{h:02d}:00", callback_data=f"{prefix}:{h}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([
        ib("✏️ ساعت دلخواه", callback_data=f"{prefix}:custom"),
        ib("🔙 بازگشت", callback_data=back_callback, style="danger"),
    ])
    return InlineKeyboardMarkup(buttons)


# ============================================================================
# کیبوردهای مدیریت پست‌ها
# ============================================================================

def post_list_keyboard(
    posts: list, 
    page: int, 
    total_pages: int
) -> InlineKeyboardMarkup:
    """کیبورد لیست پست‌ها."""
    buttons = []
    
    for post in posts:
        target = post.get("target_channel_title") or post["target_channel"]
        msg_count = len(post.get("message_ids", []))
        label = f"🆔{post['id']} — {target} — {post['schedule_date']} {post['schedule_time']} ({msg_count})"
        if len(label) > 60:
            label = label[:57] + "..."
        buttons.append([
            ib(label, callback_data=f"post:{post['id']}")
        ])
    
    # صفحه‌بندی
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(ib("◀️ قبلی", callback_data=f"pg:posts:{page-1}"))
        nav.append(ib(f"📄 {page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(ib("▶️ بعدی", callback_data=f"pg:posts:{page+1}"))
        buttons.append(nav)
    
    buttons.append([ib("🏠 منوی اصلی", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def post_detail_keyboard(
    post_id: int, 
    status: str = "pending"
) -> InlineKeyboardMarkup:
    """کیبورد جزئیات پست."""
    buttons = []
    
    if status == "pending":
        buttons.append([
            ib("📅 ویرایش تاریخ", callback_data=f"edit_date:{post_id}"),
            ib("🕐 ویرایش ساعت", callback_data=f"edit_time:{post_id}"),
        ])
        buttons.append([
            ib("📢 تغییر مقصد", callback_data=f"edit_ch:{post_id}"),
        ])
        buttons.append([
            ib("🗑 حذف کامل", callback_data=f"del:{post_id}", style="danger"),
            ib("⏸ غیرفعال کردن", callback_data=f"disable_post:{post_id}", style="danger"),
        ])
    elif status == "disabled":
        # پست غیرفعال - فقط می‌تونه فعال کنه یا حذف کنه
        buttons.append([
            ib("▶️ فعال کردن مجدد", callback_data=f"enable_post:{post_id}", style="success"),
        ])
        buttons.append([
            ib("🗑 حذف کامل", callback_data=f"del:{post_id}", style="danger"),
        ])
    
    buttons.append([ib("📋 بازگشت به لیست", callback_data="back_to_list")])
    buttons.append([ib("🏠 منوی اصلی", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(buttons)


def history_keyboard(
    posts: list, 
    page: int, 
    total_pages: int
) -> InlineKeyboardMarkup:
    """کیبورد تاریخچه."""
    buttons = []
    
    for post in posts:
        target = post.get("target_channel_title") or post["target_channel"]
        status_icon = "✅" if post["status"] == "sent" else "❌"
        msg_count = len(post.get("message_ids", []))
        label = f"{status_icon} 🆔{post['id']} — {target} — {post['schedule_date']} ({msg_count})"
        if len(label) > 60:
            label = label[:57] + "..."
        buttons.append([
            ib(label, callback_data=f"hpost:{post['id']}")
        ])
    
    # صفحه‌بندی
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(ib("◀️ قبلی", callback_data=f"pg:history:{page-1}"))
        nav.append(ib(f"📄 {page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(ib("▶️ بعدی", callback_data=f"pg:history:{page+1}"))
        buttons.append(nav)
    
    buttons.append([ib("🏠 منوی اصلی", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


# ============================================================================
# کیبوردهای تنظیمات
# ============================================================================

def settings_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    """کیبورد منوی تنظیمات."""
    buttons = [
        [
            ib("📢 کانال‌ها", callback_data="st:channels"),
            ib("🕐 ساعت‌های پیش‌فرض", callback_data="st:hours"),
        ],
        [
            ib("👥 مدیران", callback_data="st:admins"),
        ],
        [
            ib("🏠 منوی اصلی", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def channels_type_keyboard() -> InlineKeyboardMarkup:
    """کیبورد انتخاب نوع کانال."""
    return InlineKeyboardMarkup([
        [
            ib("📥 کانال‌های مبدأ", callback_data="st:source_channels"),
            ib("📤 کانال‌های مقصد", callback_data="st:dest_channels"),
        ],
        [
            ib("🔙 بازگشت", callback_data="st:back", style="danger"),
        ],
    ])


def source_channels_manage_keyboard(channels: list) -> InlineKeyboardMarkup:
    """کیبورد مدیریت کانال‌های مبدأ."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            ib(f"🗑 {title}", callback_data=f"rmsrc:{ch['channel_id']}", style="danger")
        ])
    buttons.append([ib("➕ افزودن کانال مبدأ", callback_data="add_source")])
    buttons.append([ib("🔙 بازگشت", callback_data="st:channels", style="danger")])
    return InlineKeyboardMarkup(buttons)


def dest_channels_manage_keyboard(channels: list) -> InlineKeyboardMarkup:
    """کیبورد مدیریت کانال‌های مقصد."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            ib(f"🗑 {title}", callback_data=f"rmdst:{ch['channel_id']}", style="danger")
        ])
    buttons.append([ib("➕ افزودن کانال مقصد", callback_data="add_dest")])
    buttons.append([ib("🔙 بازگشت", callback_data="st:channels", style="danger")])
    return InlineKeyboardMarkup(buttons)


def hours_manage_keyboard(hours: List[int]) -> InlineKeyboardMarkup:
    """کیبورد مدیریت ساعت‌ها."""
    buttons = []
    row = []
    
    for h in sorted(hours):
        row.append(ib(f"🗑 {h:02d}:00", callback_data=f"rmh:{h}", style="danger"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([ib("➕ افزودن ساعت", callback_data="add_hour")])
    buttons.append([ib("🔙 بازگشت", callback_data="st:back", style="danger")])
    return InlineKeyboardMarkup(buttons)


def admins_manage_keyboard(admins: list) -> InlineKeyboardMarkup:
    """کیبورد مدیریت ادمین‌ها."""
    buttons = []
    for admin in admins:
        name = admin.get("first_name") or admin.get("username") or str(admin["user_id"])
        buttons.append([
            ib(f"🗑 {name}", callback_data=f"rmadm:{admin['user_id']}", style="danger")
        ])
    buttons.append([ib("➕ افزودن ادمین", callback_data="add_admin")])
    buttons.append([ib("🔙 بازگشت", callback_data="st:back", style="danger")])
    return InlineKeyboardMarkup(buttons)

"""
Keyboard builders for Pop Scheduler Bot.
"""
from datetime import date
from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from .constants import MONTH_NAMES, MONTH_NAMES_SHORT, QUICK_HOURS


def main_menu(user_id: int, is_owner: bool = False) -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    keyboard = [
        [
            KeyboardButton(text="📅 زمان‌بندی جدید"),
            KeyboardButton(text="📋 پست‌های فعال"),
        ],
        [
            KeyboardButton(text="📊 تاریخچه"),
            KeyboardButton(text="⚙️ تنظیمات"),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Cancel keyboard for text input."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text="❌ لغو")]],
        resize_keyboard=True,
    )


# ── Source/Destination Channel Keyboards ────────────────────────────────────

def source_channels_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    """Source channels selection keyboard."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            InlineKeyboardButton(
                text=f"📥 {title}",
                callback_data=f"src:{ch['channel_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ لغو", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def dest_channels_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    """Destination channels selection keyboard."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            InlineKeyboardButton(
                text=f"📤 {title}",
                callback_data=f"dst:{ch['channel_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ لغو", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


# ── Date/Time Keyboards ─────────────────────────────────────────────────────

def datetime_keyboard(year: int, month: int, day: int, hour: int) -> InlineKeyboardMarkup:
    """
    Main datetime selection keyboard.
    Shows current selections with buttons to change each.
    """
    month_name = MONTH_NAMES.get(month, str(month))
    date_str = f"{day} {month_name} {year}"
    time_str = f"{hour:02d}:00"

    buttons = [
        [
            InlineKeyboardButton(
                text=f"🗓 {month_name} {year}",
                callback_data="dt:month"
            ),
            InlineKeyboardButton(
                text=f"📆 {day}",
                callback_data="dt:day"
            ),
            InlineKeyboardButton(
                text=f"🕐 {time_str}",
                callback_data="dt:hour"
            ),
        ],
        [
            InlineKeyboardButton(text="✅ ثبت", callback_data="dt:submit"),
        ],
        [
            InlineKeyboardButton(text="❌ لغو", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def months_keyboard(current_month: int) -> InlineKeyboardMarkup:
    """Months selection keyboard (3 per row)."""
    buttons = []
    row = []
    for m in range(1, 13):
        month_name = MONTH_NAMES_SHORT[m]
        # Checkmark for current month
        prefix = "✅ " if m == current_month else ""
        row.append(InlineKeyboardButton(
            text=f"{prefix}{month_name}",
            callback_data=f"m:{m}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="dt:back")])
    return InlineKeyboardMarkup(buttons)


def hours_keyboard(hours: list[int], current_hour: int = None) -> InlineKeyboardMarkup:
    """Hours selection keyboard (3 per row)."""
    buttons = []
    row = []
    for h in sorted(hours):
        prefix = "✅ " if h == current_hour else ""
        row.append(InlineKeyboardButton(
            text=f"{prefix}{h:02d}:00",
            callback_data=f"h:{h}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="dt:back")])
    return InlineKeyboardMarkup(buttons)


# ── Post List Keyboards ─────────────────────────────────────────────────────

def post_list_keyboard(posts: list[dict], page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Post list with action buttons."""
    buttons = []
    for post in posts:
        target = post.get("target_channel_title") or post["target_channel"]
        msg_count = len(post.get("message_ids", []))
        label = f"🆔{post['id']} — {target} — {post['schedule_date']} {post['schedule_time']} ({msg_count})"
        if len(label) > 60:
            label = label[:57] + "..."
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"post:{post['id']}")
        ])

    # Pagination
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"pg:posts:{page-1}"))
        nav.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton(text="▶️ بعدی", callback_data=f"pg:posts:{page+1}"))
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(buttons)


def post_detail_keyboard(post_id: int, status: str = "pending") -> InlineKeyboardMarkup:
    """Post detail action buttons."""
    buttons = []
    if status == "pending":
        buttons.append([
            InlineKeyboardButton(text="📅 ویرایش تاریخ", callback_data=f"edit_date:{post_id}"),
            InlineKeyboardButton(text="🕐 ویرایش ساعت", callback_data=f"edit_time:{post_id}"),
        ])
        buttons.append([
            InlineKeyboardButton(text="📢 تغییر مقصد", callback_data=f"edit_ch:{post_id}"),
        ])
        buttons.append([
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"del:{post_id}"),
            InlineKeyboardButton(text="❌ لغو پست", callback_data=f"cancel_post:{post_id}"),
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔄 ارسال مجدد", callback_data=f"resend:{post_id}"),
        ])

    buttons.append([
        InlineKeyboardButton(text="📋 بازگشت به لیست", callback_data="back_to_list"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(buttons)


def history_keyboard(posts: list[dict], page: int, total_pages: int) -> InlineKeyboardMarkup:
    """History list keyboard."""
    buttons = []
    for post in posts:
        target = post.get("target_channel_title") or post["target_channel"]
        status_icon = "✅" if post["status"] == "sent" else "❌"
        msg_count = len(post.get("message_ids", []))
        label = f"{status_icon} 🆔{post['id']} — {target} — {post['schedule_date']} ({msg_count})"
        if len(label) > 60:
            label = label[:57] + "..."
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"hpost:{post['id']}")
        ])

    # Pagination
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"pg:history:{page-1}"))
        nav.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton(text="▶️ بعدی", callback_data=f"pg:history:{page+1}"))
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(buttons)


# ── Settings Keyboards ──────────────────────────────────────────────────────

def settings_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    """Settings menu keyboard (only for owner)."""
    buttons = [
        [
            InlineKeyboardButton(text="📢 کانال‌ها", callback_data="st:channels"),
            InlineKeyboardButton(text="🕐 ساعت‌های پیش‌فرض", callback_data="st:hours"),
        ],
        [
            InlineKeyboardButton(text="👥 مدیران", callback_data="st:admins"),
        ],
        [
            InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def channels_type_keyboard() -> InlineKeyboardMarkup:
    """Channel type selection keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="📥 کانال‌های مبدأ", callback_data="st:source_channels"),
            InlineKeyboardButton(text="📤 کانال‌های مقصد", callback_data="st:dest_channels"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="st:back"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def source_channels_manage_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    """Source channels management keyboard."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            InlineKeyboardButton(text=f"🗑 {title}", callback_data=f"rmsrc:{ch['channel_id']}")
        ])
    buttons.append([
        InlineKeyboardButton(text="➕ افزودن کانال مبدأ", callback_data="add_source"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="st:channels"),
    ])
    return InlineKeyboardMarkup(buttons)


def dest_channels_manage_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    """Destination channels management keyboard."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            InlineKeyboardButton(text=f"🗑 {title}", callback_data=f"rmdst:{ch['channel_id']}")
        ])
    buttons.append([
        InlineKeyboardButton(text="➕ افزودن کانال مقصد", callback_data="add_dest"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="st:channels"),
    ])
    return InlineKeyboardMarkup(buttons)


def hours_manage_keyboard(hours: list[int]) -> InlineKeyboardMarkup:
    """Hours management keyboard."""
    buttons = []
    row = []
    for h in sorted(hours):
        row.append(
            InlineKeyboardButton(text=f"🗑 {h:02d}:00", callback_data=f"rmh:{h}")
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="➕ افزودن ساعت", callback_data="add_hour"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="st:back"),
    ])
    return InlineKeyboardMarkup(buttons)


def admins_manage_keyboard(admins: list[dict]) -> InlineKeyboardMarkup:
    """Admins management keyboard."""
    buttons = []
    for admin in admins:
        name = admin.get("first_name") or admin.get("username") or str(admin["user_id"])
        buttons.append([
            InlineKeyboardButton(text=f"🗑 {name}", callback_data=f"rmadm:{admin['user_id']}")
        ])
    buttons.append([
        InlineKeyboardButton(text="➕ افزودن ادمین", callback_data="add_admin"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="st:back"),
    ])
    return InlineKeyboardMarkup(buttons)

"""
Keyboard builders for Pop Scheduler Bot.
"""
from datetime import date, timedelta
from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from .utils import fmt_date


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


def back_to_menu_keyboard() -> ReplyKeyboardMarkup:
    """Back to main menu keyboard."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text="🏠 منوی اصلی")]],
        resize_keyboard=True,
    )


# ── Inline Keyboards ────────────────────────────────────────────────────────

def channel_selection_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    """Channel selection inline keyboard."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            InlineKeyboardButton(
                text=f"📢 {title}",
                callback_data=f"ch:{ch['channel_id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="❌ لغو", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(buttons)


def date_keyboard(tz_name: str = None) -> InlineKeyboardMarkup:
    """Date selection keyboard with today, tomorrow, day after + custom."""
    from .utils import now_tz
    today = now_tz(tz_name).date()

    buttons = [
        [
            InlineKeyboardButton(
                text=f"📌 امروز ({fmt_date(today)})",
                callback_data=f"d:{fmt_date(today)}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📌 فردا ({fmt_date(today + timedelta(days=1))})",
                callback_data=f"d:{fmt_date(today + timedelta(days=1))}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📌 پس‌فردا ({fmt_date(today + timedelta(days=2))})",
                callback_data=f"d:{fmt_date(today + timedelta(days=2))}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ انتخاب تاریخ دلخواه",
                callback_data="d:custom"
            )
        ],
        [
            InlineKeyboardButton(text="❌ لغو", callback_data="cancel")
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def time_keyboard(hours: list[int]) -> InlineKeyboardMarkup:
    """Time selection keyboard with preset hours."""
    buttons = []
    # Two hours per row
    row = []
    for h in sorted(hours):
        row.append(
            InlineKeyboardButton(
                text=f"🕐 {h:02d}:00",
                callback_data=f"t:{h:02d}:00"
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="✏️ ساعت دلخواه", callback_data="t:custom")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ لغو", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm/cancel keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="✅ تأیید", callback_data="confirm:yes"),
            InlineKeyboardButton(text="❌ لغو", callback_data="confirm:no"),
        ]
    ])


def post_list_keyboard(posts: list[dict], page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Post list with action buttons."""
    buttons = []
    for post in posts:
        channel = post.get("target_channel_title") or post["target_channel"]
        label = f"🆔{post['id']} — {channel} — {post['schedule_date']} {post['schedule_time']}"
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
            InlineKeyboardButton(text="📢 تغییر کانال", callback_data=f"edit_ch:{post_id}"),
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
        channel = post.get("target_channel_title") or post["target_channel"]
        status_icon = "✅" if post["status"] == "sent" else "❌"
        label = f"{status_icon} 🆔{post['id']} — {channel} — {post['schedule_date']}"
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


def settings_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    """Settings menu keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="📢 کانال‌ها", callback_data="st:channels"),
            InlineKeyboardButton(text="🕐 ساعت‌های پیش‌فرض", callback_data="st:hours"),
        ],
    ]
    if is_owner:
        buttons.append([
            InlineKeyboardButton(text="👥 مدیران", callback_data="st:admins"),
        ])
    buttons.append([
        InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(buttons)


def channels_manage_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    """Channel management keyboard."""
    buttons = []
    for ch in channels:
        title = ch.get("title") or ch.get("username") or ch["channel_id"]
        buttons.append([
            InlineKeyboardButton(text=f"🗑 {title}", callback_data=f"rmch:{ch['channel_id']}")
        ])
    buttons.append([
        InlineKeyboardButton(text="➕ افزودن کانال", callback_data="add_channel"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="st:back"),
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

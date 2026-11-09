"""
Constants, messages and conversation states for Pop Scheduler Bot.
"""
from telegram import InlineKeyboardButton

# ── Conversation States ─────────────────────────────────────────────────────
# Main flow
MAIN_MENU = 0
AWAITING_POST = 1
SELECT_CHANNEL = 2
SELECT_DATE = 3
SELECT_TIME = 4
CUSTOM_TIME = 5
CONFIRM_SCHEDULE = 6

# Post management
MANAGE_POSTS = 10
MANAGE_POST_DETAIL = 11
EDIT_POST_DATE = 12
EDIT_POST_TIME = 13
EDIT_CUSTOM_TIME = 14

# Settings
SETTINGS_MENU = 20
ADD_CHANNEL = 21
REMOVE_CHANNEL = 22
ADD_ADMIN = 23
REMOVE_ADMIN = 24
SET_DEFAULT_HOUR = 25
CUSTOM_HOUR_INPUT = 26

# History
VIEW_HISTORY = 30

# ── Quick hours ─────────────────────────────────────────────────────────────
QUICK_HOURS = [8, 11, 14, 17, 20, 23]

# ── Post Status ─────────────────────────────────────────────────────────────
STATUS_PENDING = "pending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

# ── Messages ────────────────────────────────────────────────────────────────
class Msg:
    WELCOME = (
        "سلام! 👋\n\n"
        "به ربات زمان‌بندی پست خوش آمدی.\n\n"
        "از منوی زیر یک گزینه انتخاب کن:"
    )

    # Schedule flow
    SEND_POST = (
        "📅 <b>زمان‌بندی پست جدید</b>\n\n"
        "پیامی که می‌خواهی زمان‌بندی کنی را ارسال کن.\n"
        "می‌تواند شامل متن، عکس، ویدیو، فایل یا ترکیبی از آنها باشد.\n\n"
        "برای لغو دکمه ❌ لغو را بزن."
    )

    POST_RECEIVED = "✅ پیام دریافت شد. حالا کانال مقصد را انتخاب کن:"

    SELECT_CHANNEL = "📢 کانال مقصد را انتخاب کن:"

    SELECT_DATE = (
        "📅 <b>تاریخ ارسال</b>\n\n"
        "تاریخ مورد نظر را به صورت میلادی وارد کن.\n\n"
        "فرمت: <code>YYYY-MM-DD</code>\n"
        "مثال: <code>2026-11-15</code>\n\n"
        "یا از دکمه‌های سریع استفاده کن:"
    )

    SELECT_TIME = (
        "🕐 <b>ساعت ارسال</b>\n\n"
        "ساعت مورد نظر را انتخاب کن یا تایپ کن.\n\n"
        "فرمت تایپ: <code>HH:MM</code> (مثال: <code>14:30</code>)"
    )

    CONFIRM_POST = (
        "✅ <b>تأیید زمان‌بندی</b>\n\n"
        "📢 کانال: <b>{channel}</b>\n"
        "📅 تاریخ: <b>{date}</b>\n"
        "🕐 ساعت: <b>{time}</b>\n\n"
        "آیا تأیید می‌کنی؟"
    )

    SCHEDULED_SUCCESS = (
        "✅ <b>پست با موفقیت زمان‌بندی شد!</b>\n\n"
        "📢 کانال: <b>{channel}</b>\n"
        "📅 تاریخ: <b>{date}</b>\n"
        "🕐 ساعت: <b>{time}</b>\n"
        "🆔 شناسه: <code>{post_id}</code>"
    )

    INVALID_DATE = "❌ تاریخ نامعتبر است. لطفاً به فرمت <code>YYYY-MM-DD</code> وارد کن.\nمثال: <code>2026-11-15</code>"

    INVALID_TIME = "❌ ساعت نامعتبر است. لطفاً به فرمت <code>HH:MM</code> وارد کن.\nمثال: <code>14:30</code>"

    DATE_IN_PAST = "❌ تاریخ در گذشته است. لطفاً تاریخ آینده وارد کن."

    # Quick dates
    TODAY = "📌 امروز"
    TOMORROW = "📌 فردا"
    DAY_AFTER = "📌 پس‌فردا"

    # Manage posts
    NO_SCHEDULED_POSTS = "📭 هیچ پست زمان‌بندی‌شده‌ای وجود ندارد."

    SCHEDULED_LIST = (
        "📋 <b>پست‌های زمان‌بندی‌شده</b>\n"
        "صفحه {page} از {total}\n\n"
        "{items}"
    )

    POST_DETAIL = (
        "📝 <b>جزئیات پست</b>\n\n"
        "🆔 شناسه: <code>{post_id}</code>\n"
        "📢 کانال: <b>{channel}</b>\n"
        "📅 تاریخ: <b>{date}</b>\n"
        "🕐 ساعت: <b>{time}</b>\n"
        "📊 وضعیت: {status}\n"
        "📄 نوع: {content_type}\n"
        "🕐 ثبت: {created_at}"
    )

    POST_DELETED = "🗑 پست با موفقیت حذف شد."

    POST_EDITED = "✅ پست با موفقیت ویرایش شد."

    POST_CANCELLED_MSG = "❌ پست لغو شد."

    POST_SENT_SUCCESS = "✅ پست با موفقیت به کانال ارسال شد!"

    POST_SENT_FAILED = "❌ ارسال پست ناموفق بود. لطفاً دوباره تلاش کن."

    # History
    NO_HISTORY = "📭 تاریخچه‌ای وجود ندارد."

    HISTORY_LIST = (
        "📊 <b>تاریخچه ارسال‌ها</b>\n"
        "صفحه {page} از {total}\n\n"
        "{items}"
    )

    # Settings
    SETTINGS_MENU_MSG = (
        "⚙️ <b>تنظیمات</b>\n\n"
        "از منوی زیر گزینه مورد نظر را انتخاب کن:"
    )

    CHANNELS_LIST = (
        "📢 <b>کانال‌های مجاز</b>\n\n"
        "{channels}\n\n"
        "برای افزودن کانال جدید، پیامی از کانال به ربات فوروارد کن."
    )

    CHANNEL_ADDED = "✅ کانال <b>{channel}</b> اضافه شد."

    CHANNEL_REMOVED = "🗑 کانال <b>{channel}</b> حذف شد."

    CHANNEL_ALREADY_EXISTS = "❌ این کانال قبلاً اضافه شده است."

    CHANNEL_NOT_FOUND = "❌ کانال پیدا نشد. مطمئن شو ربات ادمین کانال است."

    ADMINS_LIST = (
        "👥 <b>مدیران</b>\n\n"
        "{admins}\n\n"
        "آیدی عددی ادمین جدید را وارد کن:"
    )

    ADMIN_ADDED = "✅ ادمین <code>{admin_id}</code> اضافه شد."

    ADMIN_REMOVED = "🗑 ادمین <code>{admin_id}</code> حذف شد."

    ADMIN_ALREADY_EXISTS = "❌ این ادمین قبلاً اضافه شده است."

    ADMIN_IS_OWNER = "❌ مالک ربات نمی‌تواند حذف شود."

    DEFAULT_HOURS_MSG = (
        "🕐 <b>ساعت‌های پیش‌فرض</b>\n\n"
        "ساعت‌هایی که معمولاً پست می‌گذاری:\n"
        "{hours}\n\n"
        "می‌توانی ساعت جدید اضافه یا حذف کنی:"
    )

    HOUR_ADDED = "✅ ساعت <b>{hour}:00</b> اضافه شد."

    HOUR_REMOVED = "🗑 ساعت <b>{hour}:00</b> حذف شد."

    HOUR_ALREADY_EXISTS = "❌ این ساعت قبلاً اضافه شده است."

    INVALID_HOUR = "❌ ساعت نامعتبر است. عدد بین 0 تا 23 وارد کن."

    # General
    CANCELLED = "❌ لغو شد."

    ACCESS_DENIED = "❌ دسترسی غیرمجاز."

    ERROR_GENERIC = "⚠️ خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کن."

    NOT_CHANNEL_ADMIN = "❌ ربات باید ادمین کانال باشد تا بتواند پیام ارسال کند."

    BOT_NOT_IN_CHANNEL = "❌ ربات در این کانال عضو نیست."

# ── Status labels ───────────────────────────────────────────────────────────
STATUS_LABELS = {
    STATUS_PENDING: "⏳ در انتظار",
    STATUS_SENT: "✅ ارسال شده",
    STATUS_FAILED: "❌ ناموفق",
    STATUS_CANCELLED: "❌ لغو شده",
}

# ── Content type labels ─────────────────────────────────────────────────────
CONTENT_TYPE_LABELS = {
    "text": "📝 متنی",
    "photo": "📷 عکس",
    "video": "🎥 ویدیو",
    "document": "📄 فایل",
    "animation": "🎞 گیف",
    "audio": "🎵 صوتی",
    "voice": "🎤 پیام صوتی",
    "video_note": "📹 ویدیو مسیج",
    "sticker": "🏷 استیکر",
    "media_group": "🖼 چندرسانه‌ای",
}

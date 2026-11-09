"""
Constants, messages and conversation states for Pop Scheduler Bot.
"""

# ── Conversation States ─────────────────────────────────────────────────────
MAIN_MENU = 0

# Schedule flow (new)
SELECT_SOURCE_CHANNEL = 1
SELECT_MESSAGE_IDS = 2
SELECT_DATETIME = 3
INPUT_YEAR = 4
INPUT_DAY = 5
SELECT_TARGET_CHANNEL = 6
CONFIRM_SCHEDULE = 7

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

# ── Month names (Gregorian) ────────────────────────────────────────────────
MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

MONTH_NAMES_SHORT = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

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

    # ── Schedule flow (new) ─────────────────────────────────────────────────
    SELECT_SOURCE = (
        "📢 <b>کانال مبدأ</b>\n\n"
        "کانالی که می‌خواهی پیام‌ها از آن کپی شوند را انتخاب کن:"
    )

    ENTER_MESSAGE_IDS = (
        "📨 <b>آیدی پیام‌ها</b>\n\n"
        "آیدی پیام‌هایی که می‌خواهی کپی شوند را وارد کن.\n\n"
        "<b>فرمت‌های مجاز:</b>\n"
        "• تکی: <code>10</code>\n"
        "• بازه: <code>10-15</code> (از 10 تا 15)\n"
        "• چندتایی: <code>10,13,17</code>\n"
        "• ترکیبی: <code>10,13-15,17</code>\n\n"
        "برای لغو دکمه ❌ لغو را بزن."
    )

    NO_SOURCE_CHANNELS = (
        "❌ هیچ کانال مبدأ‌ای ثبت نشده.\n"
        "ابتدا از ⚙️ تنظیمات → 📢 کانال‌های مبدأ، کانال اضافه کن."
    )

    NO_DEST_CHANNELS = (
        "❌ هیچ کانال مقصدی ثبت نشده.\n"
        "ابتدا از ⚙️ تنظیمات → 📢 کانال‌های مقصد، کانال اضافه کن."
    )

    INVALID_MESSAGE_IDS = (
        "❌ فرمت آیدی نامعتبر است.\n\n"
        "<b>مثال‌های صحیح:</b>\n"
        "• <code>10</code>\n"
        "• <code>10-15</code>\n"
        "• <code>10,13,17</code>\n"
        "• <code>10,13-15,17</code>"
    )

    MESSAGE_IDS_CONFIRM = (
        "✅ <b>{count} پیام</b> انتخاب شد:\n"
        "<code>{ids_text}</code>\n\n"
        "📢 کانال مبدأ: <b>{source}</b>\n\n"
        "حالا تاریخ و ساعت ارسال را تنظیم کن:"
    )

    # ── Date/Time selection ─────────────────────────────────────────────────
    SELECT_DATETIME_MSG = (
        "📅 <b>تنظیم تاریخ و ساعت</b>\n\n"
        "📅 تاریخ: <b>{date}</b>\n"
        "🕐 ساعت: <b>{time}</b>\n\n"
        "روی هر دکمه کلیک کن تا تغییر دهی:"
    )

    ENTER_YEAR = (
        "📅 <b>سال</b>\n\n"
        "سال را وارد کن (مثال: <code>2026</code>):"
    )

    ENTER_DAY = (
        "📆 <b>روز</b>\n\n"
        "روز را وارد کن (مثال: <code>15</code>):"
    )

    SELECT_HOUR = (
        "🕐 <b>ساعت</b>\n\n"
        "ساعت ارسال را انتخاب کن:"
    )

    INVALID_YEAR = "❌ سال نامعتبر است. عدد ۴ رقمی وارد کن (مثال: <code>2026</code>)"
    INVALID_DAY = "❌ روز نامعتبر است. عدد بین 1 تا 31 وارد کن."

    SCHEDULE_SUMMARY = (
        "📋 <b>خلاصه زمان‌بندی</b>\n\n"
        "📢 مبدأ: <b>{source}</b>\n"
        "📨 پیام‌ها: <code>{ids}</code> ({count} پیام)\n"
        "📅 تاریخ: <b>{date}</b>\n"
        "🕐 ساعت: <b>{time}</b>\n\n"
        "حالا کانال مقصد را انتخاب کن:"
    )

    SCHEDULED_SUCCESS = (
        "✅ <b>پست با موفقیت زمان‌بندی شد!</b>\n\n"
        "📢 مبدأ: <b>{source}</b>\n"
        "📨 پیام‌ها: {count} عدد\n"
        "📢 مقصد: <b>{target}</b>\n"
        "📅 تاریخ: <b>{date}</b>\n"
        "🕐 ساعت: <b>{time}</b>\n"
        "🆔 شناسه: <code>{post_id}</code>"
    )

    # ── Manage posts ────────────────────────────────────────────────────────
    NO_SCHEDULED_POSTS = "📭 هیچ پست زمان‌بندی‌شده‌ای وجود ندارد."

    SCHEDULED_LIST = (
        "📋 <b>پست‌های زمان‌بندی‌شده</b>\n"
        "صفحه {page} از {total}\n\n"
        "{items}"
    )

    POST_DETAIL = (
        "📝 <b>جزئیات پست</b>\n\n"
        "🆔 شناسه: <code>{post_id}</code>\n"
        "📢 مبدأ: <b>{source}</b>\n"
        "📨 پیام‌ها: <code>{message_ids}</code> ({count} عدد)\n"
        "📢 مقصد: <b>{target}</b>\n"
        "📅 تاریخ: <b>{date}</b>\n"
        "🕐 ساعت: <b>{time}</b>\n"
        "📊 وضعیت: {status}\n"
        "🕐 ثبت: {created_at}"
    )

    POST_DELETED = "🗑 پست با موفقیت حذف شد."
    POST_EDITED = "✅ پست با موفقیت ویرایش شد."
    POST_CANCELLED_MSG = "❌ پست لغو شد."

    # ── History ─────────────────────────────────────────────────────────────
    NO_HISTORY = "📭 تاریخچه‌ای وجود ندارد."

    HISTORY_LIST = (
        "📊 <b>تاریخچه ارسال‌ها</b>\n"
        "صفحه {page} از {total}\n\n"
        "{items}"
    )

    # ── Settings ────────────────────────────────────────────────────────────
    SETTINGS_MENU_MSG = (
        "⚙️ <b>تنظیمات</b>\n\n"
        "از منوی زیر گزینه مورد نظر را انتخاب کن:"
    )

    CHANNELS_MENU = (
        "📢 <b>کانال‌ها</b>\n\n"
        "نوع کانال را انتخاب کن:"
    )

    SOURCE_CHANNELS_LIST = (
        "📥 <b>کانال‌های مبدأ</b>\n\n"
        "{channels}\n\n"
        "کانال مبدأ نیازی به عضویت ربات ندارد."
    )

    DEST_CHANNELS_LIST = (
        "📤 <b>کانال‌های مقصد</b>\n\n"
        "{channels}\n\n"
        "⚠️ ربات باید در کانال مقصد عضو و ادمین باشد."
    )

    ENTER_CHANNEL_ID = (
        "📢 آیدی عددی کانال را وارد کن.\n\n"
        "مثال: <code>-1001234567890</code>\n\n"
        "💡 نکته: آیدی عددی کانال با <code>-100</code> شروع می‌شود."
    )

    CHANNEL_ADDED = "✅ کانال <b>{channel}</b> اضافه شد."
    CHANNEL_REMOVED = "🗑 کانال <b>{channel}</b> حذف شد."
    CHANNEL_ALREADY_EXISTS = "❌ این کانال قبلاً اضافه شده است."

    BOT_NOT_IN_CHANNEL = (
        "❌ ربات در این کانال عضو نیست یا ادمین نیست.\n"
        "برای کانال مقصد، ربات باید حتماً عضو و ادمین باشد."
    )

    ADMINS_LIST = (
        "👥 <b>مدیران</b>\n\n"
        "{admins}\n\n"
        "آیدی عددی ادمین جدید را وارد کن:"
    )

    ADMIN_ADDED = "✅ ادمین <code>{admin_id}</code> اضافه شد."
    ADMIN_REMOVED = "🗑 ادمین <code>{admin_id}</code> حذف شد."
    ADMIN_ALREADY_EXISTS = "❌ این ادمین قبلاً اضافه شده است."
    ADMIN_IS_OWNER = "❌ مالک ربات به صورت خودکار دسترسی کامل دارد."

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

    # ── General ─────────────────────────────────────────────────────────────
    CANCELLED = "❌ لغو شد."
    ACCESS_DENIED = "❌ دسترسی غیرمجاز.\nفقط مالک ربات می‌تواند از تنظیمات استفاده کند."
    ERROR_GENERIC = "⚠️ خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کن."

# ── Status labels ───────────────────────────────────────────────────────────
STATUS_LABELS = {
    STATUS_PENDING: "⏳ در انتظار",
    STATUS_SENT: "✅ ارسال شده",
    STATUS_FAILED: "❌ ناموفق",
    STATUS_CANCELLED: "❌ لغو شده",
}

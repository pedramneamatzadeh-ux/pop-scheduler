"""
ثابت‌ها، حالت‌های ConversationHandler و پیام‌ها.
"""

# ============================================================================
# حالت‌های ConversationHandler
# ============================================================================

# فلوی اصلی زمان‌بندی
(
    SELECT_SOURCE_CHANNEL,  # انتخاب کانال مبدأ
    SELECT_MESSAGE_IDS,     # وارد کردن آیدی پیام‌ها
    SELECT_DATETIME,        # انتخاب تاریخ و ساعت (دکمه‌ای)
    INPUT_YEAR,             # ورودی متنی سال
    INPUT_DAY,              # ورودی متنی روز
    INPUT_HOUR,             # ورودی متنی ساعت (HH:MM)
    SELECT_TARGET_CHANNEL,  # انتخاب کانال مقصد
    CONFIRM_SCHEDULE,       # تأیید نهایی
) = range(8)

# مدیریت پست‌ها
(
    MANAGE_POSTS,           # لیست پست‌ها
    MANAGE_POST_DETAIL,     # جزئیات پست
    EDIT_POST_DATE,         # ویرایش تاریخ
    EDIT_POST_TIME,         # ویرایش ساعت
    EDIT_CUSTOM_TIME,       # ورودی متنی ساعت
) = range(8, 13)

# تنظیمات (فقط مالک)
(
    SETTINGS_MENU,          # منوی اصلی تنظیمات
    ADD_CHANNEL,            # افزودن کانال
    REMOVE_CHANNEL,         # حذف کانال
    ADD_ADMIN,              # افزودن ادمین
    REMOVE_ADMIN,           # حذف ادمین
    CUSTOM_HOUR_INPUT,      # افزودن ساعت سفارشی
) = range(13, 19)

# تاریخچه
VIEW_HISTORY = 19

# منوی اصلی
MAIN_MENU = 20

# ============================================================================
# نام ماه‌های میلادی
# ============================================================================

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

MONTH_NAMES_SHORT = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

# ============================================================================
# وضعیت پست‌ها
# ============================================================================

STATUS_PENDING = "pending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

STATUS_LABELS = {
    STATUS_PENDING: "⏳ در انتظار",
    STATUS_SENT: "✅ ارسال شده",
    STATUS_FAILED: "❌ ناموفق",
    STATUS_CANCELLED: "❌ لغو شده",
}

# ============================================================================
# پیام‌ها
# ============================================================================

class Msg:
    """تمام پیام‌های ربات."""
    
    # عمومی
    WELCOME = (
        "سلام! 👋\n\n"
        "به ربات زمان‌بندی پست خوش آمدی.\n\n"
        "از منوی زیر یک گزینه انتخاب کن:"
    )
    
    ACCESS_DENIED = "❌ دسترسی غیرمجاز.\nفقط مالک ربات می‌تواند از تنظیمات استفاده کند."
    CANCELLED = "❌ لغو شد."
    ERROR_GENERIC = "⚠️ خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کن."
    
    # زمان‌بندی
    SELECT_SOURCE = (
        "📢 <b>کانال مبدأ</b>\n\n"
        "کانالی که می‌خواهی پیام‌ها از آن کپی شوند را انتخاب کن:"
    )
    
    NO_SOURCE_CHANNELS = (
        "❌ هیچ کانال مبدأ‌ای ثبت نشده.\n"
        "ابتدا از ⚙️ تنظیمات → 📢 کانال‌های مبدأ، کانال اضافه کن."
    )
    
    NO_DEST_CHANNELS = (
        "❌ هیچ کانال مقصدی ثبت نشده.\n"
        "ابتدا از ⚙️ تنظیمات → 📢 کانال‌های مقصد، کانال اضافه کن."
    )
    
    ENTER_MESSAGE_IDS = (
        "📨 <b>آیدی پیام‌ها</b>\n\n"
        "آیدی پیام‌هایی که می‌خواهی کپی شوند را وارد کن.\n\n"
        "<b>فرمت‌های مجاز:</b>\n"
        "• تکی: <code>10</code>\n"
        "• بازه: <code>10-15</code> (از 10 تا 15)\n"
        "• چندتایی: <code>10,13,17</code>\n"
        "• ترکیبی: <code>10,13-15,17</code>"
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
    
    SELECT_DATETIME_MSG = (
        "📅 <b>تنظیم تاریخ و ساعت</b>\n\n"
        "📅 تاریخ: <b>{date}</b>\n"
        "🕐 ساعت: <b>{time}</b>\n\n"
        "روی هر دکمه کلیک کن تا تغییر دهی:"
    )
    
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
    
    # مدیریت پست‌ها
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
    
    # تاریخچه
    NO_HISTORY = "📭 تاریخچه‌ای وجود ندارد."
    
    HISTORY_LIST = (
        "📊 <b>تاریخچه ارسال‌ها</b>\n"
        "صفحه {page} از {total}\n\n"
        "{items}"
    )
    
    # تنظیمات
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
    INVALID_HOUR = "❌ ساعت نامعتبر است. لطفاً به فرمت <code>HH:MM</code> وارد کن (مثال: <code>14:30</code>)."

// ============================================================================
// Constants & Messages
// ============================================================================

// وضعیت‌های پست
export const STATUS_PENDING = 'pending';
export const STATUS_SENT = 'sent';
export const STATUS_FAILED = 'failed';
export const STATUS_DISABLED = 'disabled';

export const STATUS_LABELS = {
  pending:  '⏳ در انتظار',
  sent:     '✅ ارسال شده',
  failed:   '❌ ناموفق',
  disabled: '⏸ غیرفعال',
};

// نام ماه‌های میلادی
export const MONTH_NAMES = {
  1: 'January', 2: 'February', 3: 'March', 4: 'April',
  5: 'May', 6: 'June', 7: 'July', 8: 'August',
  9: 'September', 10: 'October', 11: 'November', 12: 'December',
};

export const MONTH_NAMES_SHORT = {
  1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
  5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
  9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec',
};

// Conversation States
export const STATES = {
  NONE: 'none',
  SELECT_SOURCE: 'select_source',
  INPUT_IDS: 'input_ids',
  SELECT_DATETIME: 'select_datetime',
  INPUT_YEAR: 'input_year',
  INPUT_DAY: 'input_day',
  INPUT_HOUR: 'input_hour',
  SELECT_TARGET: 'select_target',
  MANAGE_POSTS: 'manage_posts',
  POST_DETAIL: 'post_detail',
  EDIT_DATE: 'edit_date',
  EDIT_TIME: 'edit_time',
  EDIT_CUSTOM_TIME: 'edit_custom_time',
  SETTINGS_MENU: 'settings_menu',
  ADD_CHANNEL: 'add_channel',
  ADD_ADMIN: 'add_admin',
  CUSTOM_HOUR_INPUT: 'custom_hour_input',
  VIEW_HISTORY: 'view_history',
};

// پیام‌ها
export const MSG = {
  WELCOME: (name, isAdmin) =>
    `سلام <b>${name}</b>! 👋\n\n` +
    `به ربات زمان‌بندی پست خوش آمدی.\n\n` +
    `از دکمه‌های زیر استفاده کن:` +
    (isAdmin ? '\n(شما دسترسی مدیریتی دارید)' : ''),

  SELECT_SOURCE: '📥 <b>انتخاب کانال مبدأ</b>\n\nاز کدام کانال کپی شود؟',

  NO_SOURCE_CHANNELS:
    '⚠️ هیچ کانال مبدأ‌ای تعریف نشده.\n\n' +
    'از ⚙️ تنظیمات → 📢 کانال‌ها → 📥 کانال‌های مبدأ یک کانال اضافه کن.',

  ENTER_MESSAGE_IDS:
    '📨 <b>آیدی پیام‌ها</b>\n\n' +
    'آیدی پیام‌هایی که می‌خواهی کپی شوند را وارد کن.\n\n' +
    '<b>فرمت‌های مجاز:</b>\n' +
    '• تکی: <code>10</code>\n' +
    '• بازه: <code>10-15</code> (از 10 تا 15)\n' +
    '• چندتایی: <code>10,13,17</code>\n' +
    '• ترکیبی: <code>10,13-15,17</code>',

  INVALID_MESSAGE_IDS:
    '❌ آیدی‌های نامعتبر.\n\n' +
    'لطفاً با فرمت صحیح وارد کن.\n' +
    'مثال: <code>10</code> یا <code>10-15</code> یا <code>10,13,17</code>',

  MESSAGE_IDS_CONFIRM: ({ count, idsText, source }) =>
    `✅ <b>${count}</b> پیام انتخاب شد:\n` +
    `📥 منبع: ${source}\n` +
    `📋 آیدی‌ها: <code>${idsText}</code>\n\n` +
    `حالا تاریخ و ساعت را مشخص کن:`,

  SELECT_DATETIME_MSG: ({ date, time }) =>
    `📅 <b>انتخاب تاریخ و ساعت</b>\n\n` +
    `📅 تاریخ: <b>${date}</b>\n` +
    `🕐 ساعت: <b>${time}</b>\n\n` +
    `روی هر دکمه کلیک کن تا تغییر دهی:`,

  SCHEDULE_SUMMARY: ({ source, ids, count, date, time }) =>
    `✅ <b>خلاصه زمان‌بندی</b>\n\n` +
    `📥 منبع: ${source}\n` +
    `📋 پیام‌ها: <code>${ids}</code> (${count} عدد)\n` +
    `📅 تاریخ: <b>${date}</b>\n` +
    `🕐 ساعت: <b>${time}</b>\n\n` +
    `📤 کانال مقصد را انتخاب کن:`,

  NO_DEST_CHANNELS:
    '⚠️ هیچ کانال مقصدی تعریف نشده.\n\n' +
    'از ⚙️ تنظیمات → 📢 کانال‌ها → 📤 کانال‌های مقصد یک کانال اضافه کن.',

  SCHEDULED_SUCCESS: ({ source, count, target, date, time, postId }) =>
    `✅ <b>زمان‌بندی با موفقیت ثبت شد!</b>\n\n` +
    `🆔 شماره: <code>${postId}</code>\n` +
    `📥 منبع: ${source}\n` +
    `📤 مقصد: ${target}\n` +
    `📨 تعداد: ${count} پیام\n` +
    `📅 ${date} ساعت ${time}`,

  CANCELLED: '❌ عملیات لغو شد.',

  NO_SCHEDULED_POSTS:
    '📭 هیچ پست فعالی وجود ندارد.\n\n' +
    'از 📅 زمان‌بندی جدید یک پست ثبت کن.',

  SCHEDULED_LIST: ({ page, total, items }) =>
    `📋 <b>پست‌های فعال</b>\n` +
    `صفحه ${page} از ${total}\n\n${items}`,

  POST_DETAIL: ({ postId, source, messageIds, count, target, date, time, status, createdAt }) =>
    `📋 <b>جزئیات پست #${postId}</b>\n\n` +
    `📥 مبدأ: ${source}\n` +
    `📨 آیدی‌ها: <code>${messageIds}</code> (${count} عدد)\n` +
    `📤 مقصد: ${target}\n` +
    `📅 تاریخ: ${date}\n` +
    `🕐 ساعت: ${time}\n` +
    `📊 وضعیت: ${status}\n` +
    `🕐 ثبت: ${createdAt}`,

  POST_DELETED: '🗑 پست با موفقیت حذف کامل شد.',
  POST_DISABLED_MSG: '⏸ پست غیرفعال شد.\n(هر زمان می‌توانید آن را مجدداً فعال کنید.)',
  POST_ENABLED_MSG: '▶️ پست فعال شد.\n(در زمان مقرر ارسال خواهد شد.)',
  POST_EDITED: '✅ پست با موفقیت ویرایش شد.',

  ACCESS_DENIED: '⛔️ دسترسی غیرمجاز.',

  NO_HISTORY: '📭 تاریخچه‌ای وجود ندارد.',

  HISTORY_LIST: ({ page, total, items }) =>
    `📊 <b>تاریخچه ارسال‌ها</b>\n` +
    `صفحه ${page} از ${total}\n\n${items}`,

  SETTINGS_MENU_MSG: (isOwner) =>
    `⚙️ <b>تنظیمات</b>\n\n` +
    (isOwner
      ? 'شما دسترسی کامل به تنظیمات دارید.'
      : 'فقط بخش‌های مجاز برای شما نمایش داده می‌شود.'),

  CHANNELS_MENU:
    '📢 <b>مدیریت کانال‌ها</b>\n\nنوع کانال را انتخاب کن:',

  CHANNEL_ADDED: (title) => `✅ کانال <b>${title}</b> اضافه شد.`,
  CHANNEL_REMOVED: (title) => `🗑 کانال <b>${title}</b> حذف شد.`,

  ADMIN_ADDED: (name) => `✅ <b>${name}</b> به عنوان مدیر اضافه شد.`,
  ADMIN_REMOVED: (name) => `🗑 <b>${name}</b> از لیست مدیران حذف شد.`,

  HOUR_ADDED: (hour) => `✅ ساعت <code>${hour}:00</code> اضافه شد.`,
  HOUR_REMOVED: (hour) => `🗑 ساعت <code>${hour}:00</code> حذف شد.`,

  ENTER_CHANNEL_ID:
    '📢 آیدی کانال را وارد کن.\n\n' +
    'فرمت: <code>@channelname</code> یا <code>-100xxxxxxxxxx</code>\n\n' +
    'برای لغو ❌ را بزن.',

  ENTER_ADMIN_ID:
    '👤 آیدی عددی کاربر را وارد کن.\n\n' +
    'مثال: <code>123456789</code>\n\n' +
    'برای لغو ❌ را بزن.',

  ENTER_HOUR:
    '🕐 ساعت جدید را وارد کن (0 تا 23).\n\n' +
    'مثال: <code>15</code>\n\n' +
    'برای لغو ❌ را بزن.',

  INVALID_INPUT: '❌ ورودی نامعتبر. دوباره تلاش کن.',
};

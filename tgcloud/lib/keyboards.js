// ============================================================================
// Keyboard Builders
// ============================================================================
import { MONTH_NAMES, MONTH_NAMES_SHORT } from './constants.js';
import { getMonthDays } from './utils.js';
import { OWNER_ID } from './config.js';

// ── منوی اصلی (ReplyKeyboard) ────────────────────────────────────────────
export function mainMenuKeyboard(isOwner) {
  return {
    keyboard: [
      [{ text: '📅 زمان‌بندی جدید' }, { text: '📋 پست‌های فعال' }],
      [{ text: '📊 تاریخچه' }, { text: '⚙️ تنظیمات' }],
    ],
    resize_keyboard: true,
  };
}

// ── کیبورد لغو inline ────────────────────────────────────────────────────
export function inlineCancelKeyboard() {
  return {
    inline_keyboard: [
      [{ text: '❌ لغو', callback_data: 'cancel' }],
    ],
  };
}

// ── کیبورد انتخاب کانال مبدأ ────────────────────────────────────────────
export function sourceChannelsKeyboard(channels) {
  const buttons = channels.map(ch => [
    { text: `📥 ${ch.title || ch.username || ch.channelId}`, callback_data: `src:${ch.channelId}` }
  ]);
  buttons.push([{ text: '❌ لغو', callback_data: 'cancel' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد انتخاب کانال مقصد ────────────────────────────────────────────
export function destChannelsKeyboard(channels) {
  const buttons = channels.map(ch => [
    { text: `📤 ${ch.title || ch.username || ch.channelId}`, callback_data: `dst:${ch.channelId}` }
  ]);
  buttons.push([{ text: '❌ لغو', callback_data: 'cancel' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد انتخاب تاریخ و ساعت ──────────────────────────────────────────
export function datetimeKeyboard(year, month, day, hour, minute = 0) {
  const monthName = MONTH_NAMES[month] || String(month);
  const maxDay = getMonthDays(year, month);
  const timeStr = minute > 0 ? `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}` : `${String(hour).padStart(2, '0')}:00`;

  return {
    inline_keyboard: [
      [
        { text: `🗓 ${monthName}`, callback_data: 'dt:month' },
        { text: `📅 ${year}`, callback_data: 'dt:year' },
      ],
      [
        { text: `📆 ${day} (از 1 تا ${maxDay})`, callback_data: 'dt:day' },
      ],
      [
        { text: `🕐 ${timeStr}`, callback_data: 'dt:hour' },
      ],
      [
        { text: '✅ ثبت', callback_data: 'dt:submit' },
      ],
      [
        { text: '❌ لغو', callback_data: 'cancel' },
      ],
    ],
  };
}

// ── کیبورد انتخاب ماه ───────────────────────────────────────────────────
export function monthsKeyboard(currentMonth) {
  const buttons = [];
  let row = [];
  for (let m = 1; m <= 12; m++) {
    const mark = m === currentMonth ? '✅ ' : '';
    row.push({ text: `${mark}${MONTH_NAMES_SHORT[m]}`, callback_data: `m:${m}` });
    if (row.length === 3) {
      buttons.push(row);
      row = [];
    }
  }
  if (row.length > 0) buttons.push(row);
  buttons.push([{ text: '🔙 بازگشت', callback_data: 'dt:back' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد انتخاب ساعت ──────────────────────────────────────────────────
export function hoursKeyboard(hours, currentHour) {
  const buttons = [];
  let row = [];
  const sorted = [...hours].sort((a, b) => a - b);

  for (const h of sorted) {
    const mark = h === currentHour ? '✅ ' : '';
    row.push({ text: `${mark}${String(h).padStart(2, '0')}:00`, callback_data: `h:${h}` });
    if (row.length === 3) {
      buttons.push(row);
      row = [];
    }
  }
  if (row.length > 0) buttons.push(row);
  buttons.push([
    { text: '✏️ ساعت دلخواه', callback_data: 'h:custom' },
    { text: '🔙 بازگشت', callback_data: 'dt:back' },
  ]);
  return { inline_keyboard: buttons };
}

// ── کیبورد لیست پست‌ها ──────────────────────────────────────────────────
export function postListKeyboard(posts, page, totalPages) {
  const buttons = posts.map(post => {
    const target = post.targetChannelTitle || post.targetChannel;
    const msgCount = (JSON.parse(post.messageIds || '[]')).length;
    let label = `🆔${post.id} — ${target} — ${post.scheduleDate} ${post.scheduleTime} (${msgCount})`;
    if (label.length > 60) label = label.slice(0, 57) + '...';
    return [{ text: label, callback_data: `post:${post.id}` }];
  });

  // صفحه‌بندی
  if (totalPages > 1) {
    const nav = [];
    if (page > 0) nav.push({ text: '◀️ قبلی', callback_data: `pg:posts:${page - 1}` });
    nav.push({ text: `📄 ${page + 1}/${totalPages}`, callback_data: 'noop' });
    if (page < totalPages - 1) nav.push({ text: '▶️ بعدی', callback_data: `pg:posts:${page + 1}` });
    buttons.push(nav);
  }

  buttons.push([{ text: '🏠 منوی اصلی', callback_data: 'main_menu' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد جزئیات پست ───────────────────────────────────────────────────
export function postDetailKeyboard(postId, status) {
  const buttons = [];

  if (status === 'pending') {
    buttons.push([
      { text: '📅 ویرایش تاریخ', callback_data: `edit_date:${postId}` },
      { text: '🕐 ویرایش ساعت', callback_data: `edit_time:${postId}` },
    ]);
    buttons.push([
      { text: '📢 تغییر مقصد', callback_data: `edit_ch:${postId}` },
    ]);
    buttons.push([
      { text: '🗑 حذف کامل', callback_data: `del:${postId}` },
      { text: '⏸ غیرفعال کردن', callback_data: `disable_post:${postId}` },
    ]);
  } else if (status === 'disabled') {
    buttons.push([
      { text: '▶️ فعال کردن مجدد', callback_data: `enable_post:${postId}` },
    ]);
    buttons.push([
      { text: '🗑 حذف کامل', callback_data: `del:${postId}` },
    ]);
  }

  buttons.push([{ text: '📋 بازگشت به لیست', callback_data: 'back_to_list' }]);
  buttons.push([{ text: '🏠 منوی اصلی', callback_data: 'main_menu' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد تاریخچه ─────────────────────────────────────────────────────
export function historyKeyboard(posts, page, totalPages) {
  const buttons = posts.map(post => {
    const target = post.targetChannelTitle || post.targetChannel;
    const statusIcon = post.status === 'sent' ? '✅' : '❌';
    const msgCount = (JSON.parse(post.messageIds || '[]')).length;
    let label = `${statusIcon} 🆔${post.id} — ${target} — ${post.scheduleDate} (${msgCount})`;
    if (label.length > 60) label = label.slice(0, 57) + '...';
    return [{ text: label, callback_data: `hpost:${post.id}` }];
  });

  if (totalPages > 1) {
    const nav = [];
    if (page > 0) nav.push({ text: '◀️ قبلی', callback_data: `pg:history:${page - 1}` });
    nav.push({ text: `📄 ${page + 1}/${totalPages}`, callback_data: 'noop' });
    if (page < totalPages - 1) nav.push({ text: '▶️ بعدی', callback_data: `pg:history:${page + 1}` });
    buttons.push(nav);
  }

  buttons.push([{ text: '🏠 منوی اصلی', callback_data: 'main_menu' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد تنظیمات ─────────────────────────────────────────────────────
export function settingsKeyboard(isOwner) {
  const buttons = [];
  if (isOwner) {
    buttons.push([
      { text: '📢 کانال‌ها', callback_data: 'st:channels' },
      { text: '🕐 ساعت‌های پیش‌فرض', callback_data: 'st:hours' },
    ]);
    buttons.push([
      { text: '👥 مدیران', callback_data: 'st:admins' },
    ]);
  } else {
    buttons.push([
      { text: '📢 کانال‌ها', callback_data: 'st:channels' },
    ]);
  }
  buttons.push([{ text: '🏠 منوی اصلی', callback_data: 'main_menu' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد نوع کانال ───────────────────────────────────────────────────
export function channelsTypeKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: '📥 کانال‌های مبدأ', callback_data: 'st:source_channels' },
        { text: '📤 کانال‌های مقصد', callback_data: 'st:dest_channels' },
      ],
      [
        { text: '🔙 بازگشت', callback_data: 'st:back' },
      ],
    ],
  };
}

// ── کیبورد مدیریت کانال‌ها ─────────────────────────────────────────────
export function channelsManageKeyboard(channels, type) {
  const prefix = type === 'source' ? 'rmsrc' : 'rmdst';
  const addData = type === 'source' ? 'add_source' : 'add_dest';
  const addLabel = type === 'source' ? '➕ افزودن کانال مبدأ' : '➕ افزودن کانال مقصد';

  const buttons = channels.map(ch => [
    { text: `🗑 ${ch.title || ch.username || ch.channelId}`, callback_data: `${prefix}:${ch.channelId}` }
  ]);
  buttons.push([{ text: addLabel, callback_data: addData }]);
  buttons.push([{ text: '🔙 بازگشت', callback_data: 'st:channels' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد مدیریت ساعت‌ها ──────────────────────────────────────────────
export function hoursManageKeyboard(hours) {
  const buttons = [];
  let row = [];
  const sorted = [...hours].sort((a, b) => a - b);

  for (const h of sorted) {
    row.push({ text: `🗑 ${String(h).padStart(2, '0')}:00`, callback_data: `rmh:${h}` });
    if (row.length === 2) {
      buttons.push(row);
      row = [];
    }
  }
  if (row.length > 0) buttons.push(row);
  buttons.push([{ text: '➕ افزودن ساعت', callback_data: 'add_hour' }]);
  buttons.push([{ text: '🔙 بازگشت', callback_data: 'st:back' }]);
  return { inline_keyboard: buttons };
}

// ── کیبورد مدیریت ادمین‌ها ─────────────────────────────────────────────
export function adminsManageKeyboard(adminList) {
  const buttons = adminList.map(admin => {
    const name = admin.firstName || admin.username || String(admin.userId);
    return [{ text: `🗑 ${name}`, callback_data: `rmadm:${admin.userId}` }];
  });
  buttons.push([{ text: '➕ افزودن ادمین', callback_data: 'add_admin' }]);
  buttons.push([{ text: '🔙 بازگشت', callback_data: 'st:back' }]);
  return { inline_keyboard: buttons };
}

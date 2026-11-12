// ============================================================================
// Utility Functions
// ============================================================================
import { MONTH_NAMES } from './constants.js';

// ── تبدیل اعداد فارسی/عربی به انگلیسی ──────────────────────────────────────
const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩';
const EN_DIGITS = '0123456789';

export function normalizeDigits(text) {
  if (!text) return '';
  let result = text;
  for (let i = 0; i < 10; i++) {
    result = result.split(FA_DIGITS[i]).join(EN_DIGITS[i]);
    result = result.split(AR_DIGITS[i]).join(EN_DIGITS[i]);
  }
  return result;
}

// ── تجزیه آیدی پیام‌ها ────────────────────────────────────────────────────
export function parseMessageIds(text) {
  if (!text) return null;
  const normalized = normalizeDigits(text).replace(/،/g, ',');
  const ids = new Set();

  const parts = normalized.split(',').map(s => s.trim()).filter(Boolean);

  for (const part of parts) {
    if (part.includes('-')) {
      const [start, end] = part.split('-').map(Number);
      if (isNaN(start) || isNaN(end) || start < 1 || start > end) return null;
      for (let i = start; i <= end; i++) ids.add(i);
    } else {
      const num = Number(part);
      if (isNaN(num) || num < 1) return null;
      ids.add(num);
    }
  }

  const result = [...ids].sort((a, b) => a - b);
  return result.length > 0 ? result : null;
}

// ── نمایش آیدی پیام‌ها ────────────────────────────────────────────────────
export function formatMessageIds(ids) {
  if (!ids || ids.length === 0) return '';
  if (ids.length === 1) return String(ids[0]);
  return ids.join(', ');
}

// ── اعتبارسنجی ساعت ──────────────────────────────────────────────────────
export function validateHourInput(text) {
  const normalized = normalizeDigits(text).trim();
  if (!normalized) return { valid: false };

  // فرمت HH:MM
  if (normalized.includes(':')) {
    const [h, m] = normalized.split(':').map(Number);
    if (isNaN(h) || isNaN(m) || h < 0 || h > 23 || m < 0 || m > 59) {
      return { valid: false };
    }
    return { valid: true, hour: h, minute: m };
  }

  // فقط ساعت
  const hour = Number(normalized);
  if (isNaN(hour) || hour < 0 || hour > 23) return { valid: false };
  return { valid: true, hour, minute: 0 };
}

// ── تعداد روزهای ماه ─────────────────────────────────────────────────────
export function getMonthDays(year, month) {
  return new Date(year, month, 0).getDate();
}

// ── تبدیل به timestamp ──────────────────────────────────────────────────
// ماه و روز 1-based، timezone تهران
export function toTimestamp(year, month, day, hour, minute = 0) {
  // ساخت Date در UTC و تنظیم به timezone تهران
  // Tehran is UTC+3:30
  const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}T${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00+03:30`;
  return new Date(dateStr).getTime() / 1000;
}

// ── زمان فعلی تهران ─────────────────────────────────────────────────────
export function nowTehran() {
  return new Date();
}

// ── صفحه‌بندی ──────────────────────────────────────────────────────────
export function paginate(items, page, perPage = 5) {
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const safePage = Math.max(0, Math.min(page, totalPages - 1));
  const start = safePage * perPage;
  const end = start + perPage;
  return {
    pageItems: items.slice(start, end),
    totalPages,
    page: safePage,
  };
}

// ── فرمت نمایش پست ─────────────────────────────────────────────────────
export function formatScheduleDisplay(post) {
  const ids = JSON.parse(post.messageIds || '[]');
  const idStr = ids.length > 3 ? `${ids.slice(0, 3).join(',')}...` : ids.join(',');
  return (
    `🆔 <code>${post.id}</code> — ${post.targetChannelTitle || post.targetChannel}\n` +
    `   📅 ${post.scheduleDate} ${post.scheduleTime} | 📨 ${ids.length} پیام`
  );
}

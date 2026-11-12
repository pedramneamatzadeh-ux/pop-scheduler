// ============================================================================
// Schedule Flow — handles the post scheduling conversation
// ============================================================================
import { api } from 'sdk';
import { STATES, MSG, MONTH_NAMES } from './constants.js';
import { getChannels, getChannel, addPost, getDefaultHours } from './db.js';
import { CHANNEL_SOURCE, CHANNEL_DESTINATION } from './config.js';
import {
  sourceChannelsKeyboard, destChannelsKeyboard,
  datetimeKeyboard, monthsKeyboard, hoursKeyboard,
  inlineCancelKeyboard, mainMenuKeyboard,
} from './keyboards.js';
import {
  parseMessageIds, formatMessageIds, toTimestamp,
  nowTehran, getMonthDays, validateHourInput,
} from './utils.js';
import { getSession, setSession, clearSession } from './session.js';
import { isOwner } from './auth.js';

// ── Start Schedule ──────────────────────────────────────────────────────

export async function startSchedule(message, session) {
  const sourceChannels = getChannels(CHANNEL_SOURCE);

  if (sourceChannels.length === 0) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.NO_SOURCE_CHANNELS,
    });
    return { state: STATES.NONE, data: {} };
  }

  await api.sendMessage({
    chat_id: message.chat.id,
    text: MSG.SELECT_SOURCE,
    reply_markup: sourceChannelsKeyboard(sourceChannels),
    parse_mode: 'HTML',
  });

  return { state: STATES.SELECT_SOURCE, data: {} };
}

// ── Select Source Channel ───────────────────────────────────────────────

export async function selectSource(callbackQuery, session) {
  const channelId = callbackQuery.data.replace('src:', '');
  const channel = getChannel(channelId);
  const channelTitle = channel?.title || channelId;

  await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
  await api.editMessageText({
    chat_id: callbackQuery.message.chat.id,
    message_id: callbackQuery.message.message_id,
    text: `✅ کانال مبدأ: <b>${channelTitle}</b>\n\n${MSG.ENTER_MESSAGE_IDS}`,
    parse_mode: 'HTML',
    reply_markup: inlineCancelKeyboard(),
  });

  return {
    state: STATES.INPUT_IDS,
    data: { ...session.data, sourceChannel: channelId, sourceChannelTitle: channelTitle },
  };
}

// ── Receive Message IDs ────────────────────────────────────────────────

export async function receiveMessageIds(message, session) {
  const text = message.text?.trim();

  // Cancel
  if (text === '❌ لغو') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.CANCELLED,
      reply_markup: mainMenuKeyboard(isOwner(message.from.id)),
    });
    return { state: STATES.NONE, data: {} };
  }

  const messageIds = parseMessageIds(text);
  if (!messageIds) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.INVALID_MESSAGE_IDS,
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_IDS, data: session.data };
  }

  // Set defaults
  const now = nowTehran();
  const hours = getDefaultHours();
  const data = {
    ...session.data,
    messageIds,
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    day: now.getDate(),
    hour: hours[0] || 12,
    minute: 0,
  };

  const idsText = formatMessageIds(messageIds);
  const source = data.sourceChannelTitle || '';

  await api.sendMessage({
    chat_id: message.chat.id,
    text: MSG.MESSAGE_IDS_CONFIRM({ count: messageIds.length, idsText, source }),
    reply_markup: datetimeKeyboard(data.year, data.month, data.day, data.hour, data.minute),
    parse_mode: 'HTML',
  });

  return { state: STATES.SELECT_DATETIME, data };
}

// ── Datetime Callback ───────────────────────────────────────────────────

export async function datetimeCallback(callbackQuery, session) {
  const data = callbackQuery.data;
  const chatId = callbackQuery.message.chat.id;
  const msgId = callbackQuery.message.message_id;
  const sd = session.data;

  // Month selection
  if (data === 'dt:month') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '🗓 <b>ماه را انتخاب کن:</b>',
      reply_markup: monthsKeyboard(sd.month || nowTehran().getMonth() + 1),
      parse_mode: 'HTML',
    });
    return { state: STATES.SELECT_DATETIME, data: sd };
  }

  // Month confirmed (from months keyboard)
  if (data.startsWith('m:')) {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const month = parseInt(data.replace('m:', ''));
    const year = sd.year || nowTehran().getFullYear();
    let day = sd.day || 1;
    const maxDay = getMonthDays(year, month);
    if (day > maxDay) day = maxDay;

    const newData = { ...sd, month, day };
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.SELECT_DATETIME_MSG({
        date: `${day} ${MONTH_NAMES[month] || month} ${year}`,
        time: `${String(sd.hour || 0).padStart(2, '0')}:00`,
      }),
      reply_markup: datetimeKeyboard(year, month, day, sd.hour || 0, sd.minute || 0),
      parse_mode: 'HTML',
    });
    return { state: STATES.SELECT_DATETIME, data: newData };
  }

  // Year
  if (data === 'dt:year') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '📅 <b>سال</b>\n\nسال را وارد کن (مثال: <code>2027</code>):\n\nبرای لغو دکمه زیر را بزن.',
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_YEAR, data: sd };
  }

  // Day
  if (data === 'dt:day') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const year = sd.year || nowTehran().getFullYear();
    const month = sd.month || nowTehran().getMonth() + 1;
    const maxDay = getMonthDays(year, month);
    const monthName = MONTH_NAMES[month] || String(month);

    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: `📆 <b>روز</b>\n\nماه ${monthName} از ۱ تا ${maxDay} روز دارد.\n\nروز را وارد کن (مثال: <code>15</code>):\n\nبرای لغو دکمه زیر را بزن.`,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_DAY, data: sd };
  }

  // Hour
  if (data === 'dt:hour') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const hours = getDefaultHours();
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '🕐 <b>ساعت</b>\n\nیکی از ساعت‌های پیش‌فرض را انتخاب کن یا ساعت دلخواه را به فرمت <code>HH:MM</code> وارد کن.\n\n(مثال: <code>14:30</code>)',
      reply_markup: hoursKeyboard(hours, sd.hour),
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_HOUR, data: sd };
  }

  // Back from month/hour selection
  if (data === 'dt:back') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.SELECT_DATETIME_MSG({
        date: `${sd.day} ${MONTH_NAMES[sd.month] || sd.month} ${sd.year}`,
        time: `${String(sd.hour || 0).padStart(2, '0')}:${String(sd.minute || 0).padStart(2, '0')}`,
      }),
      reply_markup: datetimeKeyboard(sd.year, sd.month, sd.day, sd.hour || 0, sd.minute || 0),
      parse_mode: 'HTML',
    });
    return { state: STATES.SELECT_DATETIME, data: sd };
  }

  // Hour selected (from hours keyboard)
  if (data.startsWith('h:') && data !== 'h:custom') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const hour = parseInt(data.replace('h:', ''));
    const newData = { ...sd, hour, minute: 0 };

    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.SELECT_DATETIME_MSG({
        date: `${newData.day} ${MONTH_NAMES[newData.month] || newData.month} ${newData.year}`,
        time: `${String(hour).padStart(2, '0')}:00`,
      }),
      reply_markup: datetimeKeyboard(newData.year, newData.month, newData.day, hour, 0),
      parse_mode: 'HTML',
    });
    return { state: STATES.SELECT_DATETIME, data: newData };
  }

  // Custom hour
  if (data === 'h:custom') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '🕐 ساعت دلخواه را به فرمت <code>HH:MM</code> وارد کن.\n\n(مثال: <code>14:30</code>)\n\nیا ❌ لغو را بزن.',
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_HOUR, data: sd };
  }

  // Submit
  if (data === 'dt:submit') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id, text: '⏳ در حال ثبت...' });

    const year = sd.year;
    const month = sd.month;
    const day = sd.day;
    const hour = sd.hour;
    const minute = sd.minute || 0;

    const now = nowTehran();
    const timestamp = toTimestamp(year, month, day, hour, minute);
    const targetDt = new Date(timestamp * 1000);

    if (targetDt <= now) {
      await api.editMessageText({
        chat_id: chatId, message_id: msgId,
        text: '❌ تاریخ و ساعت در گذشته است. لطفاً زمان آینده‌ای انتخاب کن.',
        reply_markup: datetimeKeyboard(year, month, day, hour, minute),
        parse_mode: 'HTML',
      });
      return { state: STATES.SELECT_DATETIME, data: sd };
    }

    // Check dest channels
    const destChannels = getChannels(CHANNEL_DESTINATION);
    if (destChannels.length === 0) {
      await api.editMessageText({
        chat_id: chatId, message_id: msgId,
        text: MSG.NO_DEST_CHANNELS,
      });
      return { state: STATES.NONE, data: {} };
    }

    const dateStr = `${day} ${MONTH_NAMES[month] || month} ${year}`;
    const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;

    const newData = { ...sd, scheduleDate: dateStr, scheduleTime: timeStr, scheduleTimestamp: timestamp };

    const idsText = formatMessageIds(sd.messageIds || []);
    const source = sd.sourceChannelTitle || '';

    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.SCHEDULE_SUMMARY({
        source,
        ids: idsText,
        count: (sd.messageIds || []).length,
        date: dateStr,
        time: timeStr,
      }),
      reply_markup: destChannelsKeyboard(destChannels),
      parse_mode: 'HTML',
    });
    return { state: STATES.SELECT_TARGET, data: newData };
  }

  // Cancel
  if (data === 'cancel') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.CANCELLED,
    });
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(callbackQuery.from.id)),
      reply_markup: mainMenuKeyboard(isOwner(callbackQuery.from.id)),
      parse_mode: 'HTML',
    });
    return { state: STATES.NONE, data: {} };
  }

  await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
  return { state: STATES.SELECT_DATETIME, data: sd };
}

// ── Input Year ──────────────────────────────────────────────────────────

export async function inputYear(message, session) {
  const text = message.text?.trim();

  if (text === '❌ لغو') {
    return await _backToDatetime(message, session);
  }

  const year = parseInt(text);
  const currentYear = nowTehran().getFullYear();

  if (isNaN(year) || year < currentYear || year > currentYear + 10) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: `❌ سال باید بین ${currentYear} و ${currentYear + 10} باشد.\n\nدوباره تلاش کن یا ❌ لغو را بزن.`,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_YEAR, data: session.data };
  }

  const newData = { ...session.data, year };
  return await _backToDatetimeWithData(message, newData);
}

// ── Input Day ───────────────────────────────────────────────────────────

export async function inputDay(message, session) {
  const text = message.text?.trim();

  if (text === '❌ لغو') {
    return await _backToDatetime(message, session);
  }

  const day = parseInt(text);
  if (isNaN(day) || day < 1 || day > 31) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: '❌ روز نامعتبر است. لطفاً عددی بین 1 و 31 وارد کن.\n\nیا ❌ لغو را بزن.',
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_DAY, data: session.data };
  }

  const year = session.data.year || nowTehran().getFullYear();
  const month = session.data.month || nowTehran().getMonth() + 1;
  const maxDay = getMonthDays(year, month);

  if (day > maxDay) {
    const monthName = MONTH_NAMES[month] || String(month);
    await api.sendMessage({
      chat_id: message.chat.id,
      text: `❌ ماه ${monthName} حداکثر ${maxDay} روز دارد.\n\nدوباره تلاش کن یا ❌ لغو را بزن.`,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_DAY, data: session.data };
  }

  const newData = { ...session.data, day };
  return await _backToDatetimeWithData(message, newData);
}

// ── Input Hour ──────────────────────────────────────────────────────────

export async function inputHour(message, session) {
  const text = message.text?.trim();

  if (text === '❌ لغو') {
    return await _backToDatetime(message, session);
  }

  // If it's a callback (hour button pressed)
  if (text.startsWith('h:')) {
    const hour = parseInt(text.replace('h:', ''));
    const newData = { ...session.data, hour, minute: 0 };
    return await _backToDatetimeWithData(message, newData);
  }

  const result = validateHourInput(text);
  if (!result.valid) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: '❌ ساعت نامعتبر است.\n\nلطفاً به فرمت <code>HH:MM</code> وارد کن (مثال: <code>14:30</code>).\n\nیا ❌ لغو را بزن.',
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.INPUT_HOUR, data: session.data };
  }

  const newData = { ...session.data, hour: result.hour, minute: result.minute };
  return await _backToDatetimeWithData(message, newData);
}

// ── Select Target Channel ───────────────────────────────────────────────

export async function selectTarget(callbackQuery, session) {
  const data = callbackQuery.data;

  if (data === 'cancel') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: callbackQuery.message.chat.id,
      message_id: callbackQuery.message.message_id,
      text: MSG.CANCELLED,
    });
    await api.sendMessage({
      chat_id: callbackQuery.message.chat.id,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(callbackQuery.from.id)),
      reply_markup: mainMenuKeyboard(isOwner(callbackQuery.from.id)),
      parse_mode: 'HTML',
    });
    return { state: STATES.NONE, data: {} };
  }

  if (data.startsWith('dst:')) {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id, text: '⏳ در حال زمان‌بندی...' });

    const channelId = data.replace('dst:', '');
    const channel = getChannel(channelId);
    const channelTitle = channel?.title || channelId;

    const sd = session.data;
    const postId = addPost({
      chatId: callbackQuery.message.chat.id,
      userId: callbackQuery.from.id,
      sourceChannel: sd.sourceChannel,
      sourceChannelTitle: sd.sourceChannelTitle,
      messageIds: sd.messageIds || [],
      targetChannel: channelId,
      targetChannelTitle: channelTitle,
      scheduleDate: sd.scheduleDate,
      scheduleTime: sd.scheduleTime,
      scheduleTimestamp: sd.scheduleTimestamp,
    });

    await api.editMessageText({
      chat_id: callbackQuery.message.chat.id,
      message_id: callbackQuery.message.message_id,
      text: MSG.SCHEDULED_SUCCESS({
        source: sd.sourceChannelTitle,
        count: (sd.messageIds || []).length,
        target: channelTitle,
        date: sd.scheduleDate,
        time: sd.scheduleTime,
        postId,
      }),
      parse_mode: 'HTML',
    });

    await api.sendMessage({
      chat_id: callbackQuery.message.chat.id,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(callbackQuery.from.id)),
      reply_markup: mainMenuKeyboard(isOwner(callbackQuery.from.id)),
      parse_mode: 'HTML',
    });

    return { state: STATES.NONE, data: {} };
  }

  return { state: STATES.SELECT_TARGET, data: session.data };
}

// ── Helpers ─────────────────────────────────────────────────────────────

async function _backToDatetime(message, session) {
  return await _backToDatetimeWithData(message, session.data);
}

async function _backToDatetimeWithData(message, data) {
  const dateStr = `${data.day} ${MONTH_NAMES[data.month] || data.month} ${data.year}`;
  const timeStr = `${String(data.hour || 0).padStart(2, '0')}:${String(data.minute || 0).padStart(2, '0')}`;

  await api.sendMessage({
    chat_id: message.chat.id,
    text: MSG.SELECT_DATETIME_MSG({ date: dateStr, time: timeStr }),
    reply_markup: datetimeKeyboard(data.year, data.month, data.day, data.hour || 0, data.minute || 0),
    parse_mode: 'HTML',
  });

  return { state: STATES.SELECT_DATETIME, data };
}

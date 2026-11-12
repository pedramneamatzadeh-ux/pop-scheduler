// ============================================================================
// Settings Flow — manage channels, admins, hours
// ============================================================================
import { api } from 'sdk';
import { STATES, MSG } from './constants.js';
import { isOwner, isAdminOrOwner } from './auth.js';
import {
  getChannels, getChannel, addChannel, removeChannel,
  getAdmins, getAdmin, addAdmin, removeAdmin,
  getDefaultHours, addHour, removeHour,
} from './db.js';
import { CHANNEL_SOURCE, CHANNEL_DESTINATION } from './config.js';
import {
  settingsKeyboard, channelsTypeKeyboard,
  channelsManageKeyboard, hoursManageKeyboard,
  adminsManageKeyboard, inlineCancelKeyboard, mainMenuKeyboard,
} from './keyboards.js';
import { normalizeDigits } from './utils.js';

// ── Show Settings ───────────────────────────────────────────────────────

export async function showSettings(message) {
  const userId = message.from.id;
  const ownerOnly = isOwner(userId);

  await api.sendMessage({
    chat_id: message.chat.id,
    text: MSG.SETTINGS_MENU_MSG(ownerOnly),
    reply_markup: settingsKeyboard(ownerOnly),
    parse_mode: 'HTML',
  });

  return { state: STATES.SETTINGS_MENU, data: {} };
}

// ── Handle Settings Callback ────────────────────────────────────────────

export async function handleSettingsCallback(callbackQuery, session) {
  const data = callbackQuery.data;
  const chatId = callbackQuery.message.chat.id;
  const msgId = callbackQuery.message.message_id;
  const userId = callbackQuery.from.id;

  // Main menu
  if (data === 'main_menu') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(userId)),
    });
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(userId)),
      reply_markup: mainMenuKeyboard(isOwner(userId)),
      parse_mode: 'HTML',
    });
    return { state: STATES.NONE, data: {} };
  }

  // Owner-only checks
  if (!isOwner(userId)) {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id, text: MSG.ACCESS_DENIED, show_alert: true });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Channels menu
  if (data === 'st:channels') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.CHANNELS_MENU,
      reply_markup: channelsTypeKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Source channels list
  if (data === 'st:source_channels') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const sourceChannels = getChannels(CHANNEL_SOURCE, false);
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '📥 <b>کانال‌های مبدأ</b>',
      reply_markup: channelsManageKeyboard(sourceChannels, 'source'),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Dest channels list
  if (data === 'st:dest_channels') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const destChannels = getChannels(CHANNEL_DESTINATION, false);
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '📤 <b>کانال‌های مقصد</b>',
      reply_markup: channelsManageKeyboard(destChannels, 'destination'),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Remove source channel
  if (data.startsWith('rmsrc:')) {
    const channelId = data.replace('rmsrc:', '');
    const channel = getChannel(channelId);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    removeChannel(channelId);
    const title = channel?.title || channelId;
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.CHANNEL_REMOVED(title),
      parse_mode: 'HTML',
    });
    const sourceChannels = getChannels(CHANNEL_SOURCE, false);
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.CHANNEL_REMOVED(title),
      reply_markup: channelsManageKeyboard(sourceChannels, 'source'),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Remove dest channel
  if (data.startsWith('rmdst:')) {
    const channelId = data.replace('rmdst:', '');
    const channel = getChannel(channelId);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    removeChannel(channelId);
    const title = channel?.title || channelId;
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.CHANNEL_REMOVED(title),
      parse_mode: 'HTML',
    });
    const destChannels = getChannels(CHANNEL_DESTINATION, false);
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.CHANNEL_REMOVED(title),
      reply_markup: channelsManageKeyboard(destChannels, 'destination'),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Add source channel
  if (data === 'add_source') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.ENTER_CHANNEL_ID,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.ADD_CHANNEL, data: { addingType: 'source' } };
  }

  // Add dest channel
  if (data === 'add_dest') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.ENTER_CHANNEL_ID,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.ADD_CHANNEL, data: { addingType: 'destination' } };
  }

  // Hours menu
  if (data === 'st:hours') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const hours = getDefaultHours();
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '🕐 <b>ساعت‌های پیش‌فرض</b>\n\nاین ساعت‌ها هنگام زمان‌بندی پیشنهاد داده می‌شوند.',
      reply_markup: hoursManageKeyboard(hours),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Remove hour
  if (data.startsWith('rmh:')) {
    const hour = parseInt(data.replace('rmh:', ''));
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    removeHour(hour);
    const hours = getDefaultHours();
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.HOUR_REMOVED(hour),
      parse_mode: 'HTML',
    });
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.HOUR_REMOVED(hour),
      reply_markup: hoursManageKeyboard(hours),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Add hour
  if (data === 'add_hour') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.ENTER_HOUR,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.CUSTOM_HOUR_INPUT, data: {} };
  }

  // Admins menu
  if (data === 'st:admins') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const adminList = getAdmins();
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '👥 <b>مدیران</b>\n\nمدیران می‌توانند از ربات استفاده کنند.',
      reply_markup: adminsManageKeyboard(adminList),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Remove admin
  if (data.startsWith('rmadm:')) {
    const adminUserId = parseInt(data.replace('rmadm:', ''));
    const admin = getAdmin(adminUserId);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    removeAdmin(adminUserId);
    const name = admin?.firstName || admin?.username || String(adminUserId);
    const adminList = getAdmins();
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.ADMIN_REMOVED(name),
      parse_mode: 'HTML',
    });
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.ADMIN_REMOVED(name),
      reply_markup: adminsManageKeyboard(adminList),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  // Add admin
  if (data === 'add_admin') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.ENTER_ADMIN_ID,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.ADD_ADMIN, data: {} };
  }

  // Back
  if (data === 'st:back') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const ownerOnly = isOwner(userId);
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.SETTINGS_MENU_MSG(ownerOnly),
      reply_markup: settingsKeyboard(ownerOnly),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  return { state: STATES.SETTINGS_MENU, data: {} };
}

// ── Add Channel Input ───────────────────────────────────────────────────

export async function addChannelInput(message, session) {
  const text = message.text?.trim();

  if (text === '❌ لغو') {
    const userId = message.from.id;
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.SETTINGS_MENU_MSG(isOwner(userId)),
      reply_markup: settingsKeyboard(isOwner(userId)),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  const addingType = session.data.addingType || CHANNEL_DESTINATION;
  const channelId = text;

  // Try to get channel info from Telegram
  let title = '';
  let username = '';
  try {
    const chat = await api.getChat({ chat_id: channelId });
    title = chat.title || chat.first_name || '';
    username = chat.username || '';
  } catch {
    title = channelId;
  }

  const added = addChannel(channelId, title, username, addingType);
  if (added) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.CHANNEL_ADDED(title || channelId),
      parse_mode: 'HTML',
    });
  } else {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: '⚠️ این کانال قبلاً اضافه شده.',
      parse_mode: 'HTML',
    });
  }

  // Show updated list
  const channelType = addingType === 'source' ? CHANNEL_SOURCE : CHANNEL_DESTINATION;
  const allChannels = getChannels(channelType, false);
  await api.sendMessage({
    chat_id: message.chat.id,
    text: addingType === 'source' ? '📥 <b>کانال‌های مبدأ</b>' : '📤 <b>کانال‌های مقصد</b>',
    reply_markup: channelsManageKeyboard(allChannels, addingType),
    parse_mode: 'HTML',
  });

  return { state: STATES.SETTINGS_MENU, data: {} };
}

// ── Add Admin Input ─────────────────────────────────────────────────────

export async function addAdminInput(message, session) {
  const text = message.text?.trim();

  if (text === '❌ لغو') {
    const userId = message.from.id;
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.SETTINGS_MENU_MSG(isOwner(userId)),
      reply_markup: settingsKeyboard(isOwner(userId)),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  const normalized = normalizeDigits(text);
  const adminUserId = parseInt(normalized);

  if (isNaN(adminUserId) || adminUserId <= 0) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.INVALID_INPUT,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.ADD_ADMIN, data: {} };
  }

  // Try to get user info
  let firstName = '';
  let username = '';
  try {
    const chat = await api.getChat({ chat_id: adminUserId });
    firstName = chat.first_name || '';
    username = chat.username || '';
  } catch {}

  const added = addAdmin(adminUserId, username, firstName);
  const name = firstName || username || String(adminUserId);

  if (added) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.ADMIN_ADDED(name),
      parse_mode: 'HTML',
    });
  } else {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: '⚠️ این کاربر قبلاً اضافه شده.',
      parse_mode: 'HTML',
    });
  }

  const adminList = getAdmins();
  await api.sendMessage({
    chat_id: message.chat.id,
    text: '👥 <b>مدیران</b>',
    reply_markup: adminsManageKeyboard(adminList),
    parse_mode: 'HTML',
  });

  return { state: STATES.SETTINGS_MENU, data: {} };
}

// ── Add Hour Input ──────────────────────────────────────────────────────

export async function addHourInput(message, session) {
  const text = message.text?.trim();

  if (text === '❌ لغو') {
    const userId = message.from.id;
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.SETTINGS_MENU_MSG(isOwner(userId)),
      reply_markup: settingsKeyboard(isOwner(userId)),
      parse_mode: 'HTML',
    });
    return { state: STATES.SETTINGS_MENU, data: {} };
  }

  const normalized = normalizeDigits(text);
  const hour = parseInt(normalized);

  if (isNaN(hour) || hour < 0 || hour > 23) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.INVALID_INPUT,
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.CUSTOM_HOUR_INPUT, data: {} };
  }

  const added = addHour(hour);
  if (added) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: MSG.HOUR_ADDED(hour),
      parse_mode: 'HTML',
    });
  } else {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: '⚠️ این ساعت قبلاً اضافه شده.',
      parse_mode: 'HTML',
    });
  }

  const hours = getDefaultHours();
  await api.sendMessage({
    chat_id: message.chat.id,
    text: '🕐 <b>ساعت‌های پیش‌فرض</b>',
    reply_markup: hoursManageKeyboard(hours),
    parse_mode: 'HTML',
  });

  return { state: STATES.SETTINGS_MENU, data: {} };
}

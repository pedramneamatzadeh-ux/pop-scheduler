// ============================================================================
// Message Handler — routes messages based on conversation state
// ============================================================================
import { api } from 'sdk';
import { STATES, MSG } from '../lib/constants.js';
import { isOwner, isAdminOrOwner } from '../lib/auth.js';
import { mainMenuKeyboard } from '../lib/keyboards.js';
import { getSession, setSession, clearSession } from '../lib/session.js';
import { checkAndDeliver } from '../lib/scheduler.js';
import * as scheduleFlow from '../lib/schedule-flow.js';
import { showActivePosts, handlePostsCallback, editCustomTimeInput } from '../lib/posts-flow.js';
import { showSettings, handleSettingsCallback, addChannelInput, addAdminInput, addHourInput } from '../lib/settings-flow.js';
import { showHistory } from '../lib/history-flow.js';

export default async function (message, ctx) {
  const userId = message.from.id;
  const chatId = message.chat.id;
  const text = message.text?.trim();

  // ── Check for overdue posts first ──────────────────────────────────
  try {
    await checkAndDeliver();
  } catch (e) {
    // Don't block on scheduler errors
  }

  // ── Get current session state ───────────────────────────────────────
  const session = await getSession(userId);

  // ── Handle based on state ──────────────────────────────────────────
  const state = session.state;

  // No state — handle main menu commands
  if (state === STATES.NONE || !state) {
    return await _handleMainMenu(message, text);
  }

  // Schedule flow states
  if (state === STATES.INPUT_IDS) {
    const result = await scheduleFlow.receiveMessageIds(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  if (state === STATES.INPUT_YEAR) {
    const result = await scheduleFlow.inputYear(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  if (state === STATES.INPUT_DAY) {
    const result = await scheduleFlow.inputDay(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  if (state === STATES.INPUT_HOUR) {
    const result = await scheduleFlow.inputHour(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  // Settings flow states
  if (state === STATES.ADD_CHANNEL) {
    const result = await addChannelInput(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  if (state === STATES.ADD_ADMIN) {
    const result = await addAdminInput(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  if (state === STATES.CUSTOM_HOUR_INPUT) {
    const result = await addHourInput(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  // Posts flow — custom time input
  if (state === STATES.EDIT_CUSTOM_TIME) {
    const result = await editCustomTimeInput(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  // Default: clear state and show main menu
  await clearSession(userId);
  await _handleMainMenu(message, text);
}

// ── Main Menu Handler ───────────────────────────────────────────────────

async function _handleMainMenu(message, text) {
  const userId = message.from.id;
  const chatId = message.chat.id;

  // /start or /help
  if (text === '/start' || text === '/help') {
    const name = message.from.first_name || '';
    const admin = await isAdminOrOwner(userId);
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.WELCOME(name, admin),
      reply_markup: mainMenuKeyboard(isOwner(userId)),
      parse_mode: 'HTML',
    });
    return;
  }

  // 📅 زمان‌بندی جدید
  if (text === '📅 زمان‌بندی جدید') {
    if (!await isAdminOrOwner(userId)) {
      await api.sendMessage({ chat_id: chatId, text: MSG.ACCESS_DENIED });
      return;
    }
    const session = await getSession(userId);
    const result = await scheduleFlow.startSchedule(message, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  // 📋 پست‌های فعال
  if (text === '📋 پست‌های فعال') {
    if (!await isAdminOrOwner(userId)) {
      await api.sendMessage({ chat_id: chatId, text: MSG.ACCESS_DENIED });
      return;
    }
    await showActivePosts(chatId, 0);
    return;
  }

  // 📊 تاریخچه
  if (text === '📊 تاریخچه') {
    if (!await isAdminOrOwner(userId)) {
      await api.sendMessage({ chat_id: chatId, text: MSG.ACCESS_DENIED });
      return;
    }
    await showHistory(chatId, 0);
    return;
  }

  // ⚙️ تنظیمات
  if (text === '⚙️ تنظیمات') {
    if (!await isAdminOrOwner(userId)) {
      await api.sendMessage({ chat_id: chatId, text: MSG.ACCESS_DENIED });
      return;
    }
    const result = await showSettings(message);
    await setSession(userId, result.state, result.data);
    return;
  }

  // ❌ لغو (from reply keyboard)
  if (text === '❌ لغو') {
    await clearSession(userId);
    const name = message.from.first_name || '';
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.CANCELLED,
      reply_markup: mainMenuKeyboard(isOwner(userId)),
    });
    return;
  }

  // Default: show welcome
  const name = message.from.first_name || '';
  const admin = await isAdminOrOwner(userId);
  await api.sendMessage({
    chat_id: chatId,
    text: MSG.WELCOME(name, admin),
    reply_markup: mainMenuKeyboard(isOwner(userId)),
    parse_mode: 'HTML',
  });
}

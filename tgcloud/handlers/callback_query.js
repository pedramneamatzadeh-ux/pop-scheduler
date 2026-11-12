// ============================================================================
// Callback Query Handler — routes callbacks based on conversation state
// ============================================================================
import { api } from 'sdk';
import { STATES, MSG } from '../lib/constants.js';
import { isOwner, isAdminOrOwner } from '../lib/auth.js';
import { mainMenuKeyboard } from '../lib/keyboards.js';
import { getSession, setSession, clearSession } from '../lib/session.js';
import { checkAndDeliver } from '../lib/scheduler.js';
import * as scheduleFlow from '../lib/schedule-flow.js';
import { handlePostsCallback, showActivePosts } from '../lib/posts-flow.js';
import { handleSettingsCallback } from '../lib/settings-flow.js';
import { handleHistoryCallback } from '../lib/history-flow.js';

export default async function (callbackQuery, ctx) {
  const userId = callbackQuery.from.id;
  const chatId = callbackQuery.message.chat.id;
  const data = callbackQuery.data;

  // ── Check for overdue posts ────────────────────────────────────────
  try {
    await checkAndDeliver();
  } catch (e) {
    // Don't block on scheduler errors
  }

  // ── Get session ─────────────────────────────────────────────────────
  const session = await getSession(userId);
  const state = session.state;

  // ── Global callbacks ────────────────────────────────────────────────

  // Cancel (from any state)
  if (data === 'cancel' && state !== STATES.NONE) {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId,
      message_id: callbackQuery.message.message_id,
      text: MSG.CANCELLED,
    });
    const name = callbackQuery.from.first_name || '';
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.WELCOME(name, isOwner(userId)),
      reply_markup: mainMenuKeyboard(isOwner(userId)),
      parse_mode: 'HTML',
    });
    await clearSession(userId);
    return;
  }

  // Main menu
  if (data === 'main_menu') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId,
      message_id: callbackQuery.message.message_id,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(userId)),
    });
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(userId)),
      reply_markup: mainMenuKeyboard(isOwner(userId)),
      parse_mode: 'HTML',
    });
    await clearSession(userId);
    return;
  }

  // Noop
  if (data === 'noop') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    return;
  }

  // ── Route based on state ────────────────────────────────────────────

  // Schedule flow
  if (
    state === STATES.SELECT_SOURCE ||
    state === STATES.INPUT_IDS ||
    state === STATES.SELECT_DATETIME ||
    state === STATES.INPUT_YEAR ||
    state === STATES.INPUT_DAY ||
    state === STATES.INPUT_HOUR ||
    state === STATES.SELECT_TARGET
  ) {
    let result;

    if (state === STATES.SELECT_SOURCE && data.startsWith('src:')) {
      result = await scheduleFlow.selectSource(callbackQuery, session);
    } else if (state === STATES.SELECT_DATETIME || state === STATES.INPUT_HOUR) {
      result = await scheduleFlow.datetimeCallback(callbackQuery, session);
    } else if (state === STATES.SELECT_TARGET) {
      result = await scheduleFlow.selectTarget(callbackQuery, session);
    } else {
      // Handle month selection from any datetime state
      if (data.startsWith('m:')) {
        result = await scheduleFlow.datetimeCallback(callbackQuery, session);
      } else {
        await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
        return;
      }
    }

    if (result) {
      await setSession(userId, result.state, result.data);
    }
    return;
  }

  // Posts flow
  if (
    state === STATES.MANAGE_POSTS ||
    state === STATES.POST_DETAIL ||
    state === STATES.EDIT_DATE ||
    state === STATES.EDIT_TIME ||
    state === STATES.EDIT_CUSTOM_TIME
  ) {
    // Handle edit custom time cancel
    if (data === 'cancel' && state === STATES.EDIT_CUSTOM_TIME) {
      await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
      // Go back to edit datetime
      const result = await handlePostsCallback(callbackQuery, session);
      await setSession(userId, result.state, result.data);
      return;
    }

    const result = await handlePostsCallback(callbackQuery, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  // Settings flow
  if (
    state === STATES.SETTINGS_MENU ||
    state === STATES.ADD_CHANNEL ||
    state === STATES.ADD_ADMIN ||
    state === STATES.CUSTOM_HOUR_INPUT
  ) {
    // Handle inline cancel in settings
    if (data === 'cancel') {
      await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
      await api.editMessageText({
        chat_id: chatId,
        message_id: callbackQuery.message.message_id,
        text: MSG.SETTINGS_MENU_MSG(isOwner(userId)),
      });
      await setSession(userId, STATES.SETTINGS_MENU, {});
      return;
    }

    const result = await handleSettingsCallback(callbackQuery, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  // History flow
  if (state === STATES.VIEW_HISTORY) {
    const result = await handleHistoryCallback(callbackQuery, session);
    await setSession(userId, result.state, result.data);
    return;
  }

  // Default: answer and ignore
  await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
}

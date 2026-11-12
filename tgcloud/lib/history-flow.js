// ============================================================================
// History Flow — view sent/failed posts
// ============================================================================
import { api } from 'sdk';
import { STATES, MSG, STATUS_LABELS } from './constants.js';
import { getHistory, getHistoryCount, getPost } from './db.js';
import { isOwner, isAdminOrOwner } from './auth.js';
import { historyKeyboard, mainMenuKeyboard, postDetailKeyboard } from './keyboards.js';
import { formatScheduleDisplay, paginate } from './utils.js';

const POSTS_PER_PAGE = 5;

// ── Show History ────────────────────────────────────────────────────────

export async function showHistory(chatId, page = 0, editMessageId = null) {
  const allPosts = getHistory(1000);

  if (allPosts.length === 0) {
    const method = editMessageId ? api.editMessageText.bind(api) : api.sendMessage.bind(api);
    const params = { chat_id: chatId, text: MSG.NO_HISTORY };
    if (editMessageId) params.message_id = editMessageId;
    await method(params);
    return;
  }

  const { pageItems, totalPages } = paginate(allPosts, page, POSTS_PER_PAGE);
  const itemsText = pageItems.map(formatScheduleDisplay).join('\n\n');
  const text = MSG.HISTORY_LIST({ page: page + 1, total: totalPages, items: itemsText });
  const keyboard = historyKeyboard(pageItems, page, totalPages);

  if (editMessageId) {
    await api.editMessageText({
      chat_id: chatId, message_id: editMessageId,
      text, reply_markup: keyboard, parse_mode: 'HTML',
    });
  } else {
    await api.sendMessage({
      chat_id: chatId,
      text, reply_markup: keyboard, parse_mode: 'HTML',
    });
  }
}

// ── Handle History Callback ─────────────────────────────────────────────

export async function handleHistoryCallback(callbackQuery, session) {
  const data = callbackQuery.data;
  const chatId = callbackQuery.message.chat.id;
  const msgId = callbackQuery.message.message_id;

  // Main menu
  if (data === 'main_menu') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(callbackQuery.from.id)),
    });
    await api.sendMessage({
      chat_id: chatId,
      text: MSG.WELCOME(callbackQuery.from.first_name || '', isOwner(callbackQuery.from.id)),
      reply_markup: mainMenuKeyboard(isOwner(callbackQuery.from.id)),
      parse_mode: 'HTML',
    });
    return { state: STATES.NONE, data: {} };
  }

  // Pagination
  if (data.startsWith('pg:history:')) {
    const page = parseInt(data.split(':')[2]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await showHistory(chatId, page, msgId);
    return { state: STATES.VIEW_HISTORY, data: { historyPage: page } };
  }

  // Post detail in history
  if (data.startsWith('hpost:')) {
    const postId = parseInt(data.split(':')[1]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const post = getPost(postId);
    if (!post) {
      await api.editMessageText({ chat_id: chatId, message_id: msgId, text: '❌ پست پیدا نشد' });
      return { state: STATES.VIEW_HISTORY, data: session.data };
    }
    const statusLabel = STATUS_LABELS[post.status] || post.status;
    const ids = post.messageIds || [];
    const text = MSG.POST_DETAIL({
      postId: post.id,
      source: post.sourceChannelTitle || post.sourceChannel || 'نامشخص',
      messageIds: ids.join(', '),
      count: ids.length,
      target: post.targetChannelTitle || post.targetChannel,
      date: post.scheduleDate,
      time: post.scheduleTime,
      status: statusLabel,
      createdAt: post.createdAt || 'نامشخص',
    });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text, parse_mode: 'HTML',
    });
    return { state: STATES.VIEW_HISTORY, data: session.data };
  }

  return { state: STATES.VIEW_HISTORY, data: session.data };
}

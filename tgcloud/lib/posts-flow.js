// ============================================================================
// Posts Flow — manage scheduled (active) posts
// ============================================================================
import { api } from 'sdk';
import { STATES, MSG, STATUS_LABELS, MONTH_NAMES, STATUS_PENDING, STATUS_DISABLED } from './constants.js';
import { getPost, getPostsByStatus, deletePost, updateStatus, updateSchedule, updateTargetChannel, getChannels, addHistoryLog, getDefaultHours } from './db.js';
import { CHANNEL_DESTINATION } from './config.js';
import { isOwner, isAdminOrOwner } from './auth.js';
import {
  postListKeyboard, postDetailKeyboard, mainMenuKeyboard,
  datetimeKeyboard, monthsKeyboard, hoursKeyboard,
  destChannelsKeyboard, inlineCancelKeyboard,
} from './keyboards.js';
import { formatScheduleDisplay, paginate, toTimestamp, nowTehran, formatMessageIds } from './utils.js';

const POSTS_PER_PAGE = 5;

// ── Show Active Posts ───────────────────────────────────────────────────

export async function showActivePosts(chatId, page = 0, editMessageId = null) {
  const pendingPosts = getPostsByStatus(STATUS_PENDING);
  const disabledPosts = getPostsByStatus(STATUS_DISABLED);
  const allPosts = [...pendingPosts, ...disabledPosts]
    .sort((a, b) => (a.scheduleTimestamp || 0) - (b.scheduleTimestamp || 0));

  if (allPosts.length === 0) {
    const method = editMessageId ? api.editMessageText.bind(api) : api.sendMessage.bind(api);
    const params = {
      chat_id: chatId,
      text: MSG.NO_SCHEDULED_POSTS,
    };
    if (editMessageId) {
      params.message_id = editMessageId;
    }
    await method(params);
    return;
  }

  const { pageItems, totalPages } = paginate(allPosts, page, POSTS_PER_PAGE);
  const itemsText = pageItems.map(formatScheduleDisplay).join('\n\n');
  const text = MSG.SCHEDULED_LIST({ page: page + 1, total: totalPages, items: itemsText });
  const keyboard = postListKeyboard(pageItems, page, totalPages);

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

// ── Handle Posts Callback ───────────────────────────────────────────────

export async function handlePostsCallback(callbackQuery, session) {
  const data = callbackQuery.data;
  const chatId = callbackQuery.message.chat.id;
  const msgId = callbackQuery.message.message_id;
  const userId = callbackQuery.from.id;

  if (!await isAdminOrOwner(userId)) {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id, text: MSG.ACCESS_DENIED, show_alert: true });
    return { state: STATES.MANAGE_POSTS, data: {} };
  }

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

  // Back to list
  if (data === 'back_to_list') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const page = session.data.postsPage || 0;
    await showActivePosts(chatId, page, msgId);
    return { state: STATES.MANAGE_POSTS, data: session.data };
  }

  // Pagination
  if (data.startsWith('pg:posts:')) {
    const page = parseInt(data.split(':')[2]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await showActivePosts(chatId, page, msgId);
    return { state: STATES.MANAGE_POSTS, data: { ...session.data, postsPage: page } };
  }

  // Post detail
  if (data.startsWith('post:')) {
    const postId = parseInt(data.split(':')[1]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    return await _showPostDetail(chatId, msgId, postId);
  }

  // Delete
  if (data.startsWith('del:')) {
    const postId = parseInt(data.split(':')[1]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id, text: '🗑 حذف...' });
    deletePost(postId);
    addHistoryLog(postId, 'deleted', null, userId);
    await api.editMessageText({ chat_id: chatId, message_id: msgId, text: MSG.POST_DELETED });
    await showActivePosts(chatId, 0, msgId);
    return { state: STATES.MANAGE_POSTS, data: {} };
  }

  // Disable
  if (data.startsWith('disable_post:')) {
    const postId = parseInt(data.split(':')[1]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id, text: '⏸ غیرفعال...' });
    updateStatus(postId, STATUS_DISABLED);
    addHistoryLog(postId, 'disabled', null, userId);
    await api.editMessageText({ chat_id: chatId, message_id: msgId, text: MSG.POST_DISABLED_MSG });
    await showActivePosts(chatId, 0, msgId);
    return { state: STATES.MANAGE_POSTS, data: {} };
  }

  // Enable
  if (data.startsWith('enable_post:')) {
    const postId = parseInt(data.split(':')[1]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id, text: '▶️ فعال...' });
    updateStatus(postId, STATUS_PENDING);
    addHistoryLog(postId, 'enabled', null, userId);
    await api.editMessageText({ chat_id: chatId, message_id: msgId, text: MSG.POST_ENABLED_MSG });
    await showActivePosts(chatId, 0, msgId);
    return { state: STATES.MANAGE_POSTS, data: {} };
  }

  // Edit date
  if (data.startsWith('edit_date:')) {
    const postId = parseInt(data.split(':')[1]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const post = getPost(postId);
    if (!post) {
      await api.editMessageText({ chat_id: chatId, message_id: msgId, text: '❌ پست پیدا نشد' });
      return { state: STATES.MANAGE_POSTS, data: {} };
    }
    const now = nowTehran();
    const editData = {
      editingPostId: postId,
      editYear: now.getFullYear(),
      editMonth: now.getMonth() + 1,
      editDay: now.getDate(),
      editHour: parseInt(post.scheduleTime.split(':')[0]),
      editMinute: parseInt(post.scheduleTime.split(':')[1] || '0'),
    };
    return await _showEditDatetime(chatId, msgId, editData);
  }

  // Edit time
  if (data.startsWith('edit_time:')) {
    const postId = parseInt(data.split(':')[1]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const post = getPost(postId);
    if (!post) {
      await api.editMessageText({ chat_id: chatId, message_id: msgId, text: '❌ پست پیدا نشد' });
      return { state: STATES.MANAGE_POSTS, data: {} };
    }
    const now = nowTehran();
    const parts = post.scheduleDate.split(' ');
    let day = now.getDate(), month = now.getMonth() + 1, year = now.getFullYear();
    try {
      if (parts.length === 3) {
        day = parseInt(parts[0]);
        const monthName = parts[1];
        for (const [num, name] of Object.entries(MONTH_NAMES)) {
          if (name.toLowerCase() === monthName.toLowerCase()) {
            month = parseInt(num);
            break;
          }
        }
        year = parseInt(parts[2]);
      }
    } catch {}
    const editData = {
      editingPostId: postId,
      editYear: year,
      editMonth: month,
      editDay: day,
      editHour: parseInt(post.scheduleTime.split(':')[0]),
      editMinute: parseInt(post.scheduleTime.split(':')[1] || '0'),
    };
    return await _showEditDatetime(chatId, msgId, editData);
  }

  // Edit datetime callbacks
  if (data.startsWith('edt:month')) {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const currentMonth = session.data.editMonth || nowTehran().getMonth() + 1;
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '🗓 <b>ماه را انتخاب کن:</b>',
      reply_markup: monthsKeyboard(currentMonth),
      parse_mode: 'HTML',
    });
    return { state: STATES.EDIT_DATE, data: session.data };
  }

  if (data.startsWith('edm:')) {
    const month = parseInt(data.replace('edm:', ''));
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    return await _showEditDatetime(chatId, msgId, { ...session.data, editMonth: month });
  }

  if (data.startsWith('edh:')) {
    const hour = parseInt(data.replace('edh:', ''));
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    return await _showEditDatetime(chatId, msgId, { ...session.data, editHour: hour, editMinute: 0 });
  }

  if (data.startsWith('edt:hour')) {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const hours = getDefaultHours();
    const currentHour = session.data.editHour;
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '🕐 <b>ساعت</b>\n\nساعت ارسال را انتخاب کن:',
      reply_markup: { inline_keyboard: [
        ...(() => {
          const buttons = [];
          let row = [];
          for (const h of hours.sort((a, b) => a - b)) {
            const mark = h === currentHour ? '✅ ' : '';
            row.push({ text: `${mark}${String(h).padStart(2, '0')}:00`, callback_data: `edh:${h}` });
            if (row.length === 3) { buttons.push(row); row = []; }
          }
          if (row.length > 0) buttons.push(row);
          return buttons;
        })(),
        [{ text: '✏️ ساعت دلخواه', callback_data: 'edt:custom_hour' }, { text: '🔙 بازگشت', callback_data: 'edt:back' }],
      ]},
      parse_mode: 'HTML',
    });
    return { state: STATES.EDIT_TIME, data: session.data };
  }

  if (data === 'edt:back') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    return await _showEditDatetime(chatId, msgId, session.data);
  }

  if (data === 'edt:custom_hour') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '🕐 ساعت دلخواه را به فرمت <code>HH:MM</code> وارد کن.\n\n(مثال: <code>14:30</code>)\n\nیا ❌ لغو را بزن.',
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.EDIT_CUSTOM_TIME, data: session.data };
  }

  if (data.startsWith('edt:submit')) {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const postId = session.data.editingPostId;
    const year = session.data.editYear;
    const month = session.data.editMonth;
    const day = session.data.editDay;
    const hour = session.data.editHour || 0;
    const minute = session.data.editMinute || 0;

    const now = nowTehran();
    const timestamp = toTimestamp(year, month, day, hour, minute);
    const targetDt = new Date(timestamp * 1000);

    if (targetDt <= now) {
      await api.editMessageText({
        chat_id: chatId, message_id: msgId,
        text: '❌ تاریخ و ساعت در گذشته است.',
        parse_mode: 'HTML',
      });
      return { state: STATES.EDIT_DATE, data: session.data };
    }

    const dateStr = `${day} ${MONTH_NAMES[month] || month} ${year}`;
    const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
    updateSchedule(postId, dateStr, timeStr, timestamp);
    addHistoryLog(postId, 'schedule_changed', `to ${dateStr} ${timeStr}`, userId);

    await api.editMessageText({ chat_id: chatId, message_id: msgId, text: MSG.POST_EDITED });
    await showActivePosts(chatId, 0, msgId);
    return { state: STATES.MANAGE_POSTS, data: {} };
  }

  // Edit channel
  if (data.startsWith('edit_ch:')) {
    const postId = parseInt(data.split(':')[1]);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    const destChannels = getChannels(CHANNEL_DESTINATION);
    if (destChannels.length === 0) {
      await api.editMessageText({ chat_id: chatId, message_id: msgId, text: MSG.NO_DEST_CHANNELS });
      return { state: STATES.MANAGE_POSTS, data: {} };
    }
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text: '📢 کانال مقصد جدید را انتخاب کن:',
      reply_markup: destChannelsKeyboard(destChannels),
      parse_mode: 'HTML',
    });
    return { state: STATES.POST_DETAIL, data: { ...session.data, editingPostId: postId } };
  }

  // Destination selected (editing post)
  if (data.startsWith('dst:') && session.data.editingPostId) {
    const postId = session.data.editingPostId;
    const channelId = data.replace('dst:', '');
    const channel = getChannels(CHANNEL_DESTINATION).find(ch => ch.channelId === channelId);
    const channelTitle = channel?.title || channelId;
    updateTargetChannel(postId, channelId, channelTitle);
    addHistoryLog(postId, 'channel_changed', `to ${channelTitle}`, userId);
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id, text: '✅ کانال تغییر کرد' });
    return await _showPostDetail(chatId, msgId, postId);
  }

  if (data === 'noop') {
    await api.answerCallbackQuery({ callback_query_id: callbackQuery.id });
    return { state: STATES.MANAGE_POSTS, data: session.data };
  }

  return { state: STATES.MANAGE_POSTS, data: session.data };
}

// ── Edit Custom Time Input ──────────────────────────────────────────────

export async function editCustomTimeInput(message, session) {
  const text = message.text?.trim();

  if (text === '❌ لغو') {
    return await _showEditDatetime(message.chat.id, null, session.data);
  }

  const { validateHourInput } = await import('./utils.js');
  const result = validateHourInput(text);
  if (!result.valid) {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: '❌ ساعت نامعتبر. به فرمت <code>HH:MM</code> وارد کن.',
      reply_markup: inlineCancelKeyboard(),
      parse_mode: 'HTML',
    });
    return { state: STATES.EDIT_CUSTOM_TIME, data: session.data };
  }

  return await _showEditDatetime(message.chat.id, null, {
    ...session.data,
    editHour: result.hour,
    editMinute: result.minute,
  });
}

// ── Helpers ─────────────────────────────────────────────────────────────

async function _showPostDetail(chatId, msgId, postId) {
  const post = getPost(postId);
  if (!post) {
    await api.editMessageText({ chat_id: chatId, message_id: msgId, text: '❌ پست پیدا نشد' });
    return { state: STATES.MANAGE_POSTS, data: {} };
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

  const keyboard = postDetailKeyboard(postId, post.status);

  if (msgId) {
    await api.editMessageText({
      chat_id: chatId, message_id: msgId,
      text, reply_markup: keyboard, parse_mode: 'HTML',
    });
  } else {
    await api.sendMessage({
      chat_id: chatId,
      text, reply_markup: keyboard, parse_mode: 'HTML',
    });
  }
  return { state: STATES.POST_DETAIL, data: {} };
}

async function _showEditDatetime(chatId, msgId, data) {
  const year = data.editYear;
  const month = data.editMonth;
  const day = data.editDay;
  const hour = data.editHour || 0;
  const minute = data.editMinute || 0;
  const dateStr = `${day} ${MONTH_NAMES[month] || month} ${year}`;
  const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;

  const params = {
    chat_id: chatId,
    text: `📅 <b>ویرایش تاریخ و ساعت</b>\n\n📅 تاریخ: <b>${dateStr}</b>\n🕐 ساعت: <b>${timeStr}</b>\n\nروی هر دکمه کلیک کن تا تغییر دهی:`,
    reply_markup: datetimeKeyboard(year, month, day, hour, minute, 'edt'),
    parse_mode: 'HTML',
  };

  if (msgId) {
    params.message_id = msgId;
    await api.editMessageText(params);
  } else {
    await api.sendMessage(params);
  }
  return { state: STATES.EDIT_DATE, data };
}

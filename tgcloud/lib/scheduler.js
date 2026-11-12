// ============================================================================
// Scheduler — checks and delivers overdue posts
// ============================================================================
// Since Telegram Serverless is event-driven (no cron), we check for
// overdue posts on every update. If any posts are due, we deliver them.

import { api } from 'sdk';
import { getDuePosts, updateStatus, getPost } from './db.js';
import { STATUS_SENT, STATUS_FAILED } from './constants.js';
import { TIMEZONE } from './config.js';

export async function checkAndDeliver() {
  const now = new Date();
  const currentTimestamp = now.getTime() / 1000;

  const duePosts = getDuePosts(currentTimestamp);

  for (const post of duePosts) {
    await deliverPost(post);
  }

  return duePosts.length;
}

async function deliverPost(post) {
  const postId = post.id;
  const sourceChannel = post.sourceChannel;
  const targetChannel = post.targetChannel;
  const messageIds = post.messageIds || [];

  if (messageIds.length === 0) {
    updateStatus(postId, STATUS_FAILED, 'No message IDs');
    return;
  }

  let successCount = 0;
  const failedIds = [];

  for (const msgId of messageIds) {
    try {
      await api.copyMessage({
        chat_id: targetChannel,
        from_chat_id: sourceChannel,
        message_id: msgId,
      });
      successCount++;
    } catch (e) {
      failedIds.push(msgId);
    }
  }

  if (successCount === 0) {
    updateStatus(postId, STATUS_FAILED, `Failed to copy all ${messageIds.length} messages`);
  } else {
    let details = `Copied ${successCount}/${messageIds.length} messages`;
    if (failedIds.length > 0) details += `, failed: ${failedIds.join(',')}`;
    updateStatus(postId, STATUS_SENT, null);
  }
}

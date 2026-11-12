// ============================================================================
// Database Operations
// ============================================================================
import { db } from 'sdk';
import { eq, and, desc, asc, lt, inArray } from 'sdk/db';
import {
  channels, admins, scheduledPosts, postHistory, settings
} from '../schema.js';
import {
  DEFAULT_HOURS, CHANNEL_SOURCE, CHANNEL_DESTINATION,
  STATUS_PENDING, STATUS_SENT, STATUS_DISABLED
} from './constants.js';

// ── Channels ────────────────────────────────────────────────────────────

export function getChannels(channelType = null, activeOnly = true) {
  if (channelType) {
    if (activeOnly) {
      return db.select().from(channels)
        .where(and(eq(channels.channelType, channelType), eq(channels.isActive, 1)))
        .all();
    }
    return db.select().from(channels)
      .where(eq(channels.channelType, channelType))
      .all();
  }
  if (activeOnly) {
    return db.select().from(channels)
      .where(eq(channels.isActive, 1))
      .all();
  }
  return db.select().from(channels).all();
}

export function getChannel(channelId) {
  return db.select().from(channels)
    .where(eq(channels.channelId, channelId))
    .get();
}

export function addChannel(channelId, title = '', username = '', channelType = CHANNEL_DESTINATION) {
  try {
    db.insert(channels).values({
      channelId, title, username, channelType
    }).run();
    return true;
  } catch {
    return false;
  }
}

export function removeChannel(channelId) {
  const result = db.delete(channels).where(eq(channels.channelId, channelId)).run();
  return (result.changes || 0) > 0;
}

// ── Admins ──────────────────────────────────────────────────────────────

export function getAdmins() {
  return db.select().from(admins).all();
}

export function getAdmin(userId) {
  return db.select().from(admins).where(eq(admins.userId, userId)).get();
}

export function addAdmin(userId, username = '', firstName = '') {
  try {
    db.insert(admins).values({ userId, username, firstName }).run();
    return true;
  } catch {
    return false;
  }
}

export function removeAdmin(userId) {
  const result = db.delete(admins).where(eq(admins.userId, userId)).run();
  return (result.changes || 0) > 0;
}

// ── Default Hours ───────────────────────────────────────────────────────

const HOURS_KEY = 'default_hours';

export function getDefaultHours() {
  const row = db.select().from(settings).where(eq(settings.key, HOURS_KEY)).get();
  if (row?.value) {
    try {
      return JSON.parse(row.value);
    } catch {
      return DEFAULT_HOURS;
    }
  }
  return DEFAULT_HOURS;
}

export function setDefaultHours(hours) {
  const sorted = [...hours].sort((a, b) => a - b);
  // Use insert with onConflictDoUpdate
  try {
    db.insert(settings).values({ key: HOURS_KEY, value: JSON.stringify(sorted) })
      .onConflictDoUpdate({ target: settings.key, set: { value: JSON.stringify(sorted) } })
      .run();
  } catch {
    // Fallback: delete and insert
    try {
      db.delete(settings).where(eq(settings.key, HOURS_KEY)).run();
      db.insert(settings).values({ key: HOURS_KEY, value: JSON.stringify(sorted) }).run();
    } catch {}
  }
}

export function addHour(hour) {
  const hours = getDefaultHours();
  if (hours.includes(hour)) return false;
  hours.push(hour);
  setDefaultHours(hours);
  return true;
}

export function removeHour(hour) {
  const hours = getDefaultHours();
  if (!hours.includes(hour)) return false;
  const filtered = hours.filter(h => h !== hour);
  setDefaultHours(filtered);
  return true;
}

// ── Scheduled Posts ─────────────────────────────────────────────────────

export function addPost(data) {
  const { chatId, userId, sourceChannel, sourceChannelTitle, messageIds,
    targetChannel, targetChannelTitle, scheduleDate, scheduleTime, scheduleTimestamp } = data;

  const result = db.insert(scheduledPosts).values({
    chatId, userId, sourceChannel, sourceChannelTitle,
    messageIds: JSON.stringify(messageIds),
    targetChannel, targetChannelTitle,
    scheduleDate, scheduleTime, scheduleTimestamp,
  }).returning().run();

  const postId = result[0]?.id || result.lastInsertRowid;

  // Add history
  if (postId) {
    db.insert(postHistory).values({
      postId,
      action: 'created',
      details: `Scheduled ${messageIds.length} message(s) for ${scheduleDate} ${scheduleTime}`,
      userId,
    }).run();
  }

  return postId;
}

export function getPost(postId) {
  const row = db.select().from(scheduledPosts).where(eq(scheduledPosts.id, postId)).get();
  if (row) {
    return { ...row, messageIds: JSON.parse(row.messageIds || '[]') };
  }
  return null;
}

export function getPendingPosts() {
  const rows = db.select().from(scheduledPosts)
    .where(eq(scheduledPosts.status, STATUS_PENDING))
    .orderBy(asc(scheduledPosts.scheduleTimestamp))
    .all();
  return rows.map(r => ({ ...r, messageIds: JSON.parse(r.messageIds || '[]') }));
}

export function getPostsByStatus(status, limit = 1000) {
  const rows = db.select().from(scheduledPosts)
    .where(eq(scheduledPosts.status, status))
    .orderBy(desc(scheduledPosts.scheduleTimestamp))
    .limit(limit)
    .all();
  return rows.map(r => ({ ...r, messageIds: JSON.parse(r.messageIds || '[]') }));
}

export function getDuePosts(currentTimestamp) {
  const rows = db.select().from(scheduledPosts)
    .where(and(
      eq(scheduledPosts.status, STATUS_PENDING),
      lt(scheduledPosts.scheduleTimestamp, currentTimestamp),
    ))
    .orderBy(asc(scheduledPosts.scheduleTimestamp))
    .all();
  return rows.map(r => ({ ...r, messageIds: JSON.parse(r.messageIds || '[]') }));
}

export function updateSchedule(postId, scheduleDate, scheduleTime, scheduleTimestamp) {
  db.update(scheduledPosts).set({
    scheduleDate, scheduleTime, scheduleTimestamp,
    updatedAt: new Date().toISOString(),
  }).where(eq(scheduledPosts.id, postId)).run();
}

export function updateStatus(postId, status, failedReason = null) {
  const updates = {
    status,
    updatedAt: new Date().toISOString(),
  };
  if (status === STATUS_SENT) {
    updates.sentAt = new Date().toISOString();
  } else {
    updates.failedReason = failedReason;
  }
  db.update(scheduledPosts).set(updates).where(eq(scheduledPosts.id, postId)).run();

  // Also add history entry
  const action = status === STATUS_SENT ? 'sent' : (status === STATUS_DISABLED ? 'disabled' : status);
  db.insert(postHistory).values({
    postId,
    action,
    details: failedReason || null,
  }).run();
}

export function updateTargetChannel(postId, channelId, channelTitle) {
  db.update(scheduledPosts).set({
    targetChannel: channelId,
    targetChannelTitle: channelTitle,
    updatedAt: new Date().toISOString(),
  }).where(eq(scheduledPosts.id, postId)).run();
}

export function deletePost(postId) {
  const result = db.delete(scheduledPosts).where(eq(scheduledPosts.id, postId)).run();
  return (result.changes || 0) > 0;
}

// ── History ─────────────────────────────────────────────────────────────

export function getHistory(limit = 50, offset = 0) {
  const rows = db.select().from(scheduledPosts)
    .where(inArray(scheduledPosts.status, [STATUS_SENT, 'failed']))
    .orderBy(desc(scheduledPosts.sentAt))
    .limit(limit)
    .offset(offset)
    .all();
  return rows.map(r => ({ ...r, messageIds: JSON.parse(r.messageIds || '[]') }));
}

export function getHistoryCount() {
  const rows = db.select().from(scheduledPosts)
    .where(inArray(scheduledPosts.status, [STATUS_SENT, 'failed']))
    .all();
  return rows.length;
}

export function addHistoryLog(postId, action, details = null, userId = null) {
  db.insert(postHistory).values({
    postId, action, details, userId,
  }).run();
}

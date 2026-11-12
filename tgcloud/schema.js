// ============================================================================
// Database Schema — Telegram Serverless (SQLite-backed)
// ============================================================================
import { table, integer, text, real } from 'sdk/db';

// کانال‌ها (مبدأ و مقصد)
export const channels = table('channels', {
  channelId:   text('channel_id').primaryKey(),
  title:       text('title').default(''),
  username:    text('username').default(''),
  channelType: text('channel_type').notNull().default('destination'), // 'source' | 'destination'
  addedAt:     text('added_at').notNull().default('(datetime(\'now\'))'),
  isActive:    integer('is_active').notNull().default(1),
});

// ادمین‌ها
export const admins = table('admins', {
  userId:    integer('user_id').primaryKey(),
  username:  text('username').default(''),
  firstName: text('first_name').default(''),
  addedAt:   text('added_at').notNull().default('(datetime(\'now\'))'),
});

// پست‌های زمان‌بندی‌شده
export const scheduledPosts = table('scheduled_posts', {
  id:                  integer('id').primaryKey({ autoIncrement: true }),
  chatId:              integer('chat_id').notNull(),
  userId:              integer('user_id').notNull(),
  sourceChannel:       text('source_channel').notNull(),
  sourceChannelTitle:  text('source_channel_title').default(''),
  messageIds:          text('message_ids').notNull().default('[]'), // JSON array
  targetChannel:       text('target_channel').notNull(),
  targetChannelTitle:  text('target_channel_title').default(''),
  scheduleDate:        text('schedule_date').notNull(),
  scheduleTime:        text('schedule_time').notNull(),
  scheduleTimestamp:   real('schedule_timestamp').notNull(),
  status:              text('status').notNull().default('pending'),
  // pending | sent | failed | disabled
  sentAt:              text('sent_at'),
  failedReason:        text('failed_reason'),
  createdAt:           text('created_at').notNull().default('(datetime(\'now\'))'),
  updatedAt:           text('updated_at').notNull().default('(datetime(\'now\'))'),
});

// لاگ تاریخچه
export const postHistory = table('post_history', {
  id:        integer('id').primaryKey({ autoIncrement: true }),
  postId:    integer('post_id').notNull(),
  action:    text('action').notNull(),
  details:   text('details'),
  userId:    integer('user_id'),
  createdAt: text('created_at').notNull().default('(datetime(\'now\'))'),
});

// تنظیمات عمومی (مثل default_hours)
export const settings = table('settings', {
  key:   text('key').primaryKey(),
  value: text('value').notNull(),
});

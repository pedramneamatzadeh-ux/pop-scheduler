// ============================================================================
// Conversation State Manager
// ============================================================================
// Telegram Serverless doesn't have a built-in conversation store,
// so we use a simple in-memory map. Since each invocation is isolated,
// we persist state to the database when needed.
//
// Strategy: Store the current conversation state + data in a table.
// Keyed by userId.

import { db } from 'sdk';
import { sql } from 'sdk/db';

// Ensure the state table exists
let tableReady = false;

async function ensureTable() {
  if (tableReady) return;
  try {
    db.execute(`
      CREATE TABLE IF NOT EXISTS conversation_state (
        user_id INTEGER PRIMARY KEY,
        state TEXT NOT NULL DEFAULT 'none',
        data TEXT NOT NULL DEFAULT '{}'
      )
    `);
    tableReady = true;
  } catch (e) {
    // Table might already exist
    tableReady = true;
  }
}

export async function getSession(userId) {
  await ensureTable();
  const row = db.execute(`SELECT state, data FROM conversation_state WHERE user_id = ${userId}`).get?.();
  if (row) {
    try {
      return { state: row.state, data: JSON.parse(row.data) };
    } catch {
      return { state: 'none', data: {} };
    }
  }
  return { state: 'none', data: {} };
}

export async function setSession(userId, state, data = {}) {
  await ensureTable();
  db.execute(`
    INSERT OR REPLACE INTO conversation_state (user_id, state, data)
    VALUES (${userId}, '${state}', '${JSON.stringify(data)}')
  `);
}

export async function clearSession(userId) {
  await ensureTable();
  db.execute(`DELETE FROM conversation_state WHERE user_id = ${userId}`);
}

export async function getState(userId) {
  const session = await getSession(userId);
  return session.state;
}

export async function setState(userId, state) {
  const session = await getSession(userId);
  await setSession(userId, state, session.data);
}

export async function getData(userId) {
  const session = await getSession(userId);
  return session.data;
}

export async function setData(userId, data) {
  const session = await getSession(userId);
  await setSession(userId, session.state, { ...session.data, ...data });
}

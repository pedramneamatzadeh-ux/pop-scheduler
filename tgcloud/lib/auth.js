// ============================================================================
// Authorization Helpers
// ============================================================================
import { db } from 'sdk';
import { eq, and } from 'sdk/db';
import { admins } from '../schema.js';
import { OWNER_ID } from './config.js';

export function isOwner(userId) {
  return userId === OWNER_ID;
}

export async function isAdmin(userId) {
  if (userId === OWNER_ID) return true;
  const row = await db.select().from(admins).where(eq(admins.userId, userId)).get();
  return !!row;
}

export async function isAdminOrOwner(userId) {
  return userId === OWNER_ID || await isAdmin(userId);
}

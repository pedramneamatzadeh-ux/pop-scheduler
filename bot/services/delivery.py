"""
Delivery service — handles sending scheduled posts to channels.
Uses copy_message to forward without showing the original sender.
"""
import json
import logging
from telegram import Bot
from telegram.error import TelegramError, RetryAfter, BadRequest
from asyncio import sleep, Lock

from ..database import db
from ..constants import STATUS_SENT, STATUS_FAILED

logger = logging.getLogger(__name__)

# Global lock dictionary to prevent duplicate deliveries
_delivery_locks = {}


async def deliver_post(post_id: int):
    """
    Deliver a scheduled post to its target channel.
    Called by the scheduler when the post is due.
    Copies all messages from source channel to target channel.
    Uses a lock to prevent duplicate deliveries.
    """
    logger.info("=== DELIVER_POST CALLED for post_id=%d ===", post_id)
    
    # Get or create lock for this post_id
    if post_id not in _delivery_locks:
        _delivery_locks[post_id] = Lock()
    
    lock = _delivery_locks[post_id]
    
    # Try to acquire lock, if can't it means another delivery is in progress
    if lock.locked():
        logger.warning("Post %d delivery already in progress, skipping duplicate", post_id)
        return
    
    async with lock:
        post = db.get_post(post_id)
        if not post:
            logger.error("Post %d not found for delivery", post_id)
            return

        if post["status"] != "pending":
            logger.warning("Post %d is not pending (status=%s), skipping", post_id, post["status"])
            return

        source_channel = post["source_channel"]
        target_channel = post["target_channel"]
        message_ids = post.get("message_ids", [])

        logger.info("Post %d: source=%s, target=%s, message_ids=%s", post_id, source_channel, target_channel, message_ids)

        if not message_ids:
            logger.error("Post %d has no message IDs", post_id)
            db.update_status(post_id, STATUS_FAILED, failed_reason="No message IDs")
            return

        try:
            from ..application import bot_instance
            logger.info("bot_instance: %s", bot_instance)
            
            if not bot_instance:
                logger.error("Bot instance not available for post %d", post_id)
                db.update_status(post_id, STATUS_FAILED, failed_reason="Bot instance not available")
                return
            
            bot = bot_instance
            logger.info("Starting delivery for post %d", post_id)

            # Copy each message from source to target
            success_count = 0
            failed_ids = []
            max_retries = 3  # Maximum retry attempts per message

            for msg_id in message_ids:
                retry_count = 0
                success = False
                
                while retry_count < max_retries and not success:
                    try:
                        logger.info("Copying message %d from %s to %s (attempt %d/%d)", 
                                  msg_id, source_channel, target_channel, retry_count + 1, max_retries)
                        await bot.copy_message(
                            chat_id=target_channel,
                            from_chat_id=source_channel,
                            message_id=msg_id,
                        )
                        success_count += 1
                        logger.info("Successfully copied message %d", msg_id)
                        success = True
                    except TelegramError as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning("Failed to copy message %d (attempt %d/%d): %s. Retrying...", 
                                         msg_id, retry_count, max_retries, e)
                            await sleep(2)  # Wait 2 seconds before retry
                        else:
                            logger.error("Failed to copy message %d after %d attempts: %s. Stopping delivery.", 
                                       msg_id, max_retries, e)
                            failed_ids.append(msg_id)
                            break  # Stop delivery, don't continue with other messages

            if success_count == 0:
                # All failed
                reason = f"Failed to copy all {len(message_ids)} messages"
                db.update_status(post_id, STATUS_FAILED, failed_reason=reason)
                db.add_history_log(post_id, "failed", details=reason)
                logger.error("Post %d delivery failed: %s", post_id, reason)
            else:
                # Success (possibly partial)
                db.update_status(post_id, STATUS_SENT)
                details = f"Copied {success_count}/{len(message_ids)} messages"
                if failed_ids:
                    details += f", failed: {failed_ids}"
                db.add_history_log(post_id, "sent", details=details)
                logger.info("Post %d delivered: %s", post_id, details)

        except RetryAfter as e:
            logger.warning("Rate limited for post %d, retrying after %ds", post_id, e.retry_after)
            await sleep(e.retry_after)
            try:
                # Retry with remaining time
                for msg_id in message_ids:
                    try:
                        await bot.copy_message(
                            chat_id=target_channel,
                            from_chat_id=source_channel,
                            message_id=msg_id,
                        )
                    except Exception:
                        pass
                db.update_status(post_id, STATUS_SENT)
                db.add_history_log(post_id, "sent", details="Retry successful")
            except Exception as e2:
                db.update_status(post_id, STATUS_FAILED, failed_reason=str(e2))
                db.add_history_log(post_id, "failed", details=str(e2))

        except TelegramError as e:
            db.update_status(post_id, STATUS_FAILED, failed_reason=str(e))
            db.add_history_log(post_id, "failed", details=str(e))
            logger.error("Post %d delivery failed: %s", post_id, e)

        except Exception as e:
            db.update_status(post_id, STATUS_FAILED, failed_reason=str(e))
            db.add_history_log(post_id, "failed", details=str(e))
            logger.error("Post %d unexpected error: %s", post_id, e, exc_info=True)

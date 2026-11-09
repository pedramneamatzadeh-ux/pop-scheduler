"""
Delivery service — handles sending scheduled posts to channels.
Uses copy_message to forward without showing the original sender.
"""
import json
import logging
from telegram import Bot
from telegram.error import TelegramError, RetryAfter, BadRequest
from asyncio import sleep

from ..database import db
from ..constants import STATUS_SENT, STATUS_FAILED

logger = logging.getLogger(__name__)


async def deliver_post(post_id: int):
    """
    Deliver a scheduled post to its target channel.
    Called by the scheduler when the post is due.
    """
    post = db.get_post(post_id)
    if not post:
        logger.error("Post %d not found for delivery", post_id)
        return

    if post["status"] != "pending":
        logger.warning("Post %d is not pending (status=%s), skipping", post_id, post["status"])
        return

    target_channel = post["target_channel"]
    message_data = post["message_data"]
    content_type = post["content_type"]

    try:
        from ..application import bot_instance
        if not bot_instance:
            raise RuntimeError("Bot instance not available")

        await _send_by_type(bot_instance, target_channel, message_data, content_type)

        # Mark as sent
        db.update_status(post_id, STATUS_SENT)
        db.add_history_log(post_id, "sent", details=f"Sent to {target_channel}")
        logger.info("Post %d delivered successfully to %s", post_id, target_channel)

    except RetryAfter as e:
        logger.warning("Rate limited for post %d, retrying after %ds", post_id, e.retry_after)
        await sleep(e.retry_after)
        try:
            await _send_by_type(bot_instance, target_channel, message_data, content_type)
            db.update_status(post_id, STATUS_SENT)
            db.add_history_log(post_id, "sent", details=f"Sent to {target_channel} (retry)")
            logger.info("Post %d delivered on retry to %s", post_id, target_channel)
        except Exception as e2:
            db.update_status(post_id, STATUS_FAILED, failed_reason=str(e2))
            db.add_history_log(post_id, "failed", details=str(e2))
            logger.error("Post %d delivery failed on retry: %s", post_id, e2)

    except TelegramError as e:
        db.update_status(post_id, STATUS_FAILED, failed_reason=str(e))
        db.add_history_log(post_id, "failed", details=str(e))
        logger.error("Post %d delivery failed: %s", post_id, e)

    except Exception as e:
        db.update_status(post_id, STATUS_FAILED, failed_reason=str(e))
        db.add_history_log(post_id, "failed", details=str(e))
        logger.error("Post %d unexpected error: %s", post_id, e, exc_info=True)


async def _send_by_type(bot: Bot, chat_id: str, data: dict, content_type: str):
    """Send message based on content type."""
    text = data.get("text", "")

    if content_type == "photo":
        await bot.send_photo(
            chat_id=chat_id,
            photo=data["file_id"],
            caption=text if text else None,
            parse_mode=data.get("parse_mode"),
        )

    elif content_type == "video":
        await bot.send_video(
            chat_id=chat_id,
            video=data["file_id"],
            caption=text if text else None,
            parse_mode=data.get("parse_mode"),
        )

    elif content_type == "document":
        await bot.send_document(
            chat_id=chat_id,
            document=data["file_id"],
            caption=text if text else None,
            parse_mode=data.get("parse_mode"),
        )

    elif content_type == "animation":
        await bot.send_animation(
            chat_id=chat_id,
            animation=data["file_id"],
            caption=text if text else None,
            parse_mode=data.get("parse_mode"),
        )

    elif content_type == "audio":
        await bot.send_audio(
            chat_id=chat_id,
            audio=data["file_id"],
            caption=text if text else None,
            parse_mode=data.get("parse_mode"),
        )

    elif content_type == "voice":
        await bot.send_voice(
            chat_id=chat_id,
            voice=data["file_id"],
            caption=text if text else None,
            parse_mode=data.get("parse_mode"),
        )

    elif content_type == "video_note":
        await bot.send_video_note(
            chat_id=chat_id,
            video_note=data["file_id"],
        )

    elif content_type == "sticker":
        await bot.send_sticker(
            chat_id=chat_id,
            sticker=data["file_id"],
        )

    elif content_type == "text":
        if text:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=data.get("parse_mode"),
            )
        else:
            raise ValueError("Empty text message")

    else:
        # Fallback: try send_message
        if text:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=data.get("parse_mode"),
            )
        else:
            raise ValueError(f"Unknown content type: {content_type}")


async def send_copy(bot: Bot, from_chat_id: int, message_id: int, to_chat_id: str) -> bool:
    """
    Copy a message from one chat to another (hides the original sender).
    Uses copyMessage Telegram Bot API.
    """
    try:
        await bot.copy_message(
            chat_id=to_chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )
        return True
    except TelegramError as e:
        logger.error("Failed to copy message %d: %s", message_id, e)
        return False

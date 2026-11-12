"""
History handler — view post delivery history.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from ..constants import (
    Msg, VIEW_HISTORY, MAIN_MENU, STATUS_LABELS,
)
from ..keyboards import history_keyboard, main_menu
from ..config import config
from ..database import db
from ..utils import format_history_item, paginate, is_admin_or_owner, format_message_ids

logger = logging.getLogger(__name__)

HISTORY_PER_PAGE = 5


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Show delivery history."""
    history = db.get_history(limit=1000)

    if not history:
        msg = Msg.NO_HISTORY
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, reply_markup=None)
        else:
            await update.message.reply_text(msg, reply_markup=None)
        return

    page_items, total_pages = paginate(history, page, HISTORY_PER_PAGE)

    items_text = "\n\n".join(format_history_item(p) for p in page_items)
    text = Msg.HISTORY_LIST.format(page=page + 1, total=total_pages, items=items_text)

    keyboard = history_keyboard(page_items, page, total_pages)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
        except BadRequest as e:
            if "not modified" not in str(e).lower():
                raise
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


async def history_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for history."""
    from ..decorators import _check_due_posts
    await _check_due_posts()
    
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if not is_admin_or_owner(user_id):
        await query.answer(Msg.ACCESS_DENIED, show_alert=True)
        return VIEW_HISTORY

    if data == "main_menu":
        context.user_data.clear()
        await query.answer()
        await query.edit_message_text(Msg.WELCOME, reply_markup=None, parse_mode="HTML")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=Msg.WELCOME,
            reply_markup=main_menu(user_id, is_owner=(user_id == config.OWNER_ID)),
            parse_mode="HTML"
        )
        return MAIN_MENU

    if data.startswith("pg:history:"):
        page = int(data.split(":")[2])
        await query.answer()
        await show_history(update, context, page=page)
        return VIEW_HISTORY

    if data.startswith("hpost:"):
        post_id = int(data.split(":")[1])
        await query.answer()
        return await _show_history_detail(query, post_id)

    if data == "noop":
        await query.answer()
        return VIEW_HISTORY

    await query.answer()
    return VIEW_HISTORY


async def _show_history_detail(query, post_id: int):
    """Show detail of a history item."""
    post = db.get_post(post_id)
    if not post:
        await query.edit_message_text("❌ پست پیدا نشد")
        return VIEW_HISTORY

    status_label = STATUS_LABELS.get(post["status"], post["status"])
    message_ids = post.get("message_ids", [])

    text = Msg.POST_DETAIL.format(
        post_id=post["id"],
        source=post.get("source_channel_title") or post.get("source_channel", "نامشخص"),
        message_ids=format_message_ids(message_ids),
        count=len(message_ids),
        target=post.get("target_channel_title") or post["target_channel"],
        date=post["schedule_date"],
        time=post["schedule_time"],
        status=status_label,
        created_at=post.get("created_at", "نامشخص"),
    )

    # Add sent_at info for history
    if post.get("sent_at"):
        text += f"\n🕐 ارسال: {post['sent_at']}"
    if post.get("failed_reason"):
        text += f"\n⚠️ دلیل خطا: {post['failed_reason']}"

    from ..keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🔄 ارسال مجدد", callback_data=f"resend:{post_id}")],
        [InlineKeyboardButton(text="📋 بازگشت", callback_data="back_to_history")],
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")],
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
    return VIEW_HISTORY

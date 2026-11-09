"""
Posts handler — manage scheduled (active) posts.
View, edit, delete, cancel scheduled posts.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

from ..constants import (
    Msg, MANAGE_POSTS, MANAGE_POST_DETAIL, EDIT_POST_DATE, EDIT_POST_TIME,
    EDIT_CUSTOM_TIME, MAIN_MENU, STATUS_PENDING, STATUS_LABELS,
)
from ..keyboards import post_list_keyboard, post_detail_keyboard, main_menu, cancel_keyboard
from ..config import OWNER_ID
from ..utils import (
    format_schedule_display, paginate, parse_date, parse_time, to_timestamp,
    is_admin_or_owner, now_tz, fmt_datetime, format_message_ids,
)
from ..database import db
from ..services.scheduler import scheduler

logger = logging.getLogger(__name__)

POSTS_PER_PAGE = 5


async def show_active_posts(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Show list of active scheduled posts."""
    posts = db.get_posts_by_status(STATUS_PENDING, limit=1000)

    if not posts:
        msg = Msg.NO_SCHEDULED_POSTS
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, reply_markup=None)
        else:
            await update.message.reply_text(msg, reply_markup=None)
        return

    page_items, total_pages = paginate(posts, page, POSTS_PER_PAGE)

    # Format items
    items_text = "\n\n".join(format_schedule_display(p) for p in page_items)
    text = Msg.SCHEDULED_LIST.format(page=page + 1, total=total_pages, items=items_text)

    keyboard = post_list_keyboard(page_items, page, total_pages)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
        except BadRequest as e:
            if "not modified" not in str(e).lower():
                raise
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


async def posts_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for posts management."""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if not is_admin_or_owner(user_id):
        await query.answer(Msg.ACCESS_DENIED, show_alert=True)
        return MANAGE_POSTS

    if data == "main_menu":
        context.user_data.clear()
        await query.answer()
        await query.edit_message_text(Msg.WELCOME, reply_markup=None, parse_mode="HTML")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=Msg.WELCOME,
            reply_markup=main_menu(user_id, is_owner=(user_id == OWNER_ID)),
            parse_mode="HTML"
        )
        return MAIN_MENU

    if data == "back_to_list":
        await query.answer()
        await show_active_posts(update, context, page=context.user_data.get("posts_page", 0))
        return MANAGE_POSTS

    if data.startswith("pg:posts:"):
        page = int(data.split(":")[2])
        context.user_data["posts_page"] = page
        await query.answer()
        await show_active_posts(update, context, page=page)
        return MANAGE_POSTS

    if data.startswith("post:"):
        post_id = int(data.split(":")[1])
        await query.answer()
        return await _show_post_detail(query, context, post_id)

    if data == "noop":
        await query.answer()
        return MANAGE_POSTS

    if data.startswith("del:"):
        post_id = int(data.split(":")[1])
        await query.answer("🗑 حذف...")
        scheduler.remove_post(post_id)
        db.delete_post(post_id)
        db.add_history_log(post_id, "deleted", user_id=user_id)
        await query.edit_message_text(Msg.POST_DELETED)
        await show_active_posts(update, context, page=0)
        return MANAGE_POSTS

    if data.startswith("cancel_post:"):
        post_id = int(data.split(":")[1])
        await query.answer("❌ لغو...")
        scheduler.remove_post(post_id)
        from ..constants import STATUS_CANCELLED
        db.update_status(post_id, STATUS_CANCELLED)
        db.add_history_log(post_id, "cancelled", user_id=user_id)
        await query.edit_message_text(Msg.POST_CANCELLED_MSG)
        await show_active_posts(update, context, page=0)
        return MANAGE_POSTS

    if data.startswith("edit_date:"):
        post_id = int(data.split(":")[1])
        context.user_data["editing_post_id"] = post_id
        await query.answer()
        from ..keyboards import date_keyboard
        await query.edit_message_text(
            Msg.SELECT_DATE,
            reply_markup=date_keyboard(),
            parse_mode="HTML"
        )
        return EDIT_POST_DATE

    if data.startswith("edit_time:"):
        post_id = int(data.split(":")[1])
        context.user_data["editing_post_id"] = post_id
        await query.answer()
        hours = db.get_default_hours()
        from ..keyboards import time_keyboard
        await query.edit_message_text(
            Msg.SELECT_TIME,
            reply_markup=time_keyboard(hours),
            parse_mode="HTML"
        )
        return EDIT_POST_TIME

    if data.startswith("edit_ch:"):
        post_id = int(data.split(":")[1])
        context.user_data["editing_post_id"] = post_id
        await query.answer()
        channels = db.get_channels()
        from ..keyboards import channel_selection_keyboard
        await query.edit_message_text(
            Msg.SELECT_CHANNEL,
            reply_markup=channel_selection_keyboard(channels),
            parse_mode="HTML"
        )
        return MANAGE_POST_DETAIL

    if data.startswith("ch:") and "editing_post_id" in context.user_data:
        post_id = context.user_data["editing_post_id"]
        channel_id = data.replace("ch:", "")
        channel = db.get_channel(channel_id)
        channel_title = channel["title"] if channel else channel_id

        db.update_target_channel(post_id, channel_id, channel_title)
        db.add_history_log(post_id, "channel_changed", details=f"to {channel_title}", user_id=user_id)

        await query.answer("✅ کانال تغییر کرد")
        del context.user_data["editing_post_id"]
        return await _show_post_detail(query, context, post_id)

    if data.startswith("resend:"):
        post_id = int(data.split(":")[1])
        await query.answer("🔄 در حال ارسال مجدد...")
        post = db.get_post(post_id)
        if post:
            # Re-schedule for now + 30 seconds
            import time
            new_ts = time.time() + 30
            db.update_status(post_id, STATUS_PENDING)
            from ..constants import STATUS_PENDING
            db.update_schedule(post_id, post["schedule_date"], post["schedule_time"], new_ts)
            scheduler.schedule_post(post_id, new_ts)
            await query.edit_message_text("✅ پست مجدداً زمان‌بندی شد (۳۰ ثانیه دیگر)")
        return MANAGE_POSTS

    if data == "noop":
        await query.answer()
        return MANAGE_POSTS

    return MANAGE_POSTS


async def edit_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date editing callback."""
    query = update.callback_query
    post_id = context.user_data.get("editing_post_id")
    if not post_id:
        await query.answer()
        return MANAGE_POSTS

    date_str = query.data.replace("d:", "")

    if date_str == "custom":
        await query.answer()
        await query.edit_message_text(
            "📅 تاریخ را به فرمت <code>YYYY-MM-DD</code> وارد کن:",
            parse_mode="HTML"
        )
        return EDIT_POST_DATE

    await query.answer()

    parsed = parse_date(date_str)
    if not parsed:
        await query.edit_message_text(Msg.INVALID_DATE, parse_mode="HTML")
        return EDIT_POST_DATE

    today = now_tz().date()
    if parsed < today:
        await query.edit_message_text(Msg.DATE_IN_PAST, parse_mode="HTML")
        return EDIT_POST_DATE

    # Update post
    post = db.get_post(post_id)
    if post:
        old_time = parse_time(post["schedule_time"])
        new_timestamp = to_timestamp(parsed, old_time)
        db.update_schedule(post_id, date_str, post["schedule_time"], new_timestamp)
        scheduler.reschedule_post(post_id, new_timestamp)
        db.add_history_log(post_id, "date_changed", details=f"to {date_str}", user_id=query.from_user.id)

    await query.edit_message_text(Msg.POST_EDITED)
    return await _show_post_detail(query, context, post_id)


async def edit_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time editing callback."""
    query = update.callback_query
    post_id = context.user_data.get("editing_post_id")
    if not post_id:
        await query.answer()
        return MANAGE_POSTS

    time_str = query.data.replace("t:", "")

    if time_str == "custom":
        await query.answer()
        await query.edit_message_text(
            "🕐 ساعت را به فرمت <code>HH:MM</code> وارد کن:",
            parse_mode="HTML"
        )
        return EDIT_CUSTOM_TIME

    await query.answer()

    post = db.get_post(post_id)
    if post:
        old_date = parse_date(post["schedule_date"])
        new_time = parse_time(time_str)
        new_timestamp = to_timestamp(old_date, new_time)
        db.update_schedule(post_id, post["schedule_date"], time_str, new_timestamp)
        scheduler.reschedule_post(post_id, new_timestamp)
        db.add_history_log(post_id, "time_changed", details=f"to {time_str}", user_id=query.from_user.id)

    await query.edit_message_text(Msg.POST_EDITED)
    return await _show_post_detail(query, context, post_id)


async def edit_custom_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom date text input for editing."""
    if update.message.text == "❌ لغو":
        post_id = context.user_data.get("editing_post_id")
        context.user_data.pop("editing_post_id", None)
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(update.effective_user.id, is_owner=(update.effective_user.id == OWNER_ID))
        )
        return ConversationHandler.END

    parsed = parse_date(update.message.text)
    if not parsed:
        await update.message.reply_text(Msg.INVALID_DATE, parse_mode="HTML")
        return EDIT_POST_DATE

    today = now_tz().date()
    if parsed < today:
        await update.message.reply_text(Msg.DATE_IN_PAST, parse_mode="HTML")
        return EDIT_POST_DATE

    post_id = context.user_data.get("editing_post_id")
    post = db.get_post(post_id)
    if post:
        date_str = str(parsed)
        old_time = parse_time(post["schedule_time"])
        new_timestamp = to_timestamp(parsed, old_time)
        db.update_schedule(post_id, date_str, post["schedule_time"], new_timestamp)
        scheduler.reschedule_post(post_id, new_timestamp)
        db.add_history_log(post_id, "date_changed", details=f"to {date_str}", user_id=update.effective_user.id)

    await update.message.reply_text(Msg.POST_EDITED, reply_markup=None, parse_mode="HTML")
    return ConversationHandler.END


async def edit_custom_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom time text input for editing."""
    if update.message.text == "❌ لغو":
        post_id = context.user_data.get("editing_post_id")
        context.user_data.pop("editing_post_id", None)
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(update.effective_user.id, is_owner=(update.effective_user.id == OWNER_ID))
        )
        return ConversationHandler.END

    parsed = parse_time(update.message.text)
    if not parsed:
        await update.message.reply_text(Msg.INVALID_TIME, parse_mode="HTML")
        return EDIT_CUSTOM_TIME

    time_str = f"{parsed.hour:02d}:{parsed.minute:02d}"
    post_id = context.user_data.get("editing_post_id")
    post = db.get_post(post_id)
    if post:
        old_date = parse_date(post["schedule_date"])
        new_timestamp = to_timestamp(old_date, parsed)
        db.update_schedule(post_id, post["schedule_date"], time_str, new_timestamp)
        scheduler.reschedule_post(post_id, new_timestamp)
        db.add_history_log(post_id, "time_changed", details=f"to {time_str}", user_id=update.effective_user.id)

    await update.message.reply_text(Msg.POST_EDITED, reply_markup=None, parse_mode="HTML")
    return ConversationHandler.END


async def _show_post_detail(query, context, post_id: int):
    """Show post detail view."""
    post = db.get_post(post_id)
    if not post:
        await query.edit_message_text("❌ پست پیدا نشد")
        return MANAGE_POSTS

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

    keyboard = post_detail_keyboard(post_id, post["status"])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
    return MANAGE_POST_DETAIL

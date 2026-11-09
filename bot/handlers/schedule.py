"""
Schedule handler — the main flow for scheduling a new post.
Steps: receive post → select channel → select date → select time → confirm
"""
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

from ..constants import (
    Msg, AWAITING_POST, SELECT_CHANNEL, SELECT_DATE, SELECT_TIME,
    CUSTOM_TIME, CONFIRM_SCHEDULE, MAIN_MENU,
)
from ..keyboards import (
    channel_selection_keyboard, date_keyboard, time_keyboard,
    confirm_keyboard, cancel_keyboard, main_menu,
)
from ..config import OWNER_ID
from ..utils import (
    extract_message_data, parse_date, parse_time, to_timestamp,
    is_admin_or_owner, now_tz,
)
from ..database import db
from ..services.scheduler import scheduler

logger = logging.getLogger(__name__)


async def start_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the scheduling flow."""
    user_id = update.effective_user.id

    if not is_admin_or_owner(user_id):
        if update.callback_query:
            await update.callback_query.answer(Msg.ACCESS_DENIED, show_alert=True)
        else:
            await update.message.reply_text(Msg.ACCESS_DENIED)
        return ConversationHandler.END

    # Check if we have channels configured
    channels = db.get_channels()
    if not channels:
        msg = "❌ هیچ کانالی ثبت نشده. ابتدا از تنظیمات، کانال اضافه کن."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            Msg.SEND_POST,
            reply_markup=None,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            Msg.SEND_POST,
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )

    context.user_data.clear()
    return AWAITING_POST


async def receive_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the post content."""
    message = update.message

    # Check for cancel
    if message.text == "❌ لغو":
        context.user_data.clear()
        await message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(update.effective_user.id, is_owner=(update.effective_user.id == OWNER_ID))
        )
        return ConversationHandler.END

    # Extract message data
    msg_data, content_type = extract_message_data(message)

    # Store message info
    context.user_data["post_data"] = msg_data
    context.user_data["content_type"] = content_type
    context.user_data["original_chat_id"] = message.chat_id
    context.user_data["original_message_id"] = message.message_id

    # Show channel selection
    channels = db.get_channels()
    await message.reply_text(
        Msg.SELECT_CHANNEL,
        reply_markup=channel_selection_keyboard(channels),
        parse_mode="HTML"
    )
    return SELECT_CHANNEL


async def select_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel selection callback."""
    query = update.callback_query
    await query.answer()

    channel_id = query.data.replace("ch:", "")
    channel = db.get_channel(channel_id)
    channel_title = channel["title"] if channel else channel_id

    context.user_data["target_channel"] = channel_id
    context.user_data["target_channel_title"] = channel_title

    # Show date selection
    await query.edit_message_text(
        Msg.SELECT_DATE,
        reply_markup=date_keyboard(),
        parse_mode="HTML"
    )
    return SELECT_DATE


async def select_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date selection callback."""
    query = update.callback_query

    date_str = query.data.replace("d:", "")

    if date_str == "custom":
        await query.answer()
        await query.edit_message_text(
            "📅 تاریخ را به فرمت <code>YYYY-MM-DD</code> وارد کن:\n(مثال: <code>2026-12-25</code>)",
            parse_mode="HTML"
        )
        return SELECT_DATE

    await query.answer()

    # Parse the date
    parsed = parse_date(date_str)
    if not parsed:
        await query.edit_message_text(Msg.INVALID_DATE, parse_mode="HTML")
        return SELECT_DATE

    # Check if date is in the past
    today = now_tz().date()
    if parsed < today:
        await query.edit_message_text(Msg.DATE_IN_PAST, parse_mode="HTML")
        return SELECT_DATE

    context.user_data["schedule_date"] = date_str

    # Show time selection
    hours = db.get_default_hours()
    await query.edit_message_text(
        Msg.SELECT_TIME,
        reply_markup=time_keyboard(hours),
        parse_mode="HTML"
    )
    return SELECT_TIME


async def receive_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom date text input."""
    if update.message.text == "❌ لغو":
        context.user_data.clear()
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(update.effective_user.id, is_owner=(update.effective_user.id == OWNER_ID))
        )
        return ConversationHandler.END

    parsed = parse_date(update.message.text)
    if not parsed:
        await update.message.reply_text(Msg.INVALID_DATE, parse_mode="HTML")
        return SELECT_DATE

    today = now_tz().date()
    if parsed < today:
        await update.message.reply_text(Msg.DATE_IN_PAST, parse_mode="HTML")
        return SELECT_DATE

    context.user_data["schedule_date"] = str(parsed)

    hours = db.get_default_hours()
    await update.message.reply_text(
        Msg.SELECT_TIME,
        reply_markup=time_keyboard(hours),
        parse_mode="HTML"
    )
    return SELECT_TIME


async def select_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time selection callback."""
    query = update.callback_query

    time_str = query.data.replace("t:", "")

    if time_str == "custom":
        await query.answer()
        await query.edit_message_text(
            "🕐 ساعت را به فرمت <code>HH:MM</code> وارد کن:\n(مثال: <code>14:30</code>)",
            parse_mode="HTML"
        )
        return CUSTOM_TIME

    await query.answer()

    context.user_data["schedule_time"] = time_str

    # Show confirmation
    await _show_confirmation(query, context)
    return CONFIRM_SCHEDULE


async def receive_custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom time text input."""
    if update.message.text == "❌ لغو":
        context.user_data.clear()
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(update.effective_user.id, is_owner=(update.effective_user.id == OWNER_ID))
        )
        return ConversationHandler.END

    parsed = parse_time(update.message.text)
    if not parsed:
        await update.message.reply_text(Msg.INVALID_TIME, parse_mode="HTML")
        return CUSTOM_TIME

    time_str = f"{parsed.hour:02d}:{parsed.minute:02d}"
    context.user_data["schedule_time"] = time_str

    # Show confirmation
    channel = context.user_data.get("target_channel_title", "")
    date_str = context.user_data.get("schedule_date", "")
    msg = await update.message.reply_text(
        Msg.CONFIRM_POST.format(channel=channel, date=date_str, time=time_str),
        reply_markup=confirm_keyboard(),
        parse_mode="HTML"
    )
    context.user_data["confirm_message_id"] = msg.message_id
    return CONFIRM_SCHEDULE


async def confirm_schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle schedule confirmation."""
    query = update.callback_query

    if query.data == "confirm:no":
        await query.answer()
        context.user_data.clear()
        await query.edit_message_text(
            Msg.CANCELLED,
            reply_markup=None
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="از منوی زیر یک گزینه انتخاب کن:",
            reply_markup=main_menu(query.from_user.id, is_owner=(query.from_user.id == OWNER_ID))
        )
        return ConversationHandler.END

    if query.data != "confirm:yes":
        return CONFIRM_SCHEDULE

    await query.answer("⏳ در حال زمان‌بندی...")

    # Gather all data
    post_data = context.user_data.get("post_data", {})
    content_type = context.user_data.get("content_type", "text")
    target_channel = context.user_data.get("target_channel", "")
    target_channel_title = context.user_data.get("target_channel_title", "")
    schedule_date = context.user_data.get("schedule_date", "")
    schedule_time = context.user_data.get("schedule_time", "")

    # Calculate timestamp
    from ..utils import parse_date, parse_time, to_timestamp
    d = parse_date(schedule_date)
    t = parse_time(schedule_time)
    timestamp = to_timestamp(d, t)

    # Save to database
    post_id = db.add_post(
        chat_id=query.message.chat_id,
        user_id=query.from_user.id,
        message_data=post_data,
        content_type=content_type,
        target_channel=target_channel,
        target_channel_title=target_channel_title,
        schedule_date=schedule_date,
        schedule_time=schedule_time,
        schedule_timestamp=timestamp,
    )

    # Schedule the job
    scheduler.schedule_post(post_id, timestamp)

    # Show success
    await query.edit_message_text(
        Msg.SCHEDULED_SUCCESS.format(
            channel=target_channel_title,
            date=schedule_date,
            time=schedule_time,
            post_id=post_id,
        ),
        reply_markup=None,
        parse_mode="HTML"
    )

    # Send main menu as new message
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="از منوی زیر یک گزینه انتخاب کن:",
        reply_markup=main_menu(query.from_user.id, is_owner=(query.from_user.id == OWNER_ID))
    )

    context.user_data.clear()
    return ConversationHandler.END


async def _show_confirmation(query, context):
    """Show the confirmation screen."""
    channel = context.user_data.get("target_channel_title", "")
    date_str = context.user_data.get("schedule_date", "")
    time_str = context.user_data.get("schedule_time", "")

    await query.edit_message_text(
        Msg.CONFIRM_POST.format(channel=channel, date=date_str, time=time_str),
        reply_markup=confirm_keyboard(),
        parse_mode="HTML"
    )

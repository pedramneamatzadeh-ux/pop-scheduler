"""
Schedule handler — the main flow for scheduling a new post.
New flow:
1. Select source channel
2. Enter message IDs (single/range/multiple)
3. Select date/time (month/year/day/hour)
4. Select target channel
5. Confirm and save
"""
import logging
import calendar
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..constants import (
    Msg, MAIN_MENU,
    SELECT_SOURCE_CHANNEL, SELECT_MESSAGE_IDS, SELECT_DATETIME,
    INPUT_YEAR, INPUT_DAY, SELECT_TARGET_CHANNEL, CONFIRM_SCHEDULE,
    STATUS_LABELS, MONTH_NAMES, QUICK_HOURS,
)
from ..keyboards import (
    source_channels_keyboard, dest_channels_keyboard,
    datetime_keyboard, months_keyboard, hours_keyboard,
    cancel_keyboard, inline_cancel_keyboard, main_menu,
)
from ..config import OWNER_ID
from ..utils import (
    parse_message_ids, format_message_ids, to_timestamp,
    is_admin_or_owner, now_tz,
)
from ..database import db, CHANNEL_SOURCE, CHANNEL_DESTINATION
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

    # Check if we have source channels
    source_channels = db.get_channels(channel_type=CHANNEL_SOURCE)
    if not source_channels:
        msg = Msg.NO_SOURCE_CHANNELS
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            Msg.SELECT_SOURCE,
            reply_markup=source_channels_keyboard(source_channels),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            Msg.SELECT_SOURCE,
            reply_markup=source_channels_keyboard(source_channels),
            parse_mode="HTML"
        )

    context.user_data.clear()
    return SELECT_SOURCE_CHANNEL


async def select_source_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle source channel selection."""
    query = update.callback_query
    await query.answer()

    channel_id = query.data.replace("src:", "")
    channel = db.get_channel(channel_id)
    channel_title = channel["title"] if channel else channel_id

    context.user_data["source_channel"] = channel_id
    context.user_data["source_channel_title"] = channel_title

    # Edit the inline message to show confirmation (no buttons)
    await query.edit_message_text(
        f"✅ کانال مبدأ: <b>{channel_title}</b>\n\n"
        f"حالا آیدی پیام‌ها را وارد کن.\n\n"
        f"<b>فرمت‌های مجاز:</b>\n"
        f"• تکی: <code>10</code>\n"
        f"• بازه: <code>10-15</code> (از 10 تا 15)\n"
        f"• چندتایی: <code>10,13,17</code>\n"
        f"• ترکیبی: <code>10,13-15,17</code>",
        parse_mode="HTML"
    )
    return SELECT_MESSAGE_IDS


async def receive_message_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive message IDs input."""
    if update.message.text == "❌ لغو":
        context.user_data.clear()
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(update.effective_user.id, is_owner=(update.effective_user.id == OWNER_ID))
        )
        return ConversationHandler.END

    # Parse message IDs
    message_ids = parse_message_ids(update.message.text)
    if not message_ids:
        await update.message.reply_text(Msg.INVALID_MESSAGE_IDS, parse_mode="HTML")
        return SELECT_MESSAGE_IDS

    # Store message IDs
    context.user_data["message_ids"] = message_ids

    # Show confirmation and ask for datetime
    now = now_tz()
    current_year = now.year
    current_month = now.month
    current_day = now.day
    hours = db.get_default_hours()
    current_hour = hours[0] if hours else 12

    context.user_data["year"] = current_year
    context.user_data["month"] = current_month
    context.user_data["day"] = current_day
    context.user_data["hour"] = current_hour

    ids_text = format_message_ids(message_ids)
    source = context.user_data.get("source_channel_title", "")

    await update.message.reply_text(
        Msg.MESSAGE_IDS_CONFIRM.format(
            count=len(message_ids),
            ids_text=ids_text,
            source=source,
        ),
        reply_markup=datetime_keyboard(current_year, current_month, current_day, current_hour),
        parse_mode="HTML"
    )
    return SELECT_DATETIME


async def datetime_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle datetime selection callbacks."""
    query = update.callback_query
    data = query.data

    if data == "dt:month":
        await query.answer()
        current_month = context.user_data.get("month", now_tz().month)
        await query.edit_message_text(
            "🗓 <b>ماه را انتخاب کن:</b>",
            reply_markup=months_keyboard(current_month),
            parse_mode="HTML"
        )
        return SELECT_DATETIME

    if data == "dt:day":
        await query.answer()
        # Edit inline message to show prompt (no reply keyboard on inline)
        await query.edit_message_text(
            f"📆 <b>روز</b>\n\n"
            f"روز را وارد کن (مثال: <code>15</code>):\n\n"
            f"یا برای لغو دکمه زیر را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return INPUT_DAY

    if data == "dt:hour":
        await query.answer()
        hours = db.get_default_hours()
        current_hour = context.user_data.get("hour")
        await query.edit_message_text(
            Msg.SELECT_HOUR,
            reply_markup=hours_keyboard(hours, current_hour),
            parse_mode="HTML"
        )
        return SELECT_DATETIME

    if data == "dt:back":
        await query.answer()
        # Go back to main datetime view
        return await _show_datetime(query, context)

    if data == "dt:submit":
        await query.answer()
        # Validate datetime is in the future
        year = context.user_data.get("year")
        month = context.user_data.get("month")
        day = context.user_data.get("day")
        hour = context.user_data.get("hour")

        now = now_tz()
        try:
            timestamp = to_timestamp(year, month, day, hour)
            from datetime import datetime
            target_dt = datetime.fromtimestamp(timestamp, tz=now.tzinfo)
            if target_dt <= now:
                await query.edit_message_text(
                    "❌ تاریخ و ساعت در گذشته است. لطفاً زمان آینده‌ای انتخاب کن.",
                    reply_markup=datetime_keyboard(year, month, day, hour),
                    parse_mode="HTML"
                )
                return SELECT_DATETIME
        except (ValueError, OverflowError):
            await query.edit_message_text(
                "❌ تاریخ نامعتبر است.",
                reply_markup=datetime_keyboard(year, month, day, hour),
                parse_mode="HTML"
            )
            return SELECT_DATETIME

        # Check if we have destination channels
        dest_channels = db.get_channels(channel_type=CHANNEL_DESTINATION)
        if not dest_channels:
            await query.edit_message_text(Msg.NO_DEST_CHANNELS)
            return ConversationHandler.END

        # Show summary and ask for target channel
        message_ids = context.user_data.get("message_ids", [])
        ids_text = format_message_ids(message_ids)
        source = context.user_data.get("source_channel_title", "")

        from ..constants import MONTH_NAMES
        date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
        time_str = f"{hour:02d}:00"

        context.user_data["schedule_date"] = date_str
        context.user_data["schedule_time"] = time_str

        await query.edit_message_text(
            Msg.SCHEDULE_SUMMARY.format(
                source=source,
                ids=ids_text,
                count=len(message_ids),
                date=date_str,
                time=time_str,
            ),
            reply_markup=dest_channels_keyboard(dest_channels),
            parse_mode="HTML"
        )
        return SELECT_TARGET_CHANNEL

    if data.startswith("m:"):
        # Month selected
        month = int(data.replace("m:", ""))
        context.user_data["month"] = month
        await query.answer()
        return await _show_datetime(query, context)

    if data.startswith("h:"):
        # Hour selected
        hour = int(data.replace("h:", ""))
        context.user_data["hour"] = hour
        await query.answer()
        return await _show_datetime(query, context)

    if data == "cancel":
        # Cancel from inline keyboard during text input
        await query.answer()
        context.user_data.clear()
        await query.edit_message_text(Msg.CANCELLED)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=Msg.WELCOME,
            reply_markup=main_menu(query.from_user.id, is_owner=(query.from_user.id == OWNER_ID)),
            parse_mode="HTML"
        )
        return ConversationHandler.END

    await query.answer()
    return SELECT_DATETIME


async def input_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle day input."""
    if update.message.text == "❌ لغو":
        return await _show_datetime_from_text(update, context)

    text = update.message.text.strip()
    try:
        day = int(text)
        if day < 1 or day > 31:
            raise ValueError()

        # Validate day for the selected month/year
        year = context.user_data.get("year", now_tz().year)
        month = context.user_data.get("month", now_tz().month)
        max_day = calendar.monthrange(year, month)[1]
        if day > max_day:
            await update.message.reply_text(
                f"❌ ماه {month} حداکثر {max_day} روز دارد.",
                parse_mode="HTML"
            )
            return INPUT_DAY

        context.user_data["day"] = day
        return await _show_datetime_from_text(update, context)

    except ValueError:
        await update.message.reply_text(Msg.INVALID_DAY, parse_mode="HTML")
        return INPUT_DAY


async def select_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target channel selection."""
    query = update.callback_query
    data = query.data

    if data == "cancel":
        await query.answer()
        context.user_data.clear()
        await query.edit_message_text(Msg.CANCELLED)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=Msg.WELCOME,
            reply_markup=main_menu(query.from_user.id, is_owner=(query.from_user.id == OWNER_ID)),
            parse_mode="HTML"
        )
        return ConversationHandler.END

    if data.startswith("dst:"):
        await query.answer("⏳ در حال زمان‌بندی...")

        channel_id = data.replace("dst:", "")
        channel = db.get_channel(channel_id)
        channel_title = channel["title"] if channel else channel_id

        # Gather all data
        source_channel = context.user_data.get("source_channel", "")
        source_title = context.user_data.get("source_channel_title", "")
        message_ids = context.user_data.get("message_ids", [])
        year = context.user_data.get("year")
        month = context.user_data.get("month")
        day = context.user_data.get("day")
        hour = context.user_data.get("hour")
        schedule_date = context.user_data.get("schedule_date", "")
        schedule_time = context.user_data.get("schedule_time", "")

        # Calculate timestamp
        timestamp = to_timestamp(year, month, day, hour)

        # Save to database
        post_id = db.add_post(
            chat_id=query.message.chat_id,
            user_id=query.from_user.id,
            source_channel=source_channel,
            source_channel_title=source_title,
            message_ids=message_ids,
            target_channel=channel_id,
            target_channel_title=channel_title,
            schedule_date=schedule_date,
            schedule_time=schedule_time,
            schedule_timestamp=timestamp,
        )

        # Schedule the job
        scheduler.schedule_post(post_id, timestamp)

        # Show success
        await query.edit_message_text(
            Msg.SCHEDULED_SUCCESS.format(
                source=source_title,
                count=len(message_ids),
                target=channel_title,
                date=schedule_date,
                time=schedule_time,
                post_id=post_id,
            ),
            reply_markup=None,
            parse_mode="HTML"
        )

        # Send main menu
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="از منوی زیر یک گزینه انتخاب کن:",
            reply_markup=main_menu(query.from_user.id, is_owner=(query.from_user.id == OWNER_ID))
        )

        context.user_data.clear()
        return ConversationHandler.END

    return SELECT_TARGET_CHANNEL


async def _show_datetime(query, context):
    """Show the main datetime selection screen."""
    year = context.user_data.get("year")
    month = context.user_data.get("month")
    day = context.user_data.get("day")
    hour = context.user_data.get("hour")

    from ..constants import MONTH_NAMES
    date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
    time_str = f"{hour:02d}:00"

    await query.edit_message_text(
        Msg.SELECT_DATETIME_MSG.format(date=date_str, time=time_str),
        reply_markup=datetime_keyboard(year, month, day, hour),
        parse_mode="HTML"
    )
    return SELECT_DATETIME


async def _show_datetime_from_text(update, context):
    """Show datetime screen from text input (no callback query)."""
    year = context.user_data.get("year")
    month = context.user_data.get("month")
    day = context.user_data.get("day")
    hour = context.user_data.get("hour")

    from ..constants import MONTH_NAMES
    date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
    time_str = f"{hour:02d}:00"

    await update.message.reply_text(
        Msg.SELECT_DATETIME_MSG.format(date=date_str, time=time_str),
        reply_markup=datetime_keyboard(year, month, day, hour),
        parse_mode="HTML"
    )
    return SELECT_DATETIME

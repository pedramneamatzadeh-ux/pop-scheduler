"""
Posts handler — manage scheduled (active) posts.
View, edit, delete, cancel scheduled posts.
"""
import logging
import calendar
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

from ..constants import (
    Msg, MANAGE_POSTS, MANAGE_POST_DETAIL, EDIT_POST_DATE, EDIT_POST_TIME,
    EDIT_CUSTOM_TIME, MAIN_MENU, STATUS_PENDING, STATUS_LABELS, MONTH_NAMES,
)
from ..keyboards import (
    post_list_keyboard, post_detail_keyboard, main_menu,
    datetime_keyboard, months_keyboard, hours_keyboard,
    dest_channels_keyboard, inline_cancel_keyboard,
)
from ..config import config
from ..utils import (
    format_schedule_display, paginate, to_timestamp,
    is_admin_or_owner, now_tz, format_message_ids,
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
            reply_markup=main_menu(user_id, is_owner=(user_id == config.OWNER_ID)),
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
        await query.answer("⏸ غیرفعال...")
        scheduler.remove_post(post_id)
        from ..constants import STATUS_CANCELLED
        db.update_status(post_id, STATUS_CANCELLED)
        db.add_history_log(post_id, "disabled", user_id=user_id)
        await query.edit_message_text(Msg.POST_CANCELLED_MSG)
        await show_active_posts(update, context, page=0)
        return MANAGE_POSTS

    # ── Edit date ───────────────────────────────────────────────────────────
    if data.startswith("edit_date:"):
        post_id = int(data.split(":")[1])
        context.user_data["editing_post_id"] = post_id
        await query.answer()
        # Parse current date from the post
        post = db.get_post(post_id)
        if post:
            now = now_tz()
            context.user_data["edit_year"] = now.year
            context.user_data["edit_month"] = now.month
            context.user_data["edit_day"] = now.day
            context.user_data["edit_hour"] = int(post["schedule_time"].split(":")[0])
        return await _show_edit_datetime(query, context)

    # ── Edit time ───────────────────────────────────────────────────────────
    if data.startswith("edit_time:"):
        post_id = int(data.split(":")[1])
        context.user_data["editing_post_id"] = post_id
        await query.answer()
        # Parse current time from the post
        post = db.get_post(post_id)
        if post:
            now = now_tz()
            try:
                # Try to parse existing date
                parts = post["schedule_date"].split()
                if len(parts) == 3:
                    day = int(parts[0])
                    month = _month_name_to_num(parts[1])
                    year = int(parts[2])
                else:
                    day = now.day
                    month = now.month
                    year = now.year
            except (ValueError, IndexError):
                day = now.day
                month = now.month
                year = now.year
            context.user_data["edit_year"] = year
            context.user_data["edit_month"] = month
            context.user_data["edit_day"] = day
            context.user_data["edit_hour"] = int(post["schedule_time"].split(":")[0])
        return await _show_edit_datetime(query, context)

    # ── Edit datetime callbacks ─────────────────────────────────────────────
    if data.startswith("edt:month"):
        await query.answer()
        current_month = context.user_data.get("edit_month", now_tz().month)
        await query.edit_message_text(
            "🗓 <b>ماه را انتخاب کن:</b>",
            reply_markup=months_keyboard(current_month, prefix="edm", back_callback="edt:back"),
            parse_mode="HTML"
        )
        return EDIT_POST_DATE

    if data.startswith("edt:day"):
        await query.answer()
        await query.edit_message_text(
            f"📆 <b>روز</b>\n\nروز را وارد کن (مثال: <code>15</code>):",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return EDIT_CUSTOM_TIME

    if data.startswith("edt:hour"):
        await query.answer()
        hours = db.get_default_hours()
        current_hour = context.user_data.get("edit_hour")
        await query.edit_message_text(
            "🕐 <b>ساعت</b>\n\nساعت ارسال را انتخاب کن:",
            reply_markup=hours_keyboard(hours, current_hour, prefix="edh", back_callback="edt:back"),
            parse_mode="HTML"
        )
        return EDIT_POST_TIME

    if data.startswith("edt:submit"):
        await query.answer()
        post_id = context.user_data.get("editing_post_id")
        year = context.user_data.get("edit_year")
        month = context.user_data.get("edit_month")
        day = context.user_data.get("edit_day")
        hour = context.user_data.get("edit_hour")

        if not post_id:
            await query.edit_message_text("❌ خطا: پست پیدا نشد")
            return MANAGE_POSTS

        # Validate
        now = now_tz()
        try:
            timestamp = to_timestamp(year, month, day, hour)
            from datetime import datetime
            target_dt = datetime.fromtimestamp(timestamp, tz=now.tzinfo)
            if target_dt <= now:
                await query.edit_message_text(
                    "❌ تاریخ و ساعت در گذشته است.",
                    reply_markup=datetime_keyboard(year, month, day, hour),
                    parse_mode="HTML"
                )
                return EDIT_POST_DATE
        except (ValueError, OverflowError):
            await query.edit_message_text(
                "❌ تاریخ نامعتبر است.",
                reply_markup=datetime_keyboard(year, month, day, hour),
                parse_mode="HTML"
            )
            return EDIT_POST_DATE

        # Update post
        date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
        time_str = f"{hour:02d}:00"
        db.update_schedule(post_id, date_str, time_str, timestamp)
        scheduler.reschedule_post(post_id, timestamp)
        db.add_history_log(post_id, "schedule_changed", details=f"to {date_str} {time_str}", user_id=user_id)

        context.user_data.pop("editing_post_id", None)
        context.user_data.pop("edit_year", None)
        context.user_data.pop("edit_month", None)
        context.user_data.pop("edit_day", None)
        context.user_data.pop("edit_hour", None)

        await query.edit_message_text(Msg.POST_EDITED)
        await show_active_posts(update, context, page=0)
        return MANAGE_POSTS

    if data.startswith("edm:"):
        # Month selected in edit mode
        month = int(data.replace("edm:", ""))
        context.user_data["edit_month"] = month
        await query.answer()
        return await _show_edit_datetime(query, context)

    if data.startswith("edh:"):
        # Hour selected in edit mode
        hour = int(data.replace("edh:", ""))
        context.user_data["edit_hour"] = hour
        await query.answer()
        return await _show_edit_datetime(query, context)

    if data.startswith("edt:back"):
        await query.answer()
        return await _show_edit_datetime(query, context)

    # ── Edit target channel ─────────────────────────────────────────────────
    if data.startswith("edit_ch:"):
        post_id = int(data.split(":")[1])
        context.user_data["editing_post_id"] = post_id
        await query.answer()
        dest_channels = db.get_channels(channel_type=db.CHANNEL_DESTINATION)
        if not dest_channels:
            await query.edit_message_text(Msg.NO_DEST_CHANNELS)
            return MANAGE_POSTS
        await query.edit_message_text(
            "📢 کانال مقصد جدید را انتخاب کن:",
            reply_markup=dest_channels_keyboard(dest_channels),
            parse_mode="HTML"
        )
        return MANAGE_POST_DETAIL

    if data.startswith("dst:") and "editing_post_id" in context.user_data:
        post_id = context.user_data["editing_post_id"]
        channel_id = data.replace("dst:", "")
        channel = db.get_channel(channel_id)
        channel_title = channel["title"] if channel else channel_id

        db.update_target_channel(post_id, channel_id, channel_title)
        db.add_history_log(post_id, "channel_changed", details=f"to {channel_title}", user_id=user_id)

        context.user_data.pop("editing_post_id", None)
        await query.answer("✅ کانال تغییر کرد")
        return await _show_post_detail(query, context, post_id)

    if data == "noop":
        await query.answer()
        return MANAGE_POSTS

    return MANAGE_POSTS


async def edit_custom_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle day text input for editing."""
    if update.message.text == "❌ لغو":
        # Go back to datetime picker
        return await _show_edit_datetime_from_text(update, context)

    text = update.message.text.strip()
    try:
        day = int(text)
        if day < 1 or day > 31:
            raise ValueError()

        year = context.user_data.get("edit_year", now_tz().year)
        month = context.user_data.get("edit_month", now_tz().month)
        max_day = calendar.monthrange(year, month)[1]
        if day > max_day:
            await update.message.reply_text(
                f"❌ ماه {month} حداکثر {max_day} روز دارد.",
                parse_mode="HTML"
            )
            return EDIT_CUSTOM_TIME

        context.user_data["edit_day"] = day
        return await _show_edit_datetime_from_text(update, context)

    except ValueError:
        await update.message.reply_text(
            "❌ روز نامعتبر. عدد بین 1 تا 31 وارد کن.",
            parse_mode="HTML"
        )
        return EDIT_CUSTOM_TIME


async def edit_custom_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom date text input (legacy fallback)."""
    return await edit_custom_time_input(update, context)


async def edit_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy fallback — redirect to main callback handler."""
    return await posts_callback_handler(update, context)


async def edit_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy fallback — redirect to main callback handler."""
    return await posts_callback_handler(update, context)


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


async def _show_edit_datetime(query, context):
    """Show datetime edit screen."""
    year = context.user_data.get("edit_year")
    month = context.user_data.get("edit_month")
    day = context.user_data.get("edit_day")
    hour = context.user_data.get("edit_hour")

    date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
    time_str = f"{hour:02d}:00"

    await query.edit_message_text(
        f"📅 <b>ویرایش تاریخ و ساعت</b>\n\n"
        f"📅 تاریخ: <b>{date_str}</b>\n"
        f"🕐 ساعت: <b>{time_str}</b>\n\n"
        f"روی هر دکمه کلیک کن تا تغییر دهی:",
        reply_markup=datetime_keyboard(year, month, day, hour, prefix="edt"),
        parse_mode="HTML"
    )
    return EDIT_POST_DATE


async def _show_edit_datetime_from_text(update, context):
    """Show datetime edit screen from text input."""
    year = context.user_data.get("edit_year")
    month = context.user_data.get("edit_month")
    day = context.user_data.get("edit_day")
    hour = context.user_data.get("edit_hour")

    date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
    time_str = f"{hour:02d}:00"

    await update.message.reply_text(
        f"📅 <b>ویرایش تاریخ و ساعت</b>\n\n"
        f"📅 تاریخ: <b>{date_str}</b>\n"
        f"🕐 ساعت: <b>{time_str}</b>\n\n"
        f"روی هر دکمه کلیک کن تا تغییر دهی:",
        reply_markup=datetime_keyboard(year, month, day, hour, prefix="edt"),
        parse_mode="HTML"
    )
    return EDIT_POST_DATE


def _month_name_to_num(name: str) -> int:
    """Convert month name to number."""
    for num, mname in MONTH_NAMES.items():
        if mname.lower() == name.lower():
            return num
    return now_tz().month

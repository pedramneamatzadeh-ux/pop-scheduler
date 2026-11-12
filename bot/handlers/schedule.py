"""
فلوی زمان‌بندی پست جدید.

مراحل:
1. انتخاب کانال مبدأ
2. وارد کردن آیدی پیام‌ها
3. انتخاب تاریخ و ساعت
4. انتخاب کانال مقصد
5. ذخیره و زمان‌بندی
"""
import logging
import calendar

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..config import config
from ..constants import (
    Msg,
    SELECT_SOURCE_CHANNEL,
    SELECT_MESSAGE_IDS,
    SELECT_DATETIME,
    INPUT_YEAR,
    INPUT_DAY,
    INPUT_HOUR,
    SELECT_TARGET_CHANNEL,
    MONTH_NAMES,
)
from ..database import db
from ..decorators import admin_required
from ..keyboards import (
    source_channels_keyboard,
    dest_channels_keyboard,
    datetime_keyboard,
    months_keyboard,
    hours_keyboard,
    inline_cancel_keyboard,
    main_menu,
)
from ..services.scheduler import scheduler
from ..utils import (
    parse_message_ids,
    format_message_ids,
    to_timestamp,
    now_tz,
    get_month_days,
    validate_hour_input,
)


logger = logging.getLogger(__name__)


@admin_required
async def start_schedule(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """شروع فلوی زمان‌بندی."""
    source_channels = db.get_channels(channel_type=db.CHANNEL_SOURCE)
    
    if not source_channels:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(Msg.NO_SOURCE_CHANNELS)
        else:
            await update.message.reply_text(Msg.NO_SOURCE_CHANNELS)
        return ConversationHandler.END
    
    context.user_data.clear()
    
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
    
    return SELECT_SOURCE_CHANNEL


async def select_source_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """انتخاب کانال مبدأ."""
    from ..decorators import _check_due_posts
    await _check_due_posts()
    
    query = update.callback_query
    await query.answer()
    
    channel_id = query.data.replace("src:", "")
    channel = db.get_channel(channel_id)
    channel_title = channel["title"] if channel else channel_id
    
    context.user_data["source_channel"] = channel_id
    context.user_data["source_channel_title"] = channel_title
    
    await query.edit_message_text(
        f"✅ کانال مبدأ: <b>{channel_title}</b>\n\n"
        f"{Msg.ENTER_MESSAGE_IDS}",
        parse_mode="HTML"
    )
    return SELECT_MESSAGE_IDS


async def receive_message_ids(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """دریافت آیدی پیام‌ها."""
    text = update.message.text.strip()
    
    # لغو
    if text == "❌ لغو":
        context.user_data.clear()
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(update.effective_user.id)
        )
        return ConversationHandler.END
    
    # تجزیه آیدی‌ها
    message_ids = parse_message_ids(text)
    if not message_ids:
        await update.message.reply_text(
            Msg.INVALID_MESSAGE_IDS,
            parse_mode="HTML"
        )
        return SELECT_MESSAGE_IDS  # بازگشت به همین state
    
    context.user_data["message_ids"] = message_ids
    
    # تنظیم مقادیر پیش‌فرض تاریخ و ساعت
    now = now_tz()
    hours = db.get_default_hours()
    
    context.user_data.update({
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": hours[0] if hours else 12,
    })
    
    ids_text = format_message_ids(message_ids)
    source = context.user_data.get("source_channel_title", "")
    
    await update.message.reply_text(
        Msg.MESSAGE_IDS_CONFIRM.format(
            count=len(message_ids),
            ids_text=ids_text,
            source=source,
        ),
        reply_markup=datetime_keyboard(
            now.year, now.month, now.day,
            context.user_data["hour"]
        ),
        parse_mode="HTML"
    )
    return SELECT_DATETIME


async def datetime_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """مدیریت callbackهای تاریخ و ساعت."""
    from ..decorators import _check_due_posts
    await _check_due_posts()
    
    query = update.callback_query
    data = query.data
    
    # ── انتخاب ماه ──────────────────────────────────────────────────────
    if data == "dt:month":
        await query.answer()
        current_month = context.user_data.get("month", now_tz().month)
        await query.edit_message_text(
            "🗓 <b>ماه را انتخاب کن:</b>",
            reply_markup=months_keyboard(current_month),
            parse_mode="HTML"
        )
        return SELECT_DATETIME
    
    # ── تأیید انتخاب ماه جدید (از months_keyboard) ──────────────────────
    if data.startswith("m:"):
        await query.answer()
        month = int(data.replace("m:", ""))
        context.user_data["month"] = month
        # اگر روز فعلی بیشتر از تعداد روزهای ماه جدید است، آن را اصلاح کن
        year = context.user_data.get("year", now_tz().year)
        max_day = get_month_days(year, month)
        current_day = context.user_data.get("day", 1)
        if current_day > max_day:
            context.user_data["day"] = max_day
        return await _show_datetime(query, context)
    
    # ── انتخاب سال ─────────────────────────────────────────────────────
    if data == "dt:year":
        await query.answer()
        await query.edit_message_text(
            "📅 <b>سال</b>\n\n"
            "سال را وارد کن (مثال: <code>2027</code>):\n\n"
            "یا برای لغو دکمه زیر را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return INPUT_YEAR
    
    # ── انتخاب روز ─────────────────────────────────────────────────────
    if data == "dt:day":
        await query.answer()
        year = context.user_data.get("year", now_tz().year)
        month = context.user_data.get("month", now_tz().month)
        max_day = get_month_days(year, month)
        month_name = MONTH_NAMES.get(month, str(month))
        
        await query.edit_message_text(
            f"📆 <b>روز</b>\n\n"
            f"ماه {month_name} از ۱ تا {max_day} روز دارد.\n\n"
            f"روز را وارد کن (مثال: <code>15</code>):\n\n"
            f"یا برای لغو دکمه زیر را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return INPUT_DAY
    
    # ── انتخاب ساعت ────────────────────────────────────────────────────
    if data == "dt:hour":
        await query.answer()
        hours = db.get_default_hours()
        current_hour = context.user_data.get("hour")
        
        await query.edit_message_text(
            "🕐 <b>ساعت</b>\n\n"
            "یکی از ساعت‌های پیش‌فرض را انتخاب کن یا ساعت دلخواه را "
            "به فرمت <code>HH:MM</code> وارد کن.\n\n"
            "(مثال: <code>14:30</code>)",
            reply_markup=hours_keyboard(hours, current_hour),
            parse_mode="HTML"
        )
        return INPUT_HOUR
    
    # ── بازگشت از انتخاب ماه/ساعت ──────────────────────────────────────
    if data == "dt:back":
        await query.answer()
        return await _show_datetime(query, context)
    
    # ── ثبت نهایی ──────────────────────────────────────────────────────
    if data == "dt:submit":
        await query.answer()
        
        year = context.user_data.get("year")
        month = context.user_data.get("month")
        day = context.user_data.get("day")
        hour = context.user_data.get("hour")
        minute = context.user_data.get("minute", 0)
        
        # اعتبارسنجی زمان آینده
        now = now_tz()
        try:
            timestamp = to_timestamp(year, month, day, hour, minute)
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
        
        # بررسی کانال‌های مقصد
        dest_channels = db.get_channels(channel_type=db.CHANNEL_DESTINATION)
        if not dest_channels:
            await query.edit_message_text(Msg.NO_DEST_CHANNELS)
            return ConversationHandler.END
        
        # نمایش خلاصه و انتخاب کانال مقصد
        message_ids = context.user_data.get("message_ids", [])
        ids_text = format_message_ids(message_ids)
        source = context.user_data.get("source_channel_title", "")
        
        date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
        time_str = f"{hour:02d}:{minute:02d}"
        
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
    
    # ── لغو ────────────────────────────────────────────────────────────
    if data == "cancel":
        await query.answer()
        context.user_data.clear()
        await query.edit_message_text(Msg.CANCELLED)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=Msg.WELCOME,
            reply_markup=main_menu(query.from_user.id),
            parse_mode="HTML"
        )
        return ConversationHandler.END
    
    await query.answer()
    return SELECT_DATETIME


async def input_year(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """دریافت ورودی سال."""
    text = update.message.text.strip()
    
    # لغو
    if text == "❌ لغو":
        return await _show_datetime_from_text(update, context)
    
    try:
        year = int(text)
        current_year = now_tz().year
        
        if year < current_year or year > current_year + 10:
            await update.message.reply_text(
                f"❌ سال باید بین {current_year} و {current_year + 10} باشد.\n\n"
                f"دوباره تلاش کن یا ❌ لغو را بزن.",
                reply_markup=inline_cancel_keyboard(),
                parse_mode="HTML"
            )
            return INPUT_YEAR  # بازگشت به همین state
        
        context.user_data["year"] = year
        return await _show_datetime_from_text(update, context)
    
    except ValueError:
        await update.message.reply_text(
            "❌ سال نامعتبر است. لطفاً یک عدد ۴ رقمی وارد کن.\n\n"
            "یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return INPUT_YEAR  # بازگشت به همین state


async def input_day(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """دریافت ورودی روز."""
    text = update.message.text.strip()
    
    # لغو
    if text == "❌ لغو":
        return await _show_datetime_from_text(update, context)
    
    try:
        day = int(text)
        if day < 1 or day > 31:
            raise ValueError()
        
        year = context.user_data.get("year", now_tz().year)
        month = context.user_data.get("month", now_tz().month)
        max_day = get_month_days(year, month)
        
        if day > max_day:
            month_name = MONTH_NAMES.get(month, str(month))
            await update.message.reply_text(
                f"❌ ماه {month_name} حداکثر {max_day} روز دارد.\n\n"
                f"دوباره تلاش کن یا ❌ لغو را بزن.",
                reply_markup=inline_cancel_keyboard(),
                parse_mode="HTML"
            )
            return INPUT_DAY  # بازگشت به همین state
        
        context.user_data["day"] = day
        return await _show_datetime_from_text(update, context)
    
    except ValueError:
        await update.message.reply_text(
            "❌ روز نامعتبر است. لطفاً عددی بین 1 و 31 وارد کن.\n\n"
            "یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return INPUT_DAY  # بازگشت به همین state


async def input_hour(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """دریافت ورودی ساعت (HH:MM یا انتخاب از دکمه‌ها)."""
    query = update.callback_query
    
    # اگر از callback (دکمه) آمده
    if query:
        data = query.data
        
        # درخواست ساعت دلخواه
        if data == "h:custom":
            await query.answer()
            await query.edit_message_text(
                "🕐 ساعت دلخواه را به فرمت <code>HH:MM</code> وارد کن.\n\n"
                "(مثال: <code>14:30</code>)\n\n"
                "یا ❌ لغو را بزن.",
                reply_markup=inline_cancel_keyboard(),
                parse_mode="HTML"
            )
            return INPUT_HOUR
        
        # انتخاب از دکمه‌های پیش‌فرض
        if data.startswith("h:"):
            await query.answer()
            hour = int(data.replace("h:", ""))
            context.user_data["hour"] = hour
            context.user_data["minute"] = 0  # ساعت‌های پیش‌فرض دقیقه 0 دارند
            return await _show_datetime(query, context)
        
        # بازگشت
        if data == "dt:back":
            await query.answer()
            return await _show_datetime(query, context)
        
        # لغو
        if data == "cancel":
            await query.answer()
            return await _show_datetime(query, context)
        
        await query.answer()
        return INPUT_HOUR
    
    # اگر از پیام متنی آمده
    text = update.message.text.strip()
    
    # لغو
    if text == "❌ لغو":
        return await _show_datetime_from_text(update, context)
    
    # اعتبارسنجی ساعت
    is_valid, hour, minute = validate_hour_input(text)
    
    if not is_valid:
        await update.message.reply_text(
            "❌ ساعت نامعتبر است.\n\n"
            "لطفاً به فرمت <code>HH:MM</code> وارد کن "
            "(مثال: <code>14:30</code>).\n\n"
            "یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return INPUT_HOUR  # بازگشت به همین state
    
    context.user_data["hour"] = hour
    context.user_data["minute"] = minute  # ذخیره دقیقه
    return await _show_datetime_from_text(update, context)


async def select_target_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """انتخاب کانال مقصد و ذخیره نهایی."""
    from ..decorators import _check_due_posts
    await _check_due_posts()
    
    query = update.callback_query
    data = query.data
    
    # لغو
    if data == "cancel":
        await query.answer()
        context.user_data.clear()
        await query.edit_message_text(Msg.CANCELLED)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=Msg.WELCOME,
            reply_markup=main_menu(query.from_user.id),
            parse_mode="HTML"
        )
        return ConversationHandler.END
    
    # انتخاب کانال مقصد
    if data.startswith("dst:"):
        await query.answer("⏳ در حال زمان‌بندی...")
        
        channel_id = data.replace("dst:", "")
        channel = db.get_channel(channel_id)
        channel_title = channel["title"] if channel else channel_id
        
        # جمع‌آوری داده‌ها
        source_channel = context.user_data.get("source_channel", "")
        source_title = context.user_data.get("source_channel_title", "")
        message_ids = context.user_data.get("message_ids", [])
        year = context.user_data.get("year")
        month = context.user_data.get("month")
        day = context.user_data.get("day")
        hour = context.user_data.get("hour")
        schedule_date = context.user_data.get("schedule_date", "")
        schedule_time = context.user_data.get("schedule_time", "")
        
        # محاسبه timestamp
        minute = context.user_data.get("minute", 0)
        timestamp = to_timestamp(year, month, day, hour, minute)
        
        # بررسی مجدد اینکه زمان در آینده هست
        from datetime import datetime as dt_class
        from ..utils import now_tz
        current_time = now_tz()
        target_time = dt_class.fromtimestamp(timestamp, tz=current_time.tzinfo)
        
        if target_time <= current_time:
            await query.edit_message_text(
                "❌ زمان انتخاب‌شده در گذشته است. لطفاً زمان آینده‌ای انتخاب کن.",
                reply_markup=None,
                parse_mode="HTML"
            )
            return ConversationHandler.END
        
        # ذخیره در دیتابیس
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
        
        # زمان‌بندی در scheduler
        scheduler.schedule_post(post_id, timestamp)
        
        # نمایش موفقیت
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
        
        # ارسال منوی اصلی
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=Msg.WELCOME,
            reply_markup=main_menu(query.from_user.id),
            parse_mode="HTML"
        )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    return SELECT_TARGET_CHANNEL


# ── توابع کمکی ──────────────────────────────────────────────────────────────


async def _show_datetime(query, context) -> int:
    """نمایش صفحه انتخاب تاریخ و ساعت."""
    year = context.user_data.get("year")
    month = context.user_data.get("month")
    day = context.user_data.get("day")
    hour = context.user_data.get("hour")
    minute = context.user_data.get("minute", 0)
    
    date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
    time_str = f"{hour:02d}:{minute:02d}"
    
    await query.edit_message_text(
        Msg.SELECT_DATETIME_MSG.format(date=date_str, time=time_str),
        reply_markup=datetime_keyboard(year, month, day, hour, minute),
        parse_mode="HTML"
    )
    return SELECT_DATETIME


async def _show_datetime_from_text(update, context) -> int:
    """نمایش صفحه انتخاب تاریخ و ساعت از ورودی متنی."""
    year = context.user_data.get("year")
    month = context.user_data.get("month")
    day = context.user_data.get("day")
    hour = context.user_data.get("hour")
    minute = context.user_data.get("minute", 0)
    
    date_str = f"{day} {MONTH_NAMES.get(month, month)} {year}"
    time_str = f"{hour:02d}:{minute:02d}"
    
    await update.message.reply_text(
        Msg.SELECT_DATETIME_MSG.format(date=date_str, time=time_str),
        reply_markup=datetime_keyboard(year, month, day, hour, minute),
        parse_mode="HTML"
    )
    return SELECT_DATETIME

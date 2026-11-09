"""
تنظیمات ربات (فقط مالک).

شامل:
- مدیریت کانال‌های مبدأ و مقصد
- مدیریت ادمین‌ها
- مدیریت ساعت‌های پیش‌فرض
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import TelegramError

from ..config import config
from ..constants import (
    Msg,
    SETTINGS_MENU,
    ADD_CHANNEL,
    ADD_ADMIN,
    CUSTOM_HOUR_INPUT,
    MAIN_MENU,
)
from ..database import db
from ..decorators import owner_only
from ..keyboards import (
    settings_keyboard,
    channels_type_keyboard,
    source_channels_manage_keyboard,
    dest_channels_manage_keyboard,
    hours_manage_keyboard,
    admins_manage_keyboard,
    main_menu,
    inline_cancel_keyboard,
)
from ..utils import validate_hour_input


logger = logging.getLogger(__name__)


@owner_only
async def show_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """نمایش منوی تنظیمات."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            Msg.SETTINGS_MENU_MSG,
            reply_markup=settings_keyboard(is_owner=True),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            Msg.SETTINGS_MENU_MSG,
            reply_markup=settings_keyboard(is_owner=True),
            parse_mode="HTML"
        )
    
    return SETTINGS_MENU


async def settings_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """مدیریت callbackهای تنظیمات."""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # فقط مالک
    if user_id != config.OWNER_ID:
        await query.answer(Msg.ACCESS_DENIED, show_alert=True)
        return ConversationHandler.END
    
    # ── بازگشت به منوی اصلی ────────────────────────────────────────────
    if data == "main_menu":
        await query.answer()
        context.user_data.clear()
        await query.edit_message_text(Msg.WELCOME, reply_markup=None, parse_mode="HTML")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=Msg.WELCOME,
            reply_markup=main_menu(user_id, is_owner=True),
            parse_mode="HTML"
        )
        return MAIN_MENU
    
    # ── بازگشت به منوی تنظیمات ─────────────────────────────────────────
    if data == "st:back":
        await query.answer()
        await query.edit_message_text(
            Msg.SETTINGS_MENU_MSG,
            reply_markup=settings_keyboard(is_owner=True),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── منوی کانال‌ها ───────────────────────────────────────────────────
    if data == "st:channels":
        await query.answer()
        await query.edit_message_text(
            Msg.CHANNELS_MENU,
            reply_markup=channels_type_keyboard(),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── کانال‌های مبدأ ──────────────────────────────────────────────────
    if data == "st:source_channels":
        await query.answer()
        channels = db.get_channels(channel_type=db.CHANNEL_SOURCE, active_only=False)
        
        if channels:
            ch_text = "\n".join(
                f"• {ch.get('title') or ch.get('username') or ch['channel_id']}"
                for ch in channels
            )
        else:
            ch_text = "(هیچ کانال مبدأ‌ای ثبت نشده)"
        
        await query.edit_message_text(
            Msg.SOURCE_CHANNELS_LIST.format(channels=ch_text),
            reply_markup=source_channels_manage_keyboard(channels),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── کانال‌های مقصد ──────────────────────────────────────────────────
    if data == "st:dest_channels":
        await query.answer()
        channels = db.get_channels(channel_type=db.CHANNEL_DESTINATION, active_only=False)
        
        if channels:
            ch_text = "\n".join(
                f"• {ch.get('title') or ch.get('username') or ch['channel_id']}"
                for ch in channels
            )
        else:
            ch_text = "(هیچ کانال مقصدی ثبت نشده)"
        
        await query.edit_message_text(
            Msg.DEST_CHANNELS_LIST.format(channels=ch_text),
            reply_markup=dest_channels_manage_keyboard(channels),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── افزودن کانال مبدأ ───────────────────────────────────────────────
    if data == "add_source":
        await query.answer()
        context.user_data["adding_channel_type"] = db.CHANNEL_SOURCE
        await query.edit_message_text(
            Msg.ENTER_CHANNEL_ID,
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return ADD_CHANNEL
    
    # ── افزودن کانال مقصد ───────────────────────────────────────────────
    if data == "add_dest":
        await query.answer()
        context.user_data["adding_channel_type"] = db.CHANNEL_DESTINATION
        await query.edit_message_text(
            Msg.ENTER_CHANNEL_ID,
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return ADD_CHANNEL
    
    # ── حذف کانال مبدأ ─────────────────────────────────────────────────
    if data.startswith("rmsrc:"):
        channel_id = data.replace("rmsrc:", "")
        channel = db.get_channel(channel_id)
        title = channel["title"] if channel else channel_id
        db.remove_channel(channel_id)
        await query.answer(f"🗑 {title} حذف شد")
        
        # نمایش مجدد لیست
        channels = db.get_channels(channel_type=db.CHANNEL_SOURCE, active_only=False)
        if channels:
            ch_text = "\n".join(
                f"• {ch.get('title') or ch.get('username') or ch['channel_id']}"
                for ch in channels
            )
        else:
            ch_text = "(هیچ کانال مبدأ‌ای ثبت نشده)"
        
        await query.edit_message_text(
            Msg.SOURCE_CHANNELS_LIST.format(channels=ch_text),
            reply_markup=source_channels_manage_keyboard(channels),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── حذف کانال مقصد ─────────────────────────────────────────────────
    if data.startswith("rmdst:"):
        channel_id = data.replace("rmdst:", "")
        channel = db.get_channel(channel_id)
        title = channel["title"] if channel else channel_id
        db.remove_channel(channel_id)
        await query.answer(f"🗑 {title} حذف شد")
        
        # نمایش مجدد لیست
        channels = db.get_channels(channel_type=db.CHANNEL_DESTINATION, active_only=False)
        if channels:
            ch_text = "\n".join(
                f"• {ch.get('title') or ch.get('username') or ch['channel_id']}"
                for ch in channels
            )
        else:
            ch_text = "(هیچ کانال مقصدی ثبت نشده)"
        
        await query.edit_message_text(
            Msg.DEST_CHANNELS_LIST.format(channels=ch_text),
            reply_markup=dest_channels_manage_keyboard(channels),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── ساعت‌های پیش‌فرض ────────────────────────────────────────────────
    if data == "st:hours":
        await query.answer()
        hours = db.get_default_hours()
        hours_text = "\n".join(f"• {h:02d}:00" for h in sorted(hours))
        
        await query.edit_message_text(
            Msg.DEFAULT_HOURS_MSG.format(hours=hours_text),
            reply_markup=hours_manage_keyboard(hours),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── افزودن ساعت ────────────────────────────────────────────────────
    if data == "add_hour":
        await query.answer()
        await query.edit_message_text(
            "🕐 ساعت مورد نظر را به فرمت <code>HH:MM</code> وارد کن.\n\n"
            "(مثال: <code>14:30</code>)\n\n"
            "یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return CUSTOM_HOUR_INPUT
    
    # ── حذف ساعت ──────────────────────────────────────────────────────
    if data.startswith("rmh:"):
        hour = int(data.replace("rmh:", ""))
        db.remove_hour(hour)
        await query.answer(f"🗑 {hour:02d}:00 حذف شد")
        
        # نمایش مجدد لیست
        hours = db.get_default_hours()
        hours_text = "\n".join(f"• {h:02d}:00" for h in sorted(hours))
        
        await query.edit_message_text(
            Msg.DEFAULT_HOURS_MSG.format(hours=hours_text),
            reply_markup=hours_manage_keyboard(hours),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── ادمین‌ها ────────────────────────────────────────────────────────
    if data == "st:admins":
        await query.answer()
        admins = db.get_admins()
        
        if admins:
            admin_text = "\n".join(
                f"• {a.get('first_name') or a.get('username') or ''} (<code>{a['user_id']}</code>)"
                for a in admins
            )
        else:
            admin_text = "(هیچ ادمینی ثبت نشده)"
        
        await query.edit_message_text(
            Msg.ADMINS_LIST.format(admins=admin_text),
            reply_markup=admins_manage_keyboard(admins),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    # ── افزودن ادمین ───────────────────────────────────────────────────
    if data == "add_admin":
        await query.answer()
        await query.edit_message_text(
            "👥 آیدی عددی ادمین جدید را وارد کن:\n\n"
            "یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return ADD_ADMIN
    
    # ── حذف ادمین ─────────────────────────────────────────────────────
    if data.startswith("rmadm:"):
        admin_id = int(data.replace("rmadm:", ""))
        if admin_id == config.OWNER_ID:
            await query.answer(Msg.ADMIN_IS_OWNER, show_alert=True)
            return SETTINGS_MENU
        
        admin = db.get_admin(admin_id)
        name = admin.get("first_name") or str(admin_id) if admin else str(admin_id)
        db.remove_admin(admin_id)
        await query.answer(f"🗑 {name} حذف شد")
        
        # نمایش مجدد لیست
        admins = db.get_admins()
        if admins:
            admin_text = "\n".join(
                f"• {a.get('first_name') or a.get('username') or ''} (<code>{a['user_id']}</code>)"
                for a in admins
            )
        else:
            admin_text = "(هیچ ادمینی ثبت نشده)"
        
        await query.edit_message_text(
            Msg.ADMINS_LIST.format(admins=admin_text),
            reply_markup=admins_manage_keyboard(admins),
            parse_mode="HTML"
        )
        return SETTINGS_MENU
    
    await query.answer()
    return SETTINGS_MENU


async def add_channel_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """دریافت آیدی کانال برای افزودن."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # لغو
    if text == "❌ لغو":
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(user_id, is_owner=True)
        )
        return ConversationHandler.END
    
    channel_type = context.user_data.get("adding_channel_type", db.CHANNEL_DESTINATION)
    
    try:
        channel_id = str(int(text))
        
        # برای کانال مقصد، بررسی عضویت ربات
        if channel_type == db.CHANNEL_DESTINATION:
            try:
                member = await context.bot.get_chat_member(channel_id, context.bot.id)
                if member.status not in ["administrator", "creator"]:
                    await update.message.reply_text(
                        Msg.BOT_NOT_IN_CHANNEL,
                        reply_markup=main_menu(user_id, is_owner=True)
                    )
                    return ConversationHandler.END
            except TelegramError:
                await update.message.reply_text(
                    Msg.BOT_NOT_IN_CHANNEL,
                    reply_markup=main_menu(user_id, is_owner=True)
                )
                return ConversationHandler.END
        
        # دریافت اطلاعات کانال
        try:
            chat = await context.bot.get_chat(channel_id)
            title = chat.title or ""
            username = chat.username or ""
            success = db.add_channel(
                channel_id=channel_id,
                title=title,
                username=username,
                channel_type=channel_type
            )
            channel_name = title or channel_id
        except TelegramError:
            if channel_type == db.CHANNEL_SOURCE:
                success = db.add_channel(
                    channel_id=channel_id,
                    title=channel_id,
                    channel_type=channel_type
                )
                channel_name = channel_id
            else:
                await update.message.reply_text(
                    Msg.BOT_NOT_IN_CHANNEL,
                    reply_markup=main_menu(user_id, is_owner=True)
                )
                return ConversationHandler.END
        
        if success:
            type_label = "مبدأ" if channel_type == db.CHANNEL_SOURCE else "مقصد"
            await update.message.reply_text(
                f"✅ کانال <b>{channel_name}</b> به عنوان کانال {type_label} اضافه شد.",
                reply_markup=main_menu(user_id, is_owner=True),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                Msg.CHANNEL_ALREADY_EXISTS,
                reply_markup=main_menu(user_id, is_owner=True)
            )
    
    except ValueError:
        await update.message.reply_text(
            "❌ آیدی نامعتبر. لطفاً عدد صحیح وارد کن.\n\n"
            "یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return ADD_CHANNEL  # بازگشت به همین state
    
    return ConversationHandler.END


async def add_admin_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """دریافت آیدی ادمین برای افزودن."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # لغو
    if text == "❌ لغو":
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(user_id, is_owner=True)
        )
        return ConversationHandler.END
    
    try:
        admin_id = int(text)
        
        if admin_id == config.OWNER_ID:
            await update.message.reply_text(
                "❌ مالک ربات به صورت خودکار ادمین است.\n\n"
                "آیدی دیگری وارد کن یا ❌ لغو را بزن.",
                reply_markup=inline_cancel_keyboard(),
                parse_mode="HTML"
            )
            return ADD_ADMIN  # بازگشت به همین state
        
        # دریافت اطلاعات کاربر
        try:
            chat = await context.bot.get_chat(admin_id)
            username = chat.username or ""
            first_name = chat.first_name or ""
            success = db.add_admin(user_id=admin_id, username=username, first_name=first_name)
        except TelegramError:
            success = db.add_admin(user_id=admin_id)
        
        if success:
            await update.message.reply_text(
                Msg.ADMIN_ADDED.format(admin_id=admin_id),
                reply_markup=main_menu(user_id, is_owner=True),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                Msg.ADMIN_ALREADY_EXISTS + "\n\nآیدی دیگری وارد کن یا ❌ لغو را بزن.",
                reply_markup=inline_cancel_keyboard(),
                parse_mode="HTML"
            )
            return ADD_ADMIN  # بازگشت به همین state
    
    except ValueError:
        await update.message.reply_text(
            "❌ آیدی نامعتبر. لطفاً عدد صحیح وارد کن.\n\n"
            "یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return ADD_ADMIN  # بازگشت به همین state
    
    return ConversationHandler.END


async def add_hour_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """دریافت ساعت برای افزودن (فرمت HH:MM)."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # لغو
    if text == "❌ لغو":
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(user_id, is_owner=True)
        )
        return ConversationHandler.END
    
    # اعتبارسنجی ساعت
    is_valid, hour, minute = validate_hour_input(text)
    
    if not is_valid:
        await update.message.reply_text(
            Msg.INVALID_HOUR + "\n\nدوباره تلاش کن یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return CUSTOM_HOUR_INPUT  # بازگشت به همین state
    
    success = db.add_hour(hour)
    
    if success:
        await update.message.reply_text(
            Msg.HOUR_ADDED.format(hour=hour),
            reply_markup=main_menu(user_id, is_owner=True),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            Msg.HOUR_ALREADY_EXISTS + "\n\nساعت دیگری وارد کن یا ❌ لغو را بزن.",
            reply_markup=inline_cancel_keyboard(),
            parse_mode="HTML"
        )
        return CUSTOM_HOUR_INPUT  # بازگشت به همین state
    
    return ConversationHandler.END

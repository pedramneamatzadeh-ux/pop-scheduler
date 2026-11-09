"""
Settings handler — manage channels, admins, default hours.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

from ..constants import (
    Msg, SETTINGS_MENU, ADD_CHANNEL, ADD_ADMIN, SET_DEFAULT_HOUR,
    CUSTOM_HOUR_INPUT, MAIN_MENU,
)
from ..keyboards import (
    settings_keyboard, channels_manage_keyboard, hours_manage_keyboard,
    admins_manage_keyboard, main_menu, cancel_keyboard,
)
from ..config import OWNER_ID
from ..utils import is_admin_or_owner, owner_only

logger = logging.getLogger(__name__)


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu."""
    user_id = update.effective_user.id
    is_owner = (user_id == OWNER_ID)

    text = Msg.SETTINGS_MENU_MSG
    keyboard = settings_keyboard(is_owner=is_owner)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")

    return SETTINGS_MENU


async def settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings callback queries."""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

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

    if data == "st:back":
        await query.answer()
        await show_settings(update, context)
        return SETTINGS_MENU

    if data == "st:channels":
        await query.answer()
        return await _show_channels(query, context)

    if data == "st:hours":
        await query.answer()
        return await _show_hours(query, context)

    if data == "st:admins":
        if user_id != OWNER_ID:
            await query.answer(Msg.ACCESS_DENIED, show_alert=True)
            return SETTINGS_MENU
        await query.answer()
        return await _show_admins(query, context)

    if data == "add_channel":
        await query.answer()
        await query.edit_message_text(
            "📢 آیدی عددی کانال را وارد کن:\n\n"
            "(مثال: <code>-1001234567890</code>)\n\n"
            "یا یک پیام از کانال به ربات فوروارد کن.",
            parse_mode="HTML"
        )
        return ADD_CHANNEL

    if data == "add_hour":
        await query.answer()
        await query.edit_message_text(
            "🕐 ساعت مورد نظر را وارد کن (0-23):",
            reply_markup=cancel_keyboard()
        )
        return CUSTOM_HOUR_INPUT

    if data == "add_admin":
        if user_id != OWNER_ID:
            await query.answer(Msg.ACCESS_DENIED, show_alert=True)
            return SETTINGS_MENU
        await query.answer()
        await query.edit_message_text(
            "👥 آیدی عددی ادمین جدید را وارد کن:",
            reply_markup=cancel_keyboard()
        )
        return ADD_ADMIN

    if data.startswith("rmch:"):
        channel_id = data.replace("rmch:", "")
        channel = db.get_channel(channel_id)
        title = channel["title"] if channel else channel_id
        db.remove_channel(channel_id)
        await query.answer(f"🗑 {title} حذف شد")
        return await _show_channels(query, context)

    if data.startswith("rmh:"):
        hour = int(data.replace("rmh:", ""))
        db.remove_hour(hour)
        await query.answer(f"🗑 {hour:02d}:00 حذف شد")
        return await _show_hours(query, context)

    if data.startswith("rmadm:"):
        admin_id = int(data.replace("rmadm:", ""))
        if admin_id == OWNER_ID:
            await query.answer(Msg.ADMIN_IS_OWNER, show_alert=True)
            return SETTINGS_MENU
        admin = db.get_admin(admin_id)
        name = admin.get("first_name") or str(admin_id) if admin else str(admin_id)
        db.remove_admin(admin_id)
        await query.answer(f"🗑 {name} حذف شد")
        return await _show_admins(query, context)

    await query.answer()
    return SETTINGS_MENU


async def add_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding a channel by ID or forwarded message."""
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text(Msg.ACCESS_DENIED)
        return ConversationHandler.END

    if update.message.text == "❌ لغو":
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(user_id, is_owner=True)
        )
        return ConversationHandler.END

    # Try to parse as channel ID
    text = update.message.text.strip()
    try:
        channel_id = str(int(text))
        # Try to get channel info
        try:
            chat = await context.bot.get_chat(channel_id)
            title = chat.title or ""
            username = chat.username or ""
            db.add_channel(channel_id=channel_id, title=title, username=username)
            await update.message.reply_text(
                Msg.CHANNEL_ADDED.format(channel=title or channel_id),
                reply_markup=main_menu(user_id, is_owner=True),
                parse_mode="HTML"
            )
        except Exception as e:
            # Channel might not be accessible yet
            db.add_channel(channel_id=channel_id, title=channel_id)
            await update.message.reply_text(
                Msg.CHANNEL_ADDED.format(channel=channel_id),
                reply_markup=main_menu(user_id, is_owner=True),
                parse_mode="HTML"
            )
    except ValueError:
        await update.message.reply_text(
            "❌ آیدی نامعتبر. لطفاً عدد صحیح وارد کن.",
            reply_markup=main_menu(user_id, is_owner=True)
        )

    return ConversationHandler.END


async def add_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding an admin by ID."""
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text(Msg.ACCESS_DENIED)
        return ConversationHandler.END

    if update.message.text == "❌ لغو":
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(user_id, is_owner=True)
        )
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        admin_id = int(text)
        if admin_id == OWNER_ID:
            await update.message.reply_text(
                "❌ مالک ربات به صورت خودکار ادمین است.",
                reply_markup=main_menu(user_id, is_owner=True)
            )
            return ConversationHandler.END

        # Try to get user info
        try:
            chat = await context.bot.get_chat(admin_id)
            username = chat.username or ""
            first_name = chat.first_name or ""
            success = db.add_admin(user_id=admin_id, username=username, first_name=first_name)
        except Exception:
            success = db.add_admin(user_id=admin_id)

        if success:
            await update.message.reply_text(
                Msg.ADMIN_ADDED.format(admin_id=admin_id),
                reply_markup=main_menu(user_id, is_owner=True),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                Msg.ADMIN_ALREADY_EXISTS,
                reply_markup=main_menu(user_id, is_owner=True)
            )
    except ValueError:
        await update.message.reply_text(
            "❌ آیدی نامعتبر. لطفاً عدد صحیح وارد کن.",
            reply_markup=main_menu(user_id, is_owner=True)
        )

    return ConversationHandler.END


async def add_hour_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding a custom hour."""
    user_id = update.effective_user.id
    is_owner = (user_id == OWNER_ID)

    if update.message.text == "❌ لغو":
        await update.message.reply_text(
            Msg.CANCELLED,
            reply_markup=main_menu(user_id, is_owner=is_owner)
        )
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        hour = int(text)
        if hour < 0 or hour > 23:
            raise ValueError()

        success = db.add_hour(hour)
        if success:
            await update.message.reply_text(
                Msg.HOUR_ADDED.format(hour=hour),
                reply_markup=main_menu(user_id, is_owner=is_owner),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                Msg.HOUR_ALREADY_EXISTS,
                reply_markup=main_menu(user_id, is_owner=is_owner)
            )
    except ValueError:
        await update.message.reply_text(
            Msg.INVALID_HOUR,
            reply_markup=main_menu(user_id, is_owner=is_owner)
        )

    return ConversationHandler.END


async def _show_channels(query, context):
    """Show channels management."""
    channels = db.get_channels(active_only=False)

    if channels:
        ch_text = "\n".join(
            f"• {ch.get('title') or ch.get('username') or ch['channel_id']}"
            for ch in channels
        )
    else:
        ch_text = "(هیچ کانالی ثبت نشده)"

    text = Msg.CHANNELS_LIST.format(channels=ch_text)
    keyboard = channels_manage_keyboard(channels)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
    return SETTINGS_MENU


async def _show_hours(query, context):
    """Show hours management."""
    hours = db.get_default_hours()

    hours_text = "\n".join(f"• {h:02d}:00" for h in sorted(hours))
    text = Msg.DEFAULT_HOURS_MSG.format(hours=hours_text)
    keyboard = hours_manage_keyboard(hours)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
    return SETTINGS_MENU


async def _show_admins(query, context):
    """Show admins management."""
    admins = db.get_admins()

    if admins:
        admin_text = "\n".join(
            f"• {a.get('first_name') or a.get('username') or ''} (<code>{a['user_id']}</code>)"
            for a in admins
        )
    else:
        admin_text = "(هیچ ادمینی ثبت نشده)"

    text = Msg.ADMINS_LIST.format(admins=admin_text)
    keyboard = admins_manage_keyboard(admins)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
    return SETTINGS_MENU

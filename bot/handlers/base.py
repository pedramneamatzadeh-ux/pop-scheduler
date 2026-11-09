"""
Base handlers — /start, main menu, cancel, error handler.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..constants import Msg, MAIN_MENU
from ..keyboards import main_menu, back_to_menu_keyboard
from ..config import OWNER_ID
from ..utils import is_admin_or_owner

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    user_id = user.id

    if not is_admin_or_owner(user_id):
        await update.message.reply_text(Msg.ACCESS_DENIED)
        return ConversationHandler.END

    # Clear any pending state
    context.user_data.clear()

    await update.message.reply_text(
        Msg.WELCOME,
        reply_markup=main_menu(user_id, is_owner=(user_id == OWNER_ID)),
        parse_mode="HTML"
    )
    return MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button presses."""
    text = update.message.text
    user_id = update.effective_user.id

    if text == "📅 زمان‌بندی جدید":
        # Will be handled by schedule conversation
        return None  # Let schedule handler take over

    elif text == "📋 پست‌های فعال":
        from .posts import show_active_posts
        await show_active_posts(update, context, page=0)
        return None

    elif text == "📊 تاریخچه":
        from .history import show_history
        await show_history(update, context, page=0)
        return None

    elif text == "⚙️ تنظیمات":
        from .settings import show_settings
        await show_settings(update, context)
        return None

    elif text in ("🏠 منوی اصلی", "/start"):
        context.user_data.clear()
        await update.message.reply_text(
            Msg.WELCOME,
            reply_markup=main_menu(user_id, is_owner=(user_id == OWNER_ID)),
            parse_mode="HTML"
        )
        return MAIN_MENU

    return MAIN_MENU


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    context.user_data.clear()
    user_id = update.effective_user.id

    await update.message.reply_text(
        Msg.CANCELLED,
        reply_markup=main_menu(user_id, is_owner=(user_id == OWNER_ID))
    )
    return ConversationHandler.END


async def go_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu (from callback queries)."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()

    user_id = query.from_user.id
    await query.edit_message_text(
        Msg.WELCOME,
        reply_markup=None,
        parse_mode="HTML"
    )
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=Msg.WELCOME,
        reply_markup=main_menu(user_id, is_owner=(user_id == OWNER_ID)),
        parse_mode="HTML"
    )
    return MAIN_MENU


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler — logs errors and notifies owner."""
    logger.error("Exception while handling update: %s", context.error, exc_info=context.error)

    # Notify owner
    try:
        if OWNER_ID:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"⚠️ <b>خطای غیرمنتظره:</b>\n\n<code>{str(context.error)[:500]}</code>",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error("Failed to notify owner of error: %s", e)

"""
Handlerهای پایه: /start, /cancel, منوی اصلی, و error handler.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..config import config
from ..constants import Msg
from ..database import db
from ..keyboards import main_menu


logger = logging.getLogger(__name__)


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """مدیریت دستور /start."""
    user = update.effective_user
    user_id = user.id
    
    # بررسی دسترسی
    is_owner = (user_id == config.OWNER_ID)
    is_admin = db.is_admin(user_id)
    
    if not is_owner and not is_admin:
        await update.message.reply_text(Msg.ACCESS_DENIED)
        return
    
    # پاک کردن state قبلی
    context.user_data.clear()
    
    await update.message.reply_text(
        Msg.WELCOME,
        reply_markup=main_menu(user_id, is_owner=is_owner),
        parse_mode="HTML"
    )


async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """مدیریت دستور /cancel."""
    context.user_data.clear()
    user_id = update.effective_user.id
    is_owner = (user_id == config.OWNER_ID)
    
    await update.message.reply_text(
        Msg.CANCELLED,
        reply_markup=main_menu(user_id, is_owner=is_owner)
    )
    return ConversationHandler.END


async def main_menu_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """مدیریت دکمه '🏠 منوی اصلی'."""
    user_id = update.effective_user.id
    is_owner = (user_id == config.OWNER_ID)
    context.user_data.clear()
    
    await update.message.reply_text(
        Msg.WELCOME,
        reply_markup=main_menu(user_id, is_owner=is_owner),
        parse_mode="HTML"
    )


async def go_to_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """بازگشت به منوی اصلی از callback."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    user_id = query.from_user.id
    is_owner = (user_id == config.OWNER_ID)
    
    # ویرایش پیام inline
    try:
        await query.edit_message_text(
            Msg.WELCOME,
            reply_markup=None,
            parse_mode="HTML"
        )
    except Exception:
        pass  # پیام ممکن است قدیمی باشد
    
    # ارسال پیام جدید با reply keyboard
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=Msg.WELCOME,
        reply_markup=main_menu(user_id, is_owner=is_owner),
        parse_mode="HTML"
    )


async def global_error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """مدیریت خطای سراسری."""
    logger.error(
        "Exception while handling update: %s",
        context.error,
        exc_info=context.error
    )
    
    # اطلاع به مالک
    try:
        if config.OWNER_ID:
            await context.bot.send_message(
                chat_id=config.OWNER_ID,
                text=f"⚠️ <b>خطای غیرمنتظره:</b>\n\n<code>{str(context.error)[:500]}</code>",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error("Failed to notify owner of error: %s", e)

"""
دکوراتورهای احراز هویت و دسترسی.
"""
import logging
from functools import wraps
from typing import Any, Callable

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .config import config
from .constants import Msg

logger = logging.getLogger(__name__)


async def _check_due_posts():
    """
    بررسی و ارسال پست‌های overdue.
    روی هر handler صدا زده می‌شه.
    """
    try:
        from .services.scheduler import scheduler
        await scheduler.check_due_posts_fallback()
    except Exception as e:
        logger.error("_check_due_posts error: %s", e)


def owner_only(func: Callable[..., Any]) -> Callable[..., Any]:
    """دکوراتور: فقط مالک ربات می‌تواند از این handler استفاده کند."""
    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # بررسی پست‌های overdue
        await _check_due_posts()
        
        user = update.effective_user

        if not user or config.OWNER_ID is None or user.id != config.OWNER_ID:
            if update.message:
                await update.message.reply_text(Msg.ACCESS_DENIED)
            elif update.callback_query:
                await update.callback_query.answer(
                    Msg.ACCESS_DENIED,
                    show_alert=True,
                )
            return ConversationHandler.END

        return await func(update, context, *args, **kwargs)

    return wrapper


def admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """دکوراتور: فقط ادمین‌ها و مالک می‌توانند از این handler استفاده کنند."""
    from .database import db
    
    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # بررسی پست‌های overdue
        await _check_due_posts()
        
        user = update.effective_user

        if not user:
            if update.message:
                await update.message.reply_text(Msg.ACCESS_DENIED)
            elif update.callback_query:
                await update.callback_query.answer(
                    Msg.ACCESS_DENIED,
                    show_alert=True,
                )
            return ConversationHandler.END

        # مالک همیشه دسترسی دارد
        if user.id == config.OWNER_ID:
            return await func(update, context, *args, **kwargs)

        # بررسی ادمین بودن
        if db.is_admin(user.id):
            return await func(update, context, *args, **kwargs)

        if update.message:
            await update.message.reply_text(Msg.ACCESS_DENIED)
        elif update.callback_query:
            await update.callback_query.answer(
                Msg.ACCESS_DENIED,
                show_alert=True,
            )
        return ConversationHandler.END

    return wrapper

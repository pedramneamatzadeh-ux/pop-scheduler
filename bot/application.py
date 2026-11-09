"""
سازنده Application و ثبت handlerها.
"""
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from .config import config
from .constants import (
    MAIN_MENU,
    SELECT_SOURCE_CHANNEL,
    SELECT_MESSAGE_IDS,
    SELECT_DATETIME,
    INPUT_YEAR,
    INPUT_DAY,
    INPUT_HOUR,
    SELECT_TARGET_CHANNEL,
    MANAGE_POSTS,
    MANAGE_POST_DETAIL,
    EDIT_POST_DATE,
    EDIT_POST_TIME,
    EDIT_CUSTOM_TIME,
    SETTINGS_MENU,
    ADD_CHANNEL,
    ADD_ADMIN,
    CUSTOM_HOUR_INPUT,
    VIEW_HISTORY,
)
from .handlers.base import (
    start_command,
    cancel_command,
    main_menu_handler,
    go_to_main_menu,
    global_error_handler,
)
from .handlers.schedule import (
    start_schedule,
    select_source_callback,
    receive_message_ids,
    datetime_callback,
    input_year,
    input_day,
    input_hour,
    select_target_callback,
)
from .handlers.posts import (
    show_active_posts,
    posts_callback_handler,
    edit_custom_time_input,
)
from .handlers.settings import (
    show_settings,
    settings_callback,
    add_channel_input,
    add_admin_input,
    add_hour_input,
)
from .handlers.history import (
    show_history,
    history_callback_handler,
)


logger = logging.getLogger(__name__)

# مرجع نمونه bot (در build تنظیم می‌شود)
bot_instance = None


def build_application() -> Application:
    """ساخت و پیکربندی Application."""
    builder = Application.builder().token(config.BOT_TOKEN)
    app = builder.build()
    
    global bot_instance
    bot_instance = app.bot
    
    # ── دستورات پایه ──────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    
    # ── Conversation: زمان‌بندی ───────────────────────────────────────
    schedule_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^📅 زمان‌بندی جدید$"),
                start_schedule
            ),
        ],
        states={
            SELECT_SOURCE_CHANNEL: [
                CallbackQueryHandler(select_source_callback, pattern=r"^src:"),
                CallbackQueryHandler(_cancel_inline, pattern=r"^cancel$"),
            ],
            SELECT_MESSAGE_IDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message_ids),
            ],
            SELECT_DATETIME: [
                CallbackQueryHandler(datetime_callback, pattern=r"^(dt:|m:|h:)"),
                CallbackQueryHandler(_cancel_inline, pattern=r"^cancel$"),
            ],
            INPUT_YEAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_year),
                CallbackQueryHandler(_cancel_year_inline, pattern=r"^cancel$"),
            ],
            INPUT_DAY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_day),
                CallbackQueryHandler(_cancel_day_inline, pattern=r"^cancel$"),
            ],
            INPUT_HOUR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_hour),
                CallbackQueryHandler(input_hour, pattern=r"^(h:.*|dt:back|cancel)$"),
            ],
            SELECT_TARGET_CHANNEL: [
                CallbackQueryHandler(select_target_callback),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel_command),
        ],
        allow_reentry=True,
    )
    app.add_handler(schedule_conv)
    
    # ── Conversation: مدیریت پست‌ها ──────────────────────────────────
    posts_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^📋 پست‌های فعال$"),
                _enter_posts
            ),
        ],
        states={
            MANAGE_POSTS: [
                CallbackQueryHandler(posts_callback_handler),
            ],
            MANAGE_POST_DETAIL: [
                CallbackQueryHandler(posts_callback_handler),
            ],
            EDIT_POST_DATE: [
                CallbackQueryHandler(posts_callback_handler, pattern=r"^(edt:|edm:)"),
                CallbackQueryHandler(_cancel_inline, pattern=r"^cancel$"),
            ],
            EDIT_POST_TIME: [
                CallbackQueryHandler(posts_callback_handler, pattern=r"^edh:"),
                CallbackQueryHandler(_cancel_inline, pattern=r"^cancel$"),
            ],
            EDIT_CUSTOM_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_custom_time_input),
                CallbackQueryHandler(posts_callback_handler, pattern=r"^edt:"),
                CallbackQueryHandler(_cancel_inline, pattern=r"^cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel_command),
        ],
        allow_reentry=True,
    )
    app.add_handler(posts_conv)
    
    # ── Conversation: تاریخچه ────────────────────────────────────────
    history_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^📊 تاریخچه$"),
                _enter_history
            ),
        ],
        states={
            VIEW_HISTORY: [
                CallbackQueryHandler(history_callback_handler),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel_command),
        ],
        allow_reentry=True,
    )
    app.add_handler(history_conv)
    
    # ── Conversation: تنظیمات ────────────────────────────────────────
    settings_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^⚙️ تنظیمات$"),
                show_settings
            ),
        ],
        states={
            SETTINGS_MENU: [
                CallbackQueryHandler(settings_callback),
            ],
            ADD_CHANNEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_input),
            ],
            ADD_ADMIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_input),
            ],
            CUSTOM_HOUR_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_hour_input),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel_command),
        ],
        allow_reentry=True,
    )
    app.add_handler(settings_conv)
    
    # ── Handler: دکمه منوی اصلی ──────────────────────────────────────
    app.add_handler(MessageHandler(
        filters.Regex("^🏠 منوی اصلی$"),
        main_menu_handler,
    ))
    
    # ── Handler: callback منوی اصلی ──────────────────────────────────
    app.add_handler(CallbackQueryHandler(go_to_main_menu, pattern=r"^main_menu$"))
    
    # ── Handler: خطای سراسری ─────────────────────────────────────────
    app.add_error_handler(global_error_handler)
    
    logger.info("Application built with %d handler groups", len(app.handlers))
    return app


async def _enter_posts(update, context):
    """ورود به مدیریت پست‌ها."""
    await show_active_posts(update, context, page=0)
    return MANAGE_POSTS


async def _enter_history(update, context):
    """ورود به تاریخچه."""
    await show_history(update, context, page=0)
    return VIEW_HISTORY


async def _cancel_inline(update, context):
    """لغو از کیبورد inline."""
    from .constants import Msg
    from .keyboards import main_menu
    
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    user_id = query.from_user.id
    is_owner = (user_id == config.OWNER_ID)
    
    await query.edit_message_text(Msg.CANCELLED, reply_markup=None)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=Msg.WELCOME,
        reply_markup=main_menu(user_id, is_owner=is_owner),
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def _cancel_year_inline(update, context):
    """لغو از ورود سال (بازگشت به صفحه تاریخ)."""
    from .handlers.schedule import _show_datetime
    query = update.callback_query
    await query.answer()
    return await _show_datetime(query, context)


async def _cancel_day_inline(update, context):
    """لغو از ورود روز (بازگشت به صفحه تاریخ)."""
    from .handlers.schedule import _show_datetime
    query = update.callback_query
    await query.answer()
    return await _show_datetime(query, context)

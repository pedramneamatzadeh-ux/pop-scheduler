"""
Application builder — wires up all handlers and creates the bot application.
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

from .constants import (
    MAIN_MENU,
    SELECT_SOURCE_CHANNEL, SELECT_MESSAGE_IDS, SELECT_DATETIME,
    INPUT_YEAR, INPUT_DAY, SELECT_TARGET_CHANNEL, CONFIRM_SCHEDULE,
    MANAGE_POSTS, MANAGE_POST_DETAIL, EDIT_POST_DATE, EDIT_POST_TIME, EDIT_CUSTOM_TIME,
    SETTINGS_MENU, ADD_CHANNEL, ADD_ADMIN, CUSTOM_HOUR_INPUT,
    VIEW_HISTORY,
)
from .handlers.base import (
    start_command, cancel_command, main_menu_handler, go_to_main_menu,
    global_error_handler,
)
from .handlers.schedule import (
    start_schedule, select_source_callback, receive_message_ids,
    datetime_callback, input_day, select_target_callback,
)
from .handlers.posts import (
    show_active_posts, posts_callback_handler,
    edit_date_callback, edit_time_callback,
    edit_custom_date_input, edit_custom_time_input,
)
from .handlers.settings import (
    show_settings, settings_callback_handler,
    add_channel_input, add_admin_input, add_hour_input,
)
from .handlers.history import show_history, history_callback_handler

logger = logging.getLogger(__name__)

# Bot instance reference (set during build)
bot_instance = None


def build_application() -> Application:
    """Build and configure the Telegram application."""
    from .config import BOT_TOKEN

    builder = Application.builder().token(BOT_TOKEN)
    app = builder.build()

    global bot_instance
    bot_instance = app.bot

    # ── Basic commands ──────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # ── Schedule conversation (new flow) ────────────────────────────────────
    schedule_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📅 زمان‌بندی جدید$"), start_schedule),
        ],
        states={
            SELECT_SOURCE_CHANNEL: [
                CallbackQueryHandler(select_source_callback, pattern=r"^src:"),
                CallbackQueryHandler(lambda u, c: _cancel_inline(u, c), pattern=r"^cancel$"),
            ],
            SELECT_MESSAGE_IDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message_ids),
            ],
            SELECT_DATETIME: [
                CallbackQueryHandler(datetime_callback, pattern=r"^dt:"),
                CallbackQueryHandler(datetime_callback, pattern=r"^m:"),
                CallbackQueryHandler(datetime_callback, pattern=r"^h:"),
                CallbackQueryHandler(lambda u, c: _cancel_inline(u, c), pattern=r"^cancel$"),
            ],
            INPUT_DAY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_day),
            ],
            SELECT_TARGET_CHANNEL: [
                CallbackQueryHandler(select_target_callback, pattern=r"^dst:"),
                CallbackQueryHandler(lambda u, c: _cancel_inline(u, c), pattern=r"^cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel_command),
        ],
        per_message=True,
        allow_reentry=True,
    )
    app.add_handler(schedule_conv)

    # ── Posts management conversation ───────────────────────────────────────
    posts_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📋 پست‌های فعال$"), _enter_posts),
        ],
        states={
            MANAGE_POSTS: [
                CallbackQueryHandler(posts_callback_handler),
            ],
            MANAGE_POST_DETAIL: [
                CallbackQueryHandler(posts_callback_handler),
            ],
            EDIT_POST_DATE: [
                CallbackQueryHandler(edit_date_callback, pattern=r"^d:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_custom_date_input),
                CallbackQueryHandler(lambda u, c: _cancel_inline(u, c), pattern=r"^cancel$"),
            ],
            EDIT_POST_TIME: [
                CallbackQueryHandler(edit_time_callback, pattern=r"^t:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_custom_time_input),
                CallbackQueryHandler(lambda u, c: _cancel_inline(u, c), pattern=r"^cancel$"),
            ],
            EDIT_CUSTOM_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_custom_time_input),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel_command),
        ],
        per_message=True,
        allow_reentry=True,
    )
    app.add_handler(posts_conv)

    # ── History conversation ────────────────────────────────────────────────
    history_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📊 تاریخچه$"), _enter_history),
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
        per_message=True,
        allow_reentry=True,
    )
    app.add_handler(history_conv)

    # ── Settings conversation ───────────────────────────────────────────────
    settings_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^⚙️ تنظیمات$"), show_settings),
        ],
        states={
            SETTINGS_MENU: [
                CallbackQueryHandler(settings_callback_handler),
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
        per_message=True,
        allow_reentry=True,
    )
    app.add_handler(settings_conv)

    # ── Main menu handler (catch-all for text) ──────────────────────────────
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (
            filters.Regex("^🏠 منوی اصلی$")
        ),
        main_menu_handler,
    ))

    # ── Main menu button (standalone) ───────────────────────────────────────
    app.add_handler(CallbackQueryHandler(go_to_main_menu, pattern=r"^main_menu$"))

    # ── Global error handler ────────────────────────────────────────────────
    app.add_error_handler(global_error_handler)

    logger.info("Application built with %d handlers", len(app.handlers))
    return app


async def _enter_posts(update, context):
    """Enter posts management."""
    await show_active_posts(update, context, page=0)
    return MANAGE_POSTS


async def _enter_history(update, context):
    """Enter history."""
    await show_history(update, context, page=0)
    return VIEW_HISTORY


async def _cancel_inline(update, context):
    """Cancel from inline keyboard."""
    from telegram.ext import ConversationHandler
    query = update.callback_query
    await query.answer()
    context.user_data.clear()

    from .constants import Msg, OWNER_ID
    from .keyboards import main_menu
    from .config import OWNER_ID as _OID
    user_id = query.from_user.id

    await query.edit_message_text(Msg.CANCELLED, reply_markup=None)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=Msg.WELCOME,
        reply_markup=main_menu(user_id, is_owner=(user_id == _OID)),
        parse_mode="HTML"
    )
    return ConversationHandler.END

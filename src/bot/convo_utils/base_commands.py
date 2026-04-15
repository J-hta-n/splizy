from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.lib.splizy_repo.repo import repo


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    username = user.username or user.first_name
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text(
            f"Hello {username}! I help make splitting bills easier for you and your friends with the convenience of telegram groups, "
            "so all of you can enjoy the group trip without worrying about the hassle of bill splits!\n\n"
            "To get started, add me into a telegram group and activate it with /start, then:\n"
            "1. Make all participants admins\n"
            "2. Run /register to auto-detect and register them\n"
            "And you're all set!"
        )
        return ConversationHandler.END

    # Register group chat id if not already registered
    group_id = update.message.chat.id
    repo.ensure_group_exists({"id": group_id})
    cur_users = repo.list_group_users(group_id)
    msg = (
        "Hello there! I help make splitting bills easier for you all with the convenience of telegram groups.\n\n"
        + "To get started, make all participants admins and then register them with /register, and refer "
        "to /help for the full list of available commands. Have a fun trip!"
        if not cur_users
        else f"The following users are already registered: {', '.join([f'@{user['username']}' for user in cur_users])}! Welcome back to Splizy!"
    )
    await update.message.reply_text(msg)
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "📋 Here's what Splizy can do!\n\n"
        "/register - Auto-register all group members (admin-based, immutable once set)\n"
        "/register_manual - Manually enter telegram handles (legacy, for testing)\n"
        "/set_exp_currency - Set the default expense currency\n"
        "/set_final_currency - Set the currency for settlement\n"
        "/add - Add a new expense\n"
        "/add_receipt - Add expense from a receipt photo (coming soon)\n"
        "/view - View all expenses (Can edit and delete from here as well)\n"
        "/settleup - Get settlement recommendations\n"
    )
    await update.message.reply_text(message)
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

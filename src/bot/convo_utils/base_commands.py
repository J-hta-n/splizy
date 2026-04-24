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
            "3. Configure currencies with /set_currencies\n\n"
            "And you're all set! Please refer to /help for the full list of available commands. Have a fun trip!"
        )
        return ConversationHandler.END

    # Register group chat id if not already registered
    group_id = update.message.chat.id
    repo.ensure_group_exists({"id": group_id})
    cur_users = repo.list_group_users(group_id)
    msg = (
        "Hello there! I help make splitting bills easier for you all with the convenience of telegram groups.\n\n"
        + "To get started, make all participants admins and then register them with /register, then configure currencies with /set_currencies.\n\n"
        + "Please refer to /help for the full list of available commands. Have a fun trip!"
        if not cur_users
        else f"The following users are already registered: {', '.join([f'@{user['username']}' for user in cur_users])}\nWelcome back to Splizy!"
    )
    await update.message.reply_text(msg)
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "📋 Here's what Splizy can do!\n\n"
        "/register - Auto-register all group members (ensure they're all admins first)\n"
        "/register_manual - Manually enter telegram handles instead\n"
        "/set_currencies - Configure default expense and settlement currencies\n"
        "/add - Add a new expense\n"
        "/add_receipt - Add detailed expense from a receipt photo\n"
        "/view - View all expenses + make edits / deletes from here as well\n"
        "/settleup - Get suggested transfer amounts\n"
        "/settleup_report - Get details on how suggested transfers were calculated\n"
    )
    await update.message.reply_text(message)
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    context.chat_data.clear()
    return ConversationHandler.END

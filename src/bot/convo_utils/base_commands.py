from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.lib.splizy_repo.database import supabase


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    username = user.username or user.first_name
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text(
            f"Hello {username}! I help make splitting bills easier for you and your friends with the convenience of telegram groups, "
            "so all of you can enjoy the group trip without worrying about the hassle of bill splits!\n\n"
            "To get started, add me into a telegram group and activate it with /start, then register all participants' telegram handles "
            "with /register, and you're all set!"
        )
        return ConversationHandler.END

    # Register group chat id if not already registered
    group_id = update.message.chat.id
    supabase.table("groups").upsert({"id": group_id}).execute()
    cur_users = (
        supabase.table("splizy_users")
        .select("*")
        .eq("group_id", group_id)
        .execute()
        .data
    )
    msg = (
        "Hello there! I help make splitting bills easier for you all with the convenience of telegram groups.\n\n"
        + "To get started, register all group members' telegram handles with /register, and refer "
        "to /help for the full list of available commands. Have a fun trip!"
        if not cur_users
        else f"The following users are already registered: {', '.join([f'@{user['username']}' for user in cur_users])}! Welcome back to Splizy!"
    )
    await update.message.reply_text(msg)
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "📋 Here's what Splizy can do!\n\n"
        "/register - Register the telegram handles of all participants\n"
        "/set_exp_currency - Set the default expense currency\n"
        "/set_final_currency - Set the currency for settlement\n"
        "/add - Add a new expense\n"
        "/add_receipt - Add expense from a receipt photo (coming soon)\n"
        "/view - View all expenses (Can edit and delete from here as well)\n"
        "/settleup - Get settlement recommendations (coming soon)\n"
    )
    await update.message.reply_text(message)
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

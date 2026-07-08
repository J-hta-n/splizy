from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.lib.splizy_repo.service import get_group_usernames


def group_only(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type in ["group", "supergroup"]:
            return await handler(update, context)
        else:
            await update.message.reply_text(
                "This command can only be used in group chats."
            )

    return wrapper


def ensure_has_registered_users(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.chat_data.clear()
        usernames = get_group_usernames(update.message.chat.id)
        if not usernames:
            await update.message.reply_text(
                "Please register participants with /register before adding expenses."
            )
            return ConversationHandler.END
        context.chat_data["all_participants"] = usernames

    return wrapper

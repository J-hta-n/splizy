from telegram import Update
from telegram.ext import ContextTypes


def group_only(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type in ["group", "supergroup"]:
            return await handler(update, context)
        else:
            await update.message.reply_text(
                "This command can only be used in group chats."
            )

    return wrapper

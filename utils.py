from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes


def get_2dp_str(input: Decimal) -> str:
    return str(round(input, 2))


def group_only(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type in ["group", "supergroup"]:
            return await handler(update, context)
        else:
            await update.message.reply_text(
                "This command can only be used in group chats."
            )

    return wrapper

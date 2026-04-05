from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import MINIAPP_URL


async def open_miniapp(
    update: Update, group_id: int
) -> None:
    base_url = MINIAPP_URL.rstrip("/")
    url = f"{base_url}/?group_id={group_id}"

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Open miniapp", url=url)]]
    )

    await update.message.reply_text(
        "Receipt parsed. Open the miniapp to review and confirm the split.",
        reply_markup=keyboard,
    )

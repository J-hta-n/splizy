from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from config import MINIAPP_URL


async def open_miniapp(update: Update, group_id: int) -> None:
    url = f"{MINIAPP_URL}/?group_id={group_id}"

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Open miniapp", url=url)],
            [InlineKeyboardButton("I'm done", callback_data="receipt_done")],
        ]
    )

    await update.message.reply_text(
        "Receipt parsed. Open the miniapp to review and confirm the split, then tap I'm done after submitting the expense via the miniapp.",
        reply_markup=keyboard,
    )

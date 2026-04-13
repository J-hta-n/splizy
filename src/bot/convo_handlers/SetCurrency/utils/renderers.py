from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from src.lib.currencies.config import COMMON_CURRENCY_CODES


async def send_select_currency(update: Update, text: str):
    keyboard = []
    for code, info in COMMON_CURRENCY_CODES.items():
        keyboard.append([InlineKeyboardButton(f"{code} ({info})", callback_data=code)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

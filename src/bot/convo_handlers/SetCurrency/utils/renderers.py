from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.convo_handlers.SetCurrency.callbacks import (
    CURRENCY_BACK,
    EDIT_EXPENSE_CURRENCY,
    EDIT_SETTLEUP_CURRENCY,
)
from src.bot.convo_handlers.SetCurrency.context import SetCurrencyChatData
from src.lib.currencies.config import ALL_CURRENCY_CODES, COMMON_CURRENCY_CODES
from src.lib.currencies.utils import build_exchange_rate_line
from src.lib.splizy_repo.model import GroupRow


def _build_current_currencies_payload(
    group: GroupRow,
) -> tuple[str, InlineKeyboardMarkup]:
    expense_currency = (group.get("expense_currency") or "SGD").upper()
    settleup_currency = (group.get("settleup_currency") or "SGD").upper()
    expense_desc = ALL_CURRENCY_CODES.get(expense_currency, expense_currency)
    settleup_desc = ALL_CURRENCY_CODES.get(settleup_currency, settleup_currency)
    rate_line = build_exchange_rate_line(settleup_currency, expense_currency)

    text = (
        "Please configure the following default currencies.\n\n"
        f"Expenses: {expense_currency} ({expense_desc})\n"
        f"Settleup: {settleup_currency} ({settleup_desc})\n\n"
        f"{rate_line}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "Edit expenses currency", callback_data=EDIT_EXPENSE_CURRENCY
            )
        ],
        [
            InlineKeyboardButton(
                "Edit settleup currency", callback_data=EDIT_SETTLEUP_CURRENCY
            ),
        ],
    ]
    return text, InlineKeyboardMarkup(keyboard)


async def send_current_currencies(
    update: Update, context: ContextTypes.DEFAULT_TYPE, remarks=None
):
    data: SetCurrencyChatData = context.chat_data
    group: GroupRow = data["group"]
    text, reply_markup = _build_current_currencies_payload(group)
    if remarks:
        text = f"({remarks})\n\n" + text
    await update.message.reply_text(text, reply_markup=reply_markup)


async def send_current_currencies_for_query(
    query: CallbackQuery, group: GroupRow, remarks=None
):
    text, reply_markup = _build_current_currencies_payload(group)
    if remarks:
        text = f"({remarks})\n\n" + text
    await query.edit_message_text(text, reply_markup=reply_markup)


async def send_select_currency(query: CallbackQuery, text: str, target_field: str):
    keyboard = []
    for code, info in COMMON_CURRENCY_CODES.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{code} ({info})",
                    callback_data=f"currency_set:{target_field}:{code}",
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                f"Input another currency",
                callback_data=f"currency_custom:{target_field}",
            )
        ]
    )
    keyboard.append([InlineKeyboardButton("Go back", callback_data=CURRENCY_BACK)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

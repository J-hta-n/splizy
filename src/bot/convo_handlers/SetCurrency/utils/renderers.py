from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.lib.currencies.config import ALL_CURRENCY_CODES, COMMON_CURRENCY_CODES
from src.lib.splizy_repo.model import GroupRow


def _build_current_currencies_payload(
    group: GroupRow,
) -> tuple[str, InlineKeyboardMarkup]:
    expense_currency = (group.get("expense_currency") or "SGD").upper()
    settleup_currency = (group.get("settleup_currency") or "SGD").upper()
    expense_desc = ALL_CURRENCY_CODES.get(expense_currency, expense_currency)
    settleup_desc = ALL_CURRENCY_CODES.get(settleup_currency, settleup_currency)

    text = (
        "Please configure the default currencies for bill expenses, and when settling up.\n\n"
        f"Expenses: {expense_currency} ({expense_desc})\n"
        f"Settleup: {settleup_currency} ({settleup_desc})"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "Edit expenses currency", callback_data="edit_expense_currency"
            )
        ],
        [
            InlineKeyboardButton(
                "Edit settleup currency", callback_data="edit_settleup_currency"
            ),
        ],
    ]
    return text, InlineKeyboardMarkup(keyboard)


async def send_current_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group: GroupRow = context.user_data["group"]
    text, reply_markup = _build_current_currencies_payload(group)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def send_current_currencies_for_query(query: CallbackQuery, group: GroupRow):
    text, reply_markup = _build_current_currencies_payload(group)
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
    keyboard.append([InlineKeyboardButton("Go back", callback_data="currency_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

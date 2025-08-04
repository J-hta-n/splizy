from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.bot.convo_handlers.Base import BaseConversation
from src.bot.convo_utils.currencies import COMMON_CURRENCY_CODES_STRING
from src.bot.convo_utils.parsers import parse_currency
from src.bot.convo_utils.wrappers import group_only
from src.utils.database import supabase


class SetCurrencies(BaseConversation):
    SET_EXPENSE_CURRENCY = 0
    SET_SETTLEUP_CURRENCY = 1

    def setup_handlers(self):
        self.entry_points = [
            (CommandHandler("set_exp_currency", set_expense_currency_command)),
        ]
        self.states = {
            self.SET_EXPENSE_CURRENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_expense_currency)
            ],
            self.SET_SETTLEUP_CURRENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_settleup_currency)
            ],
        }


@group_only
async def set_expense_currency_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.message.reply_text(
        "Please enter the default expense currency you want to set, eg 'MYR', 'USD', 'SGD'.\n\n"
        f"Available currencies:\n{COMMON_CURRENCY_CODES_STRING}"
    )
    return SetCurrencies.SET_EXPENSE_CURRENCY


async def set_expense_currency(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    is_valid, currency = parse_currency(update.message.text.upper())
    if not is_valid:
        await update.message.reply_text(currency)
        return SetCurrencies.SET_EXPENSE_CURRENCY

    group_id = update.message.chat.id
    supabase.table("groups").update({"expense_currency": currency}).eq(
        "id", group_id
    ).execute()

    await update.message.reply_text(f"Expense currency set to {currency}.")
    return ConversationHandler.END


async def set_settleup_currency_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.message.reply_text(
        "Please enter the settleup currency you want to set, eg 'MYR', 'USD', 'SGD'.\n\n"
        f"Available currencies:\n{COMMON_CURRENCY_CODES_STRING}"
    )
    return SetCurrencies.SET_SETTLEUP_CURRENCY


async def set_settleup_currency(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    is_valid, currency = parse_currency(update.message.text.upper())
    if not is_valid:
        await update.message.reply_text(currency)
        return SetCurrencies.SET_EXPENSE_CURRENCY

    group_id = update.message.chat.id
    supabase.table("groups").update({"settleup_currency": currency}).eq(
        "id", group_id
    ).execute()

    await update.message.reply_text(f"Expense currency set to {currency}.")
    return ConversationHandler.END

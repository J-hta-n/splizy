from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.SetCurrency.states import SetCurrencyStates
from src.bot.convo_handlers.SetCurrency.utils.renderers import send_select_currency
from src.bot.convo_utils.wrappers import group_only
from src.lib.splizy_repo.database import supabase


@group_only
async def set_expense_currency_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await send_select_currency(update, "Please select the default expense currency:")
    return SetCurrencyStates.SET_EXPENSE_CURRENCY


async def set_expense_currency(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    currency = query.data

    group_id = query.message.chat.id
    supabase.table("groups").update({"expense_currency": currency}).eq(
        "id", group_id
    ).execute()

    await update.callback_query.edit_message_text(f"Expense currency set to {currency}.")
    return ConversationHandler.END


@group_only
async def set_settleup_currency_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await send_select_currency(update, "Please select the settleup currency:")
    return SetCurrencyStates.SET_SETTLEUP_CURRENCY


async def set_settleup_currency(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    currency = query.data

    group_id = query.message.chat.id
    supabase.table("groups").update({"settleup_currency": currency}).eq(
        "id", group_id
    ).execute()

    await update.callback_query.edit_message_text(f"Settleup currency set to {currency}.")
    return ConversationHandler.END

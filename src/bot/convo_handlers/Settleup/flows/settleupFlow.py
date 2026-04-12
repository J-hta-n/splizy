from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.Settleup.utils.general import get_suggested_payments
from src.bot.convo_utils.wrappers import group_only
from src.lib.currencies.service import refresh_exchange_rates_if_stale
from src.lib.splizy_repo.repo import repo


@group_only
async def set_expense_currency_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    refresh_exchange_rates_if_stale()
    group_id = update.message.chat.id
    all_expenses = repo.list_expenses(group_id)
    settleup_currency = repo.get_group(group_id).get("settleup_currency", "SGD")
    suggested_payments = get_suggested_payments(all_expenses, settleup_currency)
    # spending_chart = generate_spending_chart(all_expenses, settleup_currency)

    return ConversationHandler.END

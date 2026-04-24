from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_handlers.ManageBills.utils.renderers import send_all_expenses
from src.bot.convo_handlers.ManageBills.utils.renderers.index import (
    get_view_all_entries_markup,
)
from src.lib.logger import get_logger
from src.lib.splizy_repo.repo import repo

logger = get_logger(__name__)


async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "confirm_delete":
        expense_id = context.chat_data["expense_id"]
        repo.delete_expense(expense_id)
        await query.edit_message_text(
            "Expense deleted successfully.",
            reply_markup=get_view_all_entries_markup(),
        )
        return ManageBillStates.VIEW_EXPENSE
    elif action == "cancel_delete":
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE

    return ConversationHandler.END

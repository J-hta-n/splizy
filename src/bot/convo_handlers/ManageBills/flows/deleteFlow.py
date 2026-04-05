from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_utils.renderers import send_all_expenses
from src.lib.logger import get_logger
from src.lib.splizy_repo.database import supabase

logger = get_logger(__name__)


async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "confirm_delete":
        expense_id = context.user_data["expense_id"]
        supabase.table("expenses").delete().eq(
            "id", expense_id
        ).execute()  # Cascade deletes user_expenses
        await query.edit_message_text("Expense deleted successfully.")
        context.user_data.clear()
        return ConversationHandler.END
    elif action == "cancel_delete":
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE

    return ConversationHandler.END

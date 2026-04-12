from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_handlers.ManageBills.utils.general import (
    populate_context_for_selected_expense_from_viewall,
)
from src.bot.convo_handlers.ManageBills.utils.renderers import (
    send_all_expenses,
    send_expense_view,
)
from src.bot.convo_utils.wrappers import group_only
from src.lib.splizy_repo.repo import repo


@group_only
async def view_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_id = update.message.chat.id
    expenses = repo.list_expenses(group_id)
    users = repo.list_group_users(group_id)
    if not expenses:
        await update.message.reply_text("No expenses logged yet.")
        return ConversationHandler.END
    context.user_data["expenses"] = expenses
    context.user_data["all_participants"] = [user["username"] for user in users]

    await send_all_expenses(update, context)
    return ManageBillStates.VIEW_EXPENSE


async def view_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    index = int(query.data)
    context.user_data["expense_index"] = index
    expense = context.user_data["expenses"][index]

    populate_context_for_selected_expense_from_viewall(context, expense)
    await send_expense_view(update, context)
    return ManageBillStates.EDIT_OR_GO_BACK

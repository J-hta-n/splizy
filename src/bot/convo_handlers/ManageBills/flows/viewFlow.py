from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.ManageBills.context import get_managebills_user_data
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
    data = get_managebills_user_data(context)
    group_id = update.message.chat.id
    expenses = repo.list_expenses(group_id)
    if not expenses:
        await update.message.reply_text("No expenses logged yet.")
        return ConversationHandler.END
    data["expenses"] = expenses

    await send_all_expenses(update, context)
    return ManageBillStates.VIEW_EXPENSE


async def view_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = get_managebills_user_data(context)
    query = update.callback_query
    await query.answer()

    # Ignore unrelated callback payloads that can be routed here while another
    # conversation is active in the same chat/user scope.
    if not query.data or not query.data.isdigit():
        return ManageBillStates.VIEW_EXPENSE

    index = int(query.data)
    data["expense_index"] = index
    expense = data["expenses"][index]

    populate_context_for_selected_expense_from_viewall(context, expense)
    await send_expense_view(update, context)
    return ManageBillStates.EDIT_OR_GO_BACK

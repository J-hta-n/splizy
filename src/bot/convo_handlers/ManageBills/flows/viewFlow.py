from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.ManageBills.callbacks import (
    VIEW_ALL_ENTRIES,
    VIEW_PAGE_NEXT,
    VIEW_PAGE_PREV,
    VIEW_SELECT_PREFIX,
    VIEW_TOGGLE_HIDE,
    VIEW_TOGGLE_SHOW,
)
from src.bot.convo_handlers.ManageBills.context import ManageBillsUserData
from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_handlers.ManageBills.utils.general import (
    initialise_viewall_context,
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
    context.user_data.clear()
    group_id = update.message.chat.id
    expenses = repo.list_expenses(group_id)
    if not expenses:
        await update.message.reply_text("No expenses logged yet.")
        return ConversationHandler.END
    initialise_viewall_context(context.user_data, expenses)
    await send_all_expenses(update, context)
    return ManageBillStates.VIEW_EXPENSE


async def view_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if not query.data:
        return ManageBillStates.VIEW_EXPENSE
    data: ManageBillsUserData = context.user_data

    # NOTE: multiple users can trigger this callback, each one with a different context, hence,
    # safer to refetch all expenses everytime to prevent bugs due to context pollution
    # TODO: refactor to tag all expenses with a scope_key, if it matches group_id and is up to date,
    # don't need to refetch; else if either different group_id or is stale, update it
    data.clear()
    group_id = update.message.chat.id
    expenses = repo.list_expenses(group_id)
    if not expenses:
        await update.message.reply_text("No expenses logged yet.")
        return ConversationHandler.END
    initialise_viewall_context(data, expenses)

    # Entry point from addFlow
    if query.data == VIEW_ALL_ENTRIES:
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE

    # View selected expense
    if query.data.startswith(VIEW_SELECT_PREFIX):
        try:
            index = int(query.data.removeprefix(VIEW_SELECT_PREFIX))
        except ValueError:
            return ManageBillStates.VIEW_EXPENSE

        if index < 0 or index >= len(data["expenses"]):
            return ManageBillStates.VIEW_EXPENSE

        data["expense_index"] = index
        expense = data["expenses"][index]

        populate_context_for_selected_expense_from_viewall(data, expense)
        await send_expense_view(update, context)
        return ManageBillStates.EDIT_OR_GO_BACK

    # Modify viewall settings
    if query.data == VIEW_PAGE_PREV:
        current_page = int(data.get("viewall_page", 0))
        data["viewall_page"] = max(0, current_page - 1)
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE

    if query.data == VIEW_PAGE_NEXT:
        current_page = int(data.get("viewall_page", 0))
        data["viewall_page"] = current_page + 1
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE

    if query.data == VIEW_TOGGLE_HIDE:
        data["viewall_is_collapsed"] = True
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE

    if query.data == VIEW_TOGGLE_SHOW:
        data["viewall_is_collapsed"] = False
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE

    # Ignore unrelated callback payloads that can be routed here while another
    # conversation is active in the same chat/user scope.
    return ManageBillStates.VIEW_EXPENSE

from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_handlers.ManageBills.utils.renderers import (
    send_all_expenses,
    send_expense_view,
)
from src.bot.convo_utils.wrappers import group_only
from src.lib.splizy_repo.database import supabase


@group_only
async def view_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_id = update.message.chat.id
    expenses = (
        supabase.table("expenses")
        .select("*")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    if not expenses:
        await update.message.reply_text("No expenses logged yet.")
        return ConversationHandler.END
    context.user_data["expenses"] = expenses

    await send_all_expenses(update, context)
    return ManageBillStates.VIEW_EXPENSE


async def view_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    index = int(query.data)
    expense = context.user_data["expenses"][index]
    group_id = query.message.chat.id

    users = (
        supabase.table("splizy_users")
        .select("username")
        .eq("group_id", group_id)
        .execute()
        .data
    )
    payees = expense.get("payees") or []

    payees_by_username = {
        entry["user"]: Decimal(str(entry["amount"])) for entry in payees
    }

    context.user_data["all_participants"] = [user["username"] for user in users]
    context.user_data["has_mult"] = expense.get("multiplier") is not None
    context.user_data["mult_val"] = expense.get("multiplier")

    if expense["is_equal_split"]:
        context.user_data["split_type"] = (
            "equal_some" if len(payees) < len(users) else "equal_all"
        )
    else:
        context.user_data["split_type"] = "custom"
    context.user_data["selected_participants"] = [
        entry["user"]
        for entry in payees
        if entry["user"] in context.user_data["all_participants"]
    ]
    context.user_data["participant_selections"] = [
        username in context.user_data["selected_participants"]
        for username in context.user_data["all_participants"]
    ]
    context.user_data["custom_amounts"] = [
        payees_by_username.get(username, Decimal("0"))
        for username in context.user_data["all_participants"]
    ]

    context.user_data["expense_id"] = expense[
        "id"
    ]  # Signals an edit flow in expense_confirm
    context.user_data["expense_name"] = expense["title"]
    context.user_data["amount"] = Decimal(expense["amount"])
    context.user_data["paid_by"] = expense["paid_by"]
    context.user_data["currency"] = expense["currency"]
    context.user_data["is_equal_split"] = expense["is_equal_split"]
    context.user_data["receipt"] = expense["receipt"]

    await send_expense_view(update, context)
    return ManageBillStates.EDIT_OR_GO_BACK

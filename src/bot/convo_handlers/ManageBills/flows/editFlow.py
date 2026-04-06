from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_handlers.ManageBills.utils.renderers import (
    send_all_expenses,
    send_confirmation_form,
)
from src.lib.logger import get_logger

logger = get_logger(__name__)


async def edit_or_go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "edit_expense":
        await send_confirmation_form(update, context, False)
        return ManageBillStates.EXPENSE_CONFIRM
    elif action == "delete_expense":
        data = context.user_data
        keyboard = [
            [
                InlineKeyboardButton("❌ No", callback_data="cancel_delete"),
                InlineKeyboardButton("✅ Yes", callback_data="confirm_delete"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=(
                f"Are you sure you want to delete this expense?\n({data['expense_name']} | {data['paid_by']} | {data['currency']} {data['amount']})\n"
                "This action cannot be undone."
            ),
            reply_markup=reply_markup,
        )
        return ManageBillStates.DELETE_EXPENSE
    else:
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE

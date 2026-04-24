from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.convo_handlers.ManageBills.callbacks import (
    CANCEL_DELETE,
    CONFIRM_DELETE,
    DELETE_EXPENSE,
    EDIT_EXPENSE,
    GO_BACK,
    HIDE_RECEIPT,
    SHOW_RECEIPT,
)
from src.bot.convo_handlers.ManageBills.context import ManageBillsChatData
from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_handlers.ManageBills.utils.renderers import (
    open_miniapp,
    send_all_expenses,
    send_confirmation_form,
    send_expense_view,
    send_expense_with_receipt_view,
)
from src.lib.logger import get_logger

logger = get_logger(__name__)


async def edit_or_go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data: ManageBillsChatData = context.chat_data
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == EDIT_EXPENSE:
        if data["receipt"]:
            await open_miniapp(
                update=update,
                group_id=update.effective_chat.id,
                expense_id=data["expense_id"],
            )
            return ManageBillStates.EXPENSE_RECEIPT_CONFIRM
        await send_confirmation_form(update, context, False)
        return ManageBillStates.EXPENSE_CONFIRM

    elif action == DELETE_EXPENSE:
        keyboard = [
            [
                InlineKeyboardButton("❌ No", callback_data=CANCEL_DELETE),
                InlineKeyboardButton("✅ Yes", callback_data=CONFIRM_DELETE),
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
    elif action == GO_BACK:
        await send_all_expenses(update, context, False)
        return ManageBillStates.VIEW_EXPENSE
    elif action == SHOW_RECEIPT:
        await send_expense_with_receipt_view(update, context)
        return ManageBillStates.EDIT_OR_GO_BACK
    elif action == HIDE_RECEIPT:
        await send_expense_view(update, context)
        return ManageBillStates.EDIT_OR_GO_BACK

    logger.warning("Unknown edit action received in edit_or_go_back: %s", action)
    return ManageBillStates.EDIT_OR_GO_BACK

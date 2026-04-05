from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from src.bot.convo_handlers.Base import BaseConversation
from src.bot.convo_handlers.ManageBills.flows.addFlow import (
    add_command,
    expense_amount,
    expense_confirm,
    expense_custom_amount,
    expense_multiplier,
    expense_name,
    expense_paid_by,
    expense_participants,
    expense_split_type,
)
from src.bot.convo_handlers.ManageBills.flows.deleteFlow import delete_expense
from src.bot.convo_handlers.ManageBills.flows.editFlow import edit_or_go_back
from src.bot.convo_handlers.ManageBills.flows.receiptFlow import (
    add_receipt_command,
    expense_receipt_done,
    expense_receipt_upload,
)
from src.bot.convo_handlers.ManageBills.flows.unevenSplitFlow import (
    expense_custom_split,
)
from src.bot.convo_handlers.ManageBills.flows.viewFlow import (
    view_all_command,
    view_expense,
)
from src.bot.convo_handlers.ManageBills.states import ManageBillStates as States
from src.lib.logger import get_logger

logger = get_logger(__name__)


class ManageBills(BaseConversation):
    def setup_handlers(self):
        self.entry_points = [
            CommandHandler("add", add_command),
            CommandHandler("add_receipt", add_receipt_command),
            CommandHandler("view", view_all_command),
        ]
        self.states = {
            States.EXPENSE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_name)
            ],
            States.EXPENSE_RECEIPT_UPLOAD: [
                MessageHandler(
                    (filters.PHOTO | filters.TEXT) & ~filters.COMMAND,
                    expense_receipt_upload,
                )
            ],
            States.EXPENSE_RECEIPT_CONFIRM: [
                CallbackQueryHandler(expense_receipt_done, pattern="^receipt_done$")
            ],
            States.EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)
            ],
            States.EXPENSE_PAID_BY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_paid_by)
            ],
            States.EXPENSE_SPLIT_TYPE: [CallbackQueryHandler(expense_split_type)],
            States.EXPENSE_PARTICIPANTS: [CallbackQueryHandler(expense_participants)],
            States.EXPENSE_CUSTOM_SPLIT: [CallbackQueryHandler(expense_custom_split)],
            States.EXPENSE_CUSTOM_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_custom_amount)
            ],
            States.EXPENSE_MULTIPLIER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_multiplier)
            ],
            States.EXPENSE_CONFIRM: [CallbackQueryHandler(expense_confirm)],
            States.VIEW_EXPENSE: [CallbackQueryHandler(view_expense)],
            States.EDIT_OR_GO_BACK: [CallbackQueryHandler(edit_or_go_back)],
            States.DELETE_EXPENSE: [CallbackQueryHandler(delete_expense)],
        }

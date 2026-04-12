from telegram.ext import CommandHandler

from src.bot.convo_handlers.Base import BaseConversation


class Settleup(BaseConversation):
    def setup_handlers(self):
        self.entry_points = [
            # (CommandHandler("settleup", set_expense_currency_command)),
        ]

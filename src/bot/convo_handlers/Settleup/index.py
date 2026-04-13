from telegram.ext import CommandHandler

from src.bot.convo_handlers.Base import BaseConversation
from src.bot.convo_handlers.Settleup.flows.settleupFlow import settleup_command


class Settleup(BaseConversation):
    def setup_handlers(self):
        self.entry_points = [
            (CommandHandler("settleup", settleup_command)),
        ]

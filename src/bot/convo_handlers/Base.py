from abc import ABC, abstractmethod

from telegram.ext import CommandHandler, ConversationHandler

from src.bot.convo_utils.base_commands import (
    cancel_command,
    help_command,
    start_command,
)

base_command_handlers = [
    CommandHandler("start", start_command),
    CommandHandler("help", help_command),
    CommandHandler("cancel", cancel_command),
]


class BaseConversation(ABC):
    def __init__(self):
        self.entry_points = []
        self.states = {}
        self.fallbacks = base_command_handlers

    @abstractmethod
    def setup_handlers(self):
        """To be implemented by subclasses"""
        pass

    def get_convo_handler(self):
        self.setup_handlers()
        return ConversationHandler(
            entry_points=self.entry_points,
            states=self.states,
            fallbacks=self.fallbacks,
            allow_reentry=True,
        )


class BaseCommands(BaseConversation):
    def setup_handlers(self):
        self.entry_points = base_command_handlers

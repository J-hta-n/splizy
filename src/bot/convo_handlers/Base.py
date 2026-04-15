from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler

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
        self.conversation_timeout = 10

    @abstractmethod
    def setup_handlers(self):
        """To be implemented by subclasses"""

    @staticmethod
    def _key_matches_current_scope(
        handler: ConversationHandler,
        key: object,
        chat_id: int | None,
        user_id: int | None,
    ) -> bool:
        if not isinstance(key, tuple):
            return False

        idx = 0
        if handler.per_chat:
            if chat_id is None or idx >= len(key) or key[idx] != chat_id:
                return False
            idx += 1

        if handler.per_user:
            if user_id is None or idx >= len(key) or key[idx] != user_id:
                return False

        return True

    def _reset_active_conversations(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_chat.id if update.effective_chat else None
        user_id = update.effective_user.id if update.effective_user else None

        for handlers in context.application.handlers.values():
            for handler in handlers:
                if not isinstance(handler, ConversationHandler):
                    continue

                conversations = getattr(handler, "_conversations", None)
                if not isinstance(conversations, dict):
                    continue

                for key in list(conversations.keys()):
                    if self._key_matches_current_scope(handler, key, chat_id, user_id):
                        conversations.pop(key, None)

    def _wrap_entry_callback(
        self,
        callback: Callable[..., Awaitable[Any]],
    ) -> Callable[..., Awaitable[Any]]:
        @wraps(callback)
        async def wrapped(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            self._reset_active_conversations(update, context)
            return await callback(update, context, *args, **kwargs)

        return wrapped

    def _wrap_entry_points(self) -> None:
        for entry in self.entry_points:
            if not isinstance(entry, CommandHandler):
                continue
            if getattr(entry.callback, "_splizy_entry_wrapped", False):
                continue

            wrapped = self._wrap_entry_callback(entry.callback)
            setattr(wrapped, "_splizy_entry_wrapped", True)
            entry.callback = wrapped

    def get_convo_handler(self):
        self.setup_handlers()
        self._wrap_entry_points()
        return ConversationHandler(
            name=self.__class__.__name__,
            entry_points=self.entry_points,
            states=self.states,
            fallbacks=self.fallbacks,
            allow_reentry=True,
            conversation_timeout=self.conversation_timeout,
        )


class BaseCommands(BaseConversation):
    def setup_handlers(self):
        self.entry_points = base_command_handlers

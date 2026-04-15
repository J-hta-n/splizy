from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from src.bot.convo_handlers.Base import BaseConversation
from src.bot.convo_handlers.SetCurrency.callbacks import ACTION_PATTERN
from src.bot.convo_handlers.SetCurrency.flows.setCurrencyFlow import (
    select_currency,
    set_currencies_command,
    set_custom_currency,
)
from src.bot.convo_handlers.SetCurrency.states import SetCurrencyStates as States


class SetCurrency(BaseConversation):
    def setup_handlers(self):
        self.entry_points = [
            (CommandHandler("set_currencies", set_currencies_command)),
        ]
        self.states = {
            States.SELECT_CURRENCY: [
                CallbackQueryHandler(
                    select_currency,
                    pattern=ACTION_PATTERN,
                )
            ],
            States.SET_CUSTOM_CURRENCY: [
                MessageHandler(
                    filters.Regex(r"^\s*[A-Za-z]{3}\s*$")
                    & filters.TEXT
                    & ~filters.COMMAND,
                    set_custom_currency,
                )
            ],
        }

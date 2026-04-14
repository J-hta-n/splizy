from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from src.bot.convo_handlers.Base import BaseConversation
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
            States.SELECT_CURRENCY: [CallbackQueryHandler(select_currency)],
            States.SET_CUSTOM_CURRENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_custom_currency)
            ],
        }

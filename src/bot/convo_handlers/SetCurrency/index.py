from telegram.ext import CallbackQueryHandler, CommandHandler

from src.bot.convo_handlers.Base import BaseConversation
from src.bot.convo_handlers.SetCurrency.flows.setCurrencyFlow import (
    set_expense_currency,
    set_expense_currency_command,
    set_settleup_currency,
    set_settleup_currency_command,
)
from src.bot.convo_handlers.SetCurrency.states import SetCurrencyStates as States


class SetCurrency(BaseConversation):
    def setup_handlers(self):
        self.entry_points = [
            (CommandHandler("set_exp_currency", set_expense_currency_command)),
            (CommandHandler("set_final_currency", set_settleup_currency_command)),
        ]
        self.states = {
            States.SET_EXPENSE_CURRENCY: [CallbackQueryHandler(set_expense_currency)],
            States.SET_SETTLEUP_CURRENCY: [CallbackQueryHandler(set_settleup_currency)],
        }

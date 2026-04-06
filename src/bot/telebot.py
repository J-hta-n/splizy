from telegram.ext import ApplicationBuilder

from config import TELEBOT_TOKEN
from src.bot.convo_handlers.Base import BaseCommands
from src.bot.convo_handlers.ManageBills import ManageBills
from src.bot.convo_handlers.RegisterUsers import RegisterUsers
from src.bot.convo_handlers.SetCurrency import SetCurrency


def initialise_telebot():
    app = ApplicationBuilder().token(TELEBOT_TOKEN).build()
    conversations = [
        BaseCommands(),
        ManageBills(),
        RegisterUsers(),
        SetCurrency(),
    ]
    for convo in conversations:
        app.add_handler(convo.get_convo_handler())
    return app

from __future__ import annotations

from typing import TypedDict, cast

from telegram.ext import ContextTypes

from src.bot.convo_handlers.SetCurrency.callbacks import CurrencyTargetField
from src.lib.splizy_repo.model import GroupRow


class SetCurrencyUserData(TypedDict, total=False):
    group: GroupRow
    currency_target_field: CurrencyTargetField


def get_setcurrency_user_data(
    context: ContextTypes.DEFAULT_TYPE,
) -> SetCurrencyUserData:
    return cast(SetCurrencyUserData, context.user_data)

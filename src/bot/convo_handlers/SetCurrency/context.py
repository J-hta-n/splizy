from __future__ import annotations

from typing import TypedDict

from src.bot.convo_handlers.SetCurrency.callbacks import CurrencyTargetField
from src.lib.splizy_repo.model import GroupRow


class SetCurrencyChatData(TypedDict, total=False):
    group: GroupRow
    currency_target_field: CurrencyTargetField

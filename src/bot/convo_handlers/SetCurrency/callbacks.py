from __future__ import annotations

from typing import Final, Literal, TypeAlias

CurrencyTargetField: TypeAlias = Literal["expense_currency", "settleup_currency"]

EDIT_EXPENSE_CURRENCY: Final = "edit_expense_currency"
EDIT_SETTLEUP_CURRENCY: Final = "edit_settleup_currency"
CURRENCY_BACK: Final = "currency_back"

ACTION_PATTERN: Final = (
    r"^(edit_expense_currency|edit_settleup_currency|currency_back|"
    r"currency_custom:(expense_currency|settleup_currency)|"
    r"currency_set:(expense_currency|settleup_currency):[A-Za-z]{3})$"
)

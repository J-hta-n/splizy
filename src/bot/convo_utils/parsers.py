from typing import TypeVar

from src.bot.convo_utils.currencies import COMMON_CURRENCY_CODES

T = TypeVar("T")
ParsedResult = tuple[bool, T | str]


def parse_currency(input: str) -> ParsedResult[str]:
    try:
        currency = input.upper()
        if currency not in COMMON_CURRENCY_CODES:
            return (
                False,
                f"Invalid currency code. Please refer to the list of supported currency codes.",
            )
        return True, currency
    except ValueError:
        return False, "Invalid format. Please refer to the list of currency codes."

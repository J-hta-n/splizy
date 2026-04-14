from typing import TypeVar

from src.lib.currencies.config import ALL_CURRENCY_CODES

T = TypeVar("T")
ParsedResult = tuple[bool, T | str]


def parse_currency(input: str) -> ParsedResult[str]:
    try:
        currency = input.strip().upper()
        if currency not in ALL_CURRENCY_CODES:
            return (
                False,
                "currency code may be out of scope",
            )
        return True, currency
    except ValueError:
        return False, "Invalid format. Please refer to the list of currency codes."

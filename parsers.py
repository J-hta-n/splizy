from dataclasses import dataclass
from decimal import Decimal
from typing import TypedDict

from currencies import COMMON_CURRENCY_CODES

from typing import Generic, TypeVar, Optional


T = TypeVar('T')
ParsedResult = tuple[bool, T | str]


def parse_amount(input: str) -> ParsedResult[tuple[Optional[str], Decimal]]:
    try:
        if input.replace('.', '', 1).isdigit():
            return True, (None, Decimal(input))
        currency, amount = input.split(' ')
        if currency.upper() not in COMMON_CURRENCY_CODES:
            return False, f"Invalid currency code. Please use one of the following: {', '.join(COMMON_CURRENCY_CODES.keys())}"
        return True, (currency.upper(), Decimal(amount))
    except ValueError:
        return False, "Invalid format, please follow the example formats: eg '50.10' or 'MYR 200.10'."

def parse_username(input: str, usernames: list[str]) -> ParsedResult[str]:
    try:
        username = input.split('@')[1]
        if username not in usernames:
            return False, f"@{username} is not registered, please double check."
        return True, username
    except IndexError:
        return False, "Invalid format, please try again, eg '@user1'."
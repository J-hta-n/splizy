import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from src.bot.convo_utils.parsers import ParsedResult, parse_currency

AMOUNT_INPUT_PATTERN = re.compile(r"^(?:([A-Za-z]{3})\s*)?([^\s]+)$")


def parse_amount(input: str) -> ParsedResult[tuple[Optional[str], Decimal]]:
    input = input.strip()

    if not input:
        return False, "Please enter a valid numeric amount."

    match = AMOUNT_INPUT_PATTERN.match(input)
    if not match:
        return (
            False,
            "Invalid format, please use '110.20', 'SGD110.20', or 'SGD 110.20'.",
        )

    currency, amount = match.group(1), match.group(2)

    try:
        parsed_amount = Decimal(amount)
    except InvalidOperation:
        return False, "Please enter a valid numeric amount."

    if currency is None:
        return True, (None, parsed_amount)

    is_valid, currency = parse_currency(currency)
    if not is_valid:
        return False, currency
    return True, (currency.upper(), parsed_amount)


def parse_multiplier(input: str) -> ParsedResult[float]:
    try:
        mult_val = float(input)
        if mult_val <= 1 or mult_val >= 2:
            return False, "Please enter a number between 1 and 2."
        return True, mult_val

    except (TypeError, ValueError):
        return False, "Invalid input, please input a number between 1 and 2."

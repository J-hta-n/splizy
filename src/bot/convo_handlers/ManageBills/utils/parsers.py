from decimal import Decimal
from typing import Optional

from src.bot.convo_utils.parsers import ParsedResult, parse_currency


def parse_amount(input: str) -> ParsedResult[tuple[Optional[str], Decimal]]:
    try:
        input = input.strip()
        if input.replace(".", "", 1).isdigit():
            return True, (None, Decimal(input))
        currency, amount = input.split(" ")
        if not amount.isdigit():
            return False, "Please enter a valid numeric amount."
        is_valid, currency = parse_currency(currency)
        if not is_valid:
            return False, currency
        return True, (currency.upper(), Decimal(amount))
    except ValueError:
        return (
            False,
            "Invalid format, please follow the example formats: eg '50.10' or 'MYR 200.10'.",
        )


def parse_multiplier(input: str) -> ParsedResult[float]:
    try:
        mult_val = float(input)
        if mult_val <= 1 or mult_val >= 2:
            return False, "Please enter a number between 1 and 2."
        return True, mult_val

    except TypeError:
        return False, "Invalid input, please input a number between 1 and 2."

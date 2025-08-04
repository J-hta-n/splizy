from decimal import Decimal


def get_2dp_str(input: Decimal) -> str:
    return str(round(input, 2))

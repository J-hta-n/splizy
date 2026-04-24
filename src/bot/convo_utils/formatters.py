from decimal import Decimal


def get_2dp_str(input: Decimal) -> str:
    return str(round(input, 2))


def truncate_label(text: str, width: int = 10) -> str:
    if width <= 0:
        return ""
    return f"{text[:width-1]}.." if len(text) > width else text

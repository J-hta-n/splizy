from decimal import Decimal


def get_2dp_str(input: Decimal) -> str:
    return str(round(input, 2))


def truncate_and_pad_label(text: str, width: int = 10) -> str:
    """Return a fixed-width label: truncate+ellipsis if > width, pad if < width."""
    if width <= 0:
        return ""

    if len(text) > width:
        truncate_len = max(0, width - 2)
        return f"{text[:truncate_len]}.."

    return text.ljust(width)

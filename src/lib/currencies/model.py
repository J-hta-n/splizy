from typing import TypedDict


class ExchangeRatesApiResponse(TypedDict):
    success: bool
    timestamp: int
    date: str
    base: str
    rates: dict[str, float]

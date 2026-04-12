import json
from datetime import datetime, timezone
from typing import TypeGuard

from src.lib.currencies.config import EXCHANGE_RATES_FILE_PATH, EXCHANGE_RATES_MAX_AGE
from src.lib.currencies.model import ExchangeRatesApiResponse
from src.lib.logger import get_logger

logger = get_logger(__name__)


def _is_exchange_rates_payload(payload: object) -> TypeGuard[ExchangeRatesApiResponse]:
    if not isinstance(payload, dict):
        return False
    if not isinstance(payload.get("success"), bool):
        return False
    if not isinstance(payload.get("timestamp"), int):
        return False
    if not isinstance(payload.get("date"), str):
        return False
    if not isinstance(payload.get("base"), str):
        return False
    rates = payload.get("rates")
    if not isinstance(rates, dict):
        return False
    return all(
        isinstance(k, str) and isinstance(v, (int, float)) for k, v in rates.items()
    )


def _parse_iso_datetime(date_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return None


def is_cache_stale(payload: ExchangeRatesApiResponse) -> bool:
    fetched_at = _parse_iso_datetime(str(payload.get("date", "")))
    if fetched_at is None:
        return True
    return datetime.now(timezone.utc) - fetched_at > EXCHANGE_RATES_MAX_AGE


def read_cached_exchange_rates() -> ExchangeRatesApiResponse | None:
    if not EXCHANGE_RATES_FILE_PATH.exists():
        return None
    try:
        with EXCHANGE_RATES_FILE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
            if _is_exchange_rates_payload(data):
                return data
            logger.warning(
                "Exchange rates cache has unexpected schema; treating as unavailable."
            )
    except (OSError, json.JSONDecodeError):
        return None
    return None


def convert(amount: float, src_currency: str, dst_currency: str) -> float:
    src = src_currency.upper()
    dst = dst_currency.upper()
    if src == dst:
        return round(float(amount), 3)

    data = read_cached_exchange_rates()
    if data is None:
        logger.error(
            "Exchange rates cache unavailable. Currency conversion cannot proceed."
        )
        raise RuntimeError("Exchange rates cache unavailable")

    rates = data["rates"]
    src_rate = rates.get(src)
    dst_rate = rates.get(dst)
    if not isinstance(src_rate, (int, float)) or not isinstance(dst_rate, (int, float)):
        logger.warning(
            "Missing exchange rate for %s or %s. Returning original amount.", src, dst
        )
        return round(float(amount), 3)

    # API rates are quoted against USD; convert src->USD->dst.
    converted = (float(amount) / float(src_rate)) * float(dst_rate)
    return round(converted, 3)

import json
from datetime import datetime, timezone
from typing import Iterable, TypeGuard

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


def get_exchange_rates_as_of_date() -> str:
    payload = read_cached_exchange_rates()
    if payload is None:
        return "unavailable"

    fetched_at = _parse_iso_datetime(str(payload.get("date", "")))
    if fetched_at is None:
        return "unavailable"

    return fetched_at.strftime("%-d %b")


def convert(amount: float, src_currency: str, dst_currency: str) -> float:
    src = src_currency.upper()
    dst = dst_currency.upper()
    if src == dst:
        return amount

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
        logger.error("Missing exchange rate for %s or %s.", src, dst)
        raise RuntimeError(f"Missing exchange rate for {src} or {dst}")

    if src_rate <= 0 or dst_rate <= 0:
        logger.error("Invalid non-positive exchange rate for %s or %s.", src, dst)
        raise RuntimeError(f"Invalid exchange rate for {src} or {dst}")

    # API rates are quoted against USD; convert src->USD->dst.
    converted = (float(amount) / float(src_rate)) * float(dst_rate)
    return converted


def build_exchange_rate_line(src_currency: str, dst_currency: str) -> str:
    src = src_currency.upper()
    dst = dst_currency.upper()
    as_of_date = get_exchange_rates_as_of_date()

    if src == dst:
        return f"1 {src} = 1 {dst} (as of {as_of_date})"

    try:
        rate = convert(1.0, src, dst)
        return f"1 {src} = {rate:.2f} {dst} (as of {as_of_date})"
    except RuntimeError:
        return f"Exchange rate unavailable for {src}/{dst} (as of {as_of_date})"


def build_exchange_rate_summary(
    src_currencies: Iterable[str], dst_currency: str
) -> str:
    dst = dst_currency.upper()
    as_of_date = get_exchange_rates_as_of_date()
    unique_currencies = sorted(
        {currency.upper() for currency in src_currencies if currency.upper() != dst}
    )
    lines = [f"Exchange rates from {dst} as of {as_of_date}:"]

    if not unique_currencies:
        lines.append(f"All expenses already in {dst}.")
        return "\n".join(lines)

    for src in unique_currencies:
        try:
            rate = convert(1.0, dst, src)
            lines.append(f"1 {dst} = {rate:.2f} {src}")
        except RuntimeError:
            lines.append(f"1 {dst} = unavailable {src}")

    return "\n".join(lines)

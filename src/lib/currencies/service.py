import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from src.lib.currencies.config import (
    EXCHANGE_RATES_BASE,
    EXCHANGE_RATES_FILE_PATH,
    EXCHANGE_RATES_PUBLIC_ENDPOINT,
)
from src.lib.currencies.model import ExchangeRatesApiResponse
from src.lib.currencies.utils import is_cache_stale, read_cached_exchange_rates
from src.lib.logger import get_logger

logger = get_logger(__name__)


def refresh_exchange_rates_if_stale() -> ExchangeRatesApiResponse | None:
    cached_payload = read_cached_exchange_rates()
    if cached_payload is not None and not is_cache_stale(cached_payload):
        return cached_payload  # type: ignore[return-value]

    params = {"base": EXCHANGE_RATES_BASE}
    url = f"{EXCHANGE_RATES_PUBLIC_ENDPOINT}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        logger.warning(
            "Unable to refresh exchange rates. Check the fx endpoint/key configuration."
        )
        return None

    if not isinstance(payload, dict) or not payload.get("success"):
        logger.warning(
            "Exchange rates API responded without success. Check endpoint compatibility."
        )
        return None

    try:
        EXCHANGE_RATES_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with EXCHANGE_RATES_FILE_PATH.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, sort_keys=True)
    except OSError:
        logger.warning("Unable to write exchange rates cache file.")

    return payload  # type: ignore[return-value]

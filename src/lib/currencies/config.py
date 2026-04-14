import json
import os
from datetime import timedelta
from pathlib import Path

EXCHANGE_RATES_PUBLIC_ENDPOINT = "https://api.fxratesapi.com/latest"
EXCHANGE_RATES_BASE = "SGD"
EXCHANGE_RATES_FILE_PATH = Path(__file__).with_name("exchange_rates.json")
EXCHANGE_RATES_MAX_AGE = timedelta(days=1)

# Non-travel assets/instruments we do not treat as user-selectable fiat currencies.
EXCLUDED_NON_FIAT_CODES = {
    "ADA",
    "ARB",
    "BNB",
    "BTC",
    "DAI",
    "DOT",
    "ETH",
    "LTC",
    "SOL",
    "XAG",
    "XAU",
    "XPD",
    "XPT",
    "XRP",
}

DEFAULT_TELEGRAM_TOP_CURRENCY_CODES = [
    "SGD",
    "MYR",
    "EUR",
    "GBP",
    "JPY",
    "KRW",
    "TWD",
    "USD",
    "AUD",
    "NZD",
    "CNY",
    "INR",
    "IDR",
    "HKD",
    "VND",
    "THB",
]


def _read_telegram_top_currency_codes() -> list[str]:
    raw = os.environ.get("TELEGRAM_TOP_CURRENCY_CODES", "").strip()
    if not raw:
        return DEFAULT_TELEGRAM_TOP_CURRENCY_CODES

    parsed = []
    seen = set()
    for token in raw.split(","):
        code = token.strip().upper()
        if len(code) != 3 or not code.isalpha() or code in seen:
            continue
        seen.add(code)
        parsed.append(code)

    return parsed or DEFAULT_TELEGRAM_TOP_CURRENCY_CODES


TELEGRAM_TOP_CURRENCY_CODES = _read_telegram_top_currency_codes()

KNOWN_CURRENCY_DESCRIPTIONS = {
    "SGD": "Singapore Dollar",
    "MYR": "Malaysian Ringgit",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
    "THB": "Thai Baht",
    "VND": "Vietnamese Dong",
    "IDR": "Indonesian Rupiah",
    "PHP": "Philippine Peso",
    "BND": "Brunei Dollar",
    "KHR": "Cambodian Riel",
    "LAK": "Lao Kip",
    "MMK": "Myanmar Kyat",
    "CNY": "Chinese Yuan",
    "HKD": "Hong Kong Dollar",
    "TWD": "New Taiwan Dollar",
    "KRW": "Korean Won",
    "JPY": "Japanese Yen",
    "MNT": "Mongolian Tugrik",
    "RUB": "Russian Ruble",
    "INR": "Indian Rupee",
    "LKR": "Sri Lankan Rupee",
    "BDT": "Bangladeshi Taka",
    "NPR": "Nepalese Rupee",
    "PKR": "Pakistani Rupee",
    "GBP": "British Pound",
    "USD": "US Dollar",
    "CAD": "Canadian Dollar",
    "MXN": "Mexican Peso",
    "EUR": "Euro",
    "CHF": "Swiss Franc",
    "NOK": "Norwegian Krone",
    "SEK": "Swedish Krona",
    "DKK": "Danish Krone",
    "PLN": "Polish Zloty",
    "CZK": "Czech Koruna",
    "HUF": "Hungarian Forint",
    "TRY": "Turkish Lira",
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "QAR": "Qatari Riyal",
    "KWD": "Kuwaiti Dinar",
    "BHD": "Bahraini Dinar",
    "OMR": "Omani Rial",
    "JOD": "Jordanian Dinar",
    "ILS": "Israeli New Shekel",
    "EGP": "Egyptian Pound",
    "ZAR": "South African Rand",
    "MAD": "Moroccan Dirham",
    "KES": "Kenyan Shilling",
    "TZS": "Tanzanian Shilling",
    "NGN": "Nigerian Naira",
}

KNOWN_CURRENCY_SHORTHANDS = {
    "SGD": "S$",
    "MYR": "RM",
    "AUD": "A$",
    "NZD": "NZ$",
    "THB": "฿",
    "VND": "₫",
    "IDR": "Rp",
    "PHP": "₱",
    "BND": "B$",
    "KHR": "KHR",
    "LAK": "LAK",
    "MMK": "MMK",
    "CNY": "¥",
    "HKD": "HK$",
    "TWD": "NT$",
    "KRW": "₩",
    "JPY": "¥",
    "MNT": "₮",
    "RUB": "₽",
    "INR": "₹",
    "LKR": "LKR",
    "BDT": "৳",
    "NPR": "NPR",
    "PKR": "PKR",
    "GBP": "£",
    "USD": "$",
    "CAD": "C$",
    "MXN": "MX$",
    "EUR": "€",
    "CHF": "CHF",
    "NOK": "kr",
    "SEK": "kr",
    "DKK": "kr",
    "PLN": "zl",
    "CZK": "Kc",
    "HUF": "Ft",
    "TRY": "TL",
    "AED": "AED",
    "SAR": "SAR",
    "QAR": "QAR",
    "KWD": "KWD",
    "BHD": "BHD",
    "OMR": "OMR",
    "JOD": "JOD",
    "ILS": "ILS",
    "EGP": "E£",
    "ZAR": "R",
    "MAD": "MAD",
    "KES": "KSh",
    "TZS": "TSh",
    "NGN": "₦",
}


def _read_all_exchange_rate_codes() -> list[str]:
    try:
        payload = json.loads(EXCHANGE_RATES_FILE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []

    rates = payload.get("rates", {})
    if not isinstance(rates, dict):
        return []

    result = []
    for code in rates.keys():
        if not isinstance(code, str):
            continue
        if len(code) != 3 or not code.isalpha() or not code.isupper():
            continue
        if code in EXCLUDED_NON_FIAT_CODES:
            continue
        result.append(code)

    return sorted(result)


ALL_RATE_CODES = _read_all_exchange_rate_codes()

ALL_CURRENCY_CODES = {
    code: KNOWN_CURRENCY_DESCRIPTIONS.get(code, code) for code in ALL_RATE_CODES
}

ALL_CURRENCY_SHORTHAND_MAPPING = {
    code: KNOWN_CURRENCY_SHORTHANDS.get(code, code) for code in ALL_RATE_CODES
}

COMMON_CURRENCY_CODES = {
    code: ALL_CURRENCY_CODES[code]
    for code in TELEGRAM_TOP_CURRENCY_CODES
    if code in ALL_CURRENCY_CODES
}

CURRENCY_SHORTHAND_MAPPING = ALL_CURRENCY_SHORTHAND_MAPPING

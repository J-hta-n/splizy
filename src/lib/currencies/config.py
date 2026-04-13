from datetime import timedelta
from pathlib import Path

ALL_CURRENCY_CODES = None  # Support in future if needed

COMMON_CURRENCY_CODES = {
    "SGD": "Singapore Dollar",
    "MYR": "Malaysian Ringgit",
    "AUD": "Australian Dollar",
    "THB": "Thai Baht",
    "VND": "Vietnamese Dong",
    "IDR": "Indonesian Rupiah",
    "CNY": "Chinese Yuan",
    "KRW": "Korean Won",
    "JPY": "Japanese Yen",
    "INR": "Indian Rupee",
    "GBP": "British Pound",
    "USD": "US Dollar",
    "EUR": "Euro",
}

CURRENCY_SHORTHAND_MAPPING = {
    "SGD": "S$",
    "MYR": "RM",
    "AUD": "A$",
    "THB": "฿",
    "VND": "₫",
    "IDR": "Rp",
    "CNY": "¥",
    "KRW": "₩",
    "JPY": "¥",
    "INR": "₹",
    "GBP": "£",
    "USD": "$",
    "EUR": "€",
}

EXCHANGE_RATES_PUBLIC_ENDPOINT = "https://api.fxratesapi.com/latest"
EXCHANGE_RATES_BASE = "SGD"
EXCHANGE_RATES_FILE_PATH = Path(__file__).with_name("exchange_rates.json")
EXCHANGE_RATES_MAX_AGE = timedelta(days=1)

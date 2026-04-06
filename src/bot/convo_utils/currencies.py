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

COMMON_CURRENCY_CODES_STRING = "\n".join(
    f"{code} ({name})" for code, name in COMMON_CURRENCY_CODES.items()
)

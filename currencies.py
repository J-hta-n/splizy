ALL_CURRENCY_CODES = None  # Support in future if needed

COMMON_CURRENCY_CODES = {
    "MYR": "Malaysian Ringgit",
    "SGD": "Singapore Dollar",
    "GBP": "British Pound",
    "THB": "Thai Baht",
    "JPY": "Japanese Yen",
    "KRW": "Korean Won",
    "CNY": "Chinese Yuan",
    "USD": "US Dollar",
    "EUR": "Euro",
    "AUD": "Australian Dollar",
}

COMMON_CURRENCY_CODES_STRING = "\n".join(
    f"{code} ({name})" for code, name in COMMON_CURRENCY_CODES.items()
)

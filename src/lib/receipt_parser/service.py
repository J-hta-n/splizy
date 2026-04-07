import config
from src.lib.receipt_parser.google_gemini.service import (
    parse_receipt as parse_receipt_with_gemini,
)
from src.lib.receipt_parser.openai_vision.service import (
    parse_receipt as parse_receipt_with_openai,
)


def parse_receipt(image_bytes: bytes):
    provider = (config.RECEIPT_PARSER_PROVIDER or "gemini").strip().lower()
    if provider == "gemini":
        return parse_receipt_with_gemini(image_bytes)
    if provider == "openai":
        return parse_receipt_with_openai(image_bytes)

    raise RuntimeError(
        f"Unsupported receipt parser provider '{provider}'. Supported providers: gemini, openai"
    )

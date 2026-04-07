import config
from src.lib.logger import get_logger
from src.lib.receipt_parser.google_gemini.utils import (
    extract_receipt_payload_with_gemini_vision,
)
from src.lib.receipt_parser.mocks import mock_parsed_receipt
from src.lib.receipt_parser.model import Receipt
from src.lib.receipt_parser.utils import (
    empty_receipt,
    enforce_monthly_quota,
    normalize_receipt_payload,
)

logger = get_logger(__name__)


def parse_receipt(image_bytes: bytes) -> Receipt:
    if config.USE_MOCK_RECEIPT_PARSER:
        return mock_parsed_receipt

    if not image_bytes:
        return empty_receipt()

    enforce_monthly_quota()

    payload = extract_receipt_payload_with_gemini_vision(image_bytes)
    receipt = normalize_receipt_payload(payload)
    logger.info(
        "Receipt parsed with Gemini Vision API: items=%s subtotal=%.2f total=%.2f currency=%s",
        len(receipt.items),
        receipt.subtotal,
        receipt.total,
        receipt.currency,
    )
    return receipt

import config
from src.lib.receipt_parser.mocks import mock_parsed_receipt
from src.lib.receipt_parser.model import Receipt


def parse_receipt(image_bytes: bytes) -> Receipt:
    if config.USE_MOCK_RECEIPT_PARSER:
        return mock_parsed_receipt
    # TODO: Implement receipt parser, likely using some Vision API
    return {}

from abc import ABC, abstractmethod

from src.lib.receipt_parser.model import ParsedReceipt


class ReceiptParser(ABC):

    @abstractmethod
    def parse(self, image_bytes: bytes) -> ParsedReceipt:
        pass

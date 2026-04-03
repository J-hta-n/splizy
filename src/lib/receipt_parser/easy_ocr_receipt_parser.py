import re
from io import BytesIO
from typing import List, Dict, Optional

import easyocr
from PIL import Image

from src.lib.receipt_parser.ReceiptParser import ReceiptParser
from src.lib.receipt_parser.model import ParsedReceipt, ReceiptItem


# Module-level singleton reader (expensive to load, reuse across calls)
_reader = None


def _get_reader():
    """Get or initialize the OCR reader."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


class EasyOCRReceiptParser(ReceiptParser):
    """Internal receipt parser implementation using EasyOCR."""

    def __init__(self):
        """Initialize parser with cached reader."""
        self.reader = _get_reader()

    def parse(self, image_bytes: bytes) -> ParsedReceipt:
        """
        Parse receipt image and extract structured data.
        
        Args:
            image_bytes: Raw image bytes from Telegram
            
        Returns:
            ParsedReceipt with extracted items, taxes, and total
        """
        # Convert bytes to PIL Image
        image = Image.open(BytesIO(image_bytes))

        # Run OCR
        results = self.reader.readtext(image)

        # Extract text from OCR results (results are list of (bbox, text, confidence))
        full_text = "\n".join([text for _, text, _ in results])

        # Parse structured data
        items = self._extract_items(full_text)
        subtotal = self._extract_subtotal(full_text)
        gst = self._extract_gst(full_text)
        service_charge = self._extract_service_charge(full_text)
        total = self._extract_total(full_text)

        return ParsedReceipt(
            items=items,
            subtotal=subtotal,
            gst=gst,
            service_charge=service_charge,
            total=total,
            currency="SGD",
        )

    def _extract_items(self, text: str) -> List[ReceiptItem]:
        """
        Extract line items from receipt text.
        Looks for patterns like:
        - "Item Name x2 @ $5.00" or "Item Name x2 5.00"
        - "Item Name 2 5.00" (quantity and price on same line)
        """
        items = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Skip lines that are clearly headers, totals, or taxes
            if any(
                keyword in line.lower()
                for keyword in [
                    "total",
                    "subtotal",
                    "gst",
                    "service",
                    "tax",
                    "amount",
                    "date",
                    "time",
                    "receipt",
                    "invoice",
                ]
            ):
                continue

            item = self._parse_item_line(line)
            if item:
                items.append(item)

        return items

    def _parse_item_line(self, line: str) -> Optional[ReceiptItem]:
        """
        Parse a single line to extract item name, quantity, and unit price.
        
        Patterns:
        1. "Item Name x2 $5.00" or "Item Name x2 5.00"
        2. "Item Name 2 5.00" (last two numbers are quantity and price)
        3. "Item Name $5.00" (only price)
        """
        # Remove excessive whitespace
        line = re.sub(r"\s+", " ", line).strip()

        # Pattern 1: "Item x<qty> $<price>" or "Item x<qty> <price>"
        match = re.search(r"(.+?)\s+x(\d+(?:\.\d+)?)\s*\$?(\d+(?:\.\d+)?)", line)
        if match:
            name = match.group(1).strip()
            quantity = float(match.group(2))
            unit_price = float(match.group(3))
            return ReceiptItem(
                name=name, quantity=quantity, unit_price=unit_price, subtotal=quantity * unit_price
            )

        # Pattern 2: Try to extract price and quantity from end of line
        # Look for patterns where last token is price and second-to-last is quantity
        tokens = line.split()
        if len(tokens) >= 2:
            try:
                # Try last token as price
                last_token = tokens[-1].replace("$", "").strip()
                price = float(last_token)

                # Try second-to-last as quantity
                if len(tokens) >= 2:
                    second_last = tokens[-2].replace("x", "").strip()
                    try:
                        quantity = float(second_last)
                        # If both parsed, construct item
                        if quantity > 0 and price > 0:
                            name = " ".join(tokens[:-2]).strip()
                            if name:
                                return ReceiptItem(
                                    name=name,
                                    quantity=quantity,
                                    unit_price=price,
                                    subtotal=quantity * price,
                                )
                    except ValueError:
                        pass

                # Pattern 3: Only price at end, quantity defaults to 1
                if price > 0:
                    name = " ".join(tokens[:-1]).strip()
                    if name and len(name) > 2:  # Ensure name is reasonable
                        return ReceiptItem(name=name, quantity=1, unit_price=price)
            except ValueError:
                pass

        return None

    def _extract_subtotal(self, text: str) -> Optional[float]:
        """Extract subtotal amount from receipt text."""
        return self._extract_amount_for_keyword(text, ["subtotal", "sub total", "subtotal"])

    def _extract_total(self, text: str) -> Optional[float]:
        """Extract total amount from receipt text."""
        return self._extract_amount_for_keyword(text, ["total"])

    def _extract_gst(self, text: str) -> Optional[float]:
        """Extract GST (Goods and Services Tax) amount. Singapore uses 8% GST."""
        return self._extract_amount_for_keyword(text, ["gst", "gst 8%", "tax"])

    def _extract_service_charge(self, text: str) -> Optional[float]:
        """Extract service charge amount."""
        return self._extract_amount_for_keyword(
            text, ["service charge", "service", "service fee", "svc chrg", "svc"]
        )

    def _extract_amount_for_keyword(self, text: str, keywords: List[str]) -> Optional[float]:
        """
        Extract amount value associated with given keywords.
        Looks for patterns like "KEYWORD $12.50" or "KEYWORD 12.50"
        """
        text_lower = text.lower()

        for keyword in keywords:
            # Look for the keyword and capture the amount that follows
            pattern = rf"{re.escape(keyword)}\s*:?\s*\$?(\d+(?:\.\d+)?)"
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None


# Public API
def parse(image_bytes: bytes) -> ParsedReceipt:
    """
    Parse a receipt image and extract structured data.
    
    Args:
        image_bytes: Raw image bytes from Telegram or any source
        
    Returns:
        ParsedReceipt with extracted items, taxes, and total
        
    Example:
        from src.lib.receipt_parser.easy_ocr_receipt_parser import parse
        
        # In your telegram handler
        image_bytes = await photo_file.download_as_bytearray()
        receipt = parse(bytes(image_bytes))
        print(f"Found {len(receipt['items'])} items")
    """
    parser = EasyOCRReceiptParser()
    return parser.parse(image_bytes)

from typing import List, Optional

from pydantic import BaseModel


class ReceiptItem(BaseModel):
    name: str
    quantity: float = 1
    unit_price: float
    subtotal: Optional[float] = None


class ParsedReceipt(BaseModel):
    items: List[ReceiptItem]
    subtotal: Optional[float] = None
    service_charge: Optional[float] = None
    gst: Optional[float] = None
    total: Optional[float] = None
    currency: str = "SGD"

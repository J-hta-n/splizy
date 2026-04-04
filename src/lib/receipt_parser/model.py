from typing import List, Literal, Optional

from pydantic import BaseModel


class ReceiptItem(BaseModel):
    name: str
    quantity: int = 1
    subtotal: Optional[float] = None


class ParsedReceipt(BaseModel):
    items: List[ReceiptItem]
    subtotal: Optional[float] = None
    service_charge: Optional[float] = None
    gst: Optional[float] = None
    total: Optional[float] = None
    currency: str = "SGD"


class MiniappPayload(BaseModel):
    users: List[str]
    receipt: ParsedReceipt
    step: Literal["indiv", "shared"]

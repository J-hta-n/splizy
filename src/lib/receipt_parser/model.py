from typing import List, Optional

from pydantic import BaseModel, Field


class IndivAssignment(BaseModel):
    username: str
    quantity: int

class ReceiptItem(BaseModel):
    name: str
    quantity: int = 1
    subtotal: Optional[float] = None
    indiv: List[IndivAssignment] = Field(default_factory=list)
    shared: List[str] = Field(default_factory=list)

class Receipt(BaseModel):
    """
    Represents the parsed receipt data + individual and shared item assignments
    for bill splitting miniapp
    """
    items: List[ReceiptItem]
    subtotal: Optional[float] = None
    service_charge: Optional[float] = None
    gst: Optional[float] = None
    total: Optional[float] = None
    currency: str = "SGD"

class MiniappLastReceipt(BaseModel):
    users: List[str]
    receipt: Receipt
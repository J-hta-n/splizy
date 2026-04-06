from typing import List

from pydantic import BaseModel, Field


class IndivAssignment(BaseModel):
    username: str
    quantity: int


class ReceiptItem(BaseModel):
    name: str
    quantity: int = 1
    subtotal: float
    indiv: List[IndivAssignment] = Field(default_factory=list)
    shared: List[str] = Field(default_factory=list)


class Receipt(BaseModel):
    """
    Represents the parsed receipt data + individual and shared item assignments
    for bill splitting miniapp
    """

    items: List[ReceiptItem]
    subtotal: float
    service_charge: float
    gst: float
    total: float
    currency: str = "SGD"


class MiniappReceipt(BaseModel):
    users: List[str]
    receipt: Receipt

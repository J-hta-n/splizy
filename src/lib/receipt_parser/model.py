from typing import Any, Dict, List

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


RECEIPT_JSON_SCHEMA: Dict[str, Any] = {
    "name": "receipt",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["items", "subtotal", "service_charge", "gst", "total", "currency"],
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "quantity", "subtotal"],
                    "properties": {
                        "name": {"type": "string"},
                        "quantity": {"type": "integer", "minimum": 1},
                        "subtotal": {"type": "number", "minimum": 0},
                    },
                },
            },
            "subtotal": {"type": "number", "minimum": 0},
            "service_charge": {"type": "number", "minimum": 0},
            "gst": {"type": "number", "minimum": 0},
            "total": {"type": "number", "minimum": 0},
            "currency": {"type": "string"},
        },
    },
}

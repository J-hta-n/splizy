from __future__ import annotations

from typing import NotRequired, TypeAlias, TypedDict

# Db schema DTOs
GroupId: TypeAlias = int
ExpenseId: TypeAlias = str
TempReceiptId: TypeAlias = int
CurrencyCode: TypeAlias = str


class ReceiptIndivAssignment(TypedDict):
    username: str
    quantity: int


class ReceiptItemData(TypedDict):
    name: str
    quantity: int
    subtotal: float
    indiv: list[ReceiptIndivAssignment]
    shared: list[str]


class ReceiptData(TypedDict):
    items: list[ReceiptItemData]
    subtotal: float
    service_charge: float
    gst: float
    total: float
    currency: CurrencyCode


class PayeeData(TypedDict):
    user: str
    amount: float


class ExpenseRow(TypedDict):
    id: ExpenseId
    group_id: GroupId
    title: str
    amount: str
    paid_by: str
    currency: CurrencyCode
    is_equal_split: bool
    payees: list[PayeeData]
    multiplier: NotRequired[str | None]
    receipt: NotRequired[ReceiptData | None]
    created_at: NotRequired[str]


class GroupRow(TypedDict):
    id: GroupId
    expense_currency: NotRequired[CurrencyCode | None]
    settleup_currency: NotRequired[CurrencyCode | None]
    created_at: NotRequired[str]


class SplizyUserRow(TypedDict):
    group_id: GroupId
    username: str
    id: NotRequired[int]
    created_at: NotRequired[str]


class MiniappReceiptData(TypedDict):
    users: list[str]
    receipt: ReceiptData


class TempReceiptRow(TypedDict):
    id: TempReceiptId
    group_id: GroupId
    title: NotRequired[str | None]
    paid_by: NotRequired[str | None]
    expense_id: NotRequired[ExpenseId | None]
    last_receipt: MiniappReceiptData
    created_at: NotRequired[str]


# Payload schema DTOs
class GroupUpsert(TypedDict):
    id: GroupId
    expense_currency: NotRequired[CurrencyCode | None]
    settleup_currency: NotRequired[CurrencyCode | None]


class GroupUpdate(TypedDict, total=False):
    expense_currency: CurrencyCode
    settleup_currency: CurrencyCode


class SplizyUserInsert(TypedDict):
    group_id: GroupId
    username: str


class ExpenseInsert(TypedDict):
    group_id: GroupId
    title: str
    amount: str
    paid_by: str
    currency: CurrencyCode
    is_equal_split: bool
    payees: list[PayeeData]
    multiplier: NotRequired[str | None]
    receipt: NotRequired[ReceiptData | None]


class ExpenseUpdate(TypedDict, total=False):
    group_id: GroupId
    title: str
    amount: str
    paid_by: str
    currency: CurrencyCode
    is_equal_split: bool
    payees: list[PayeeData]
    multiplier: str | None
    receipt: ReceiptData | None


class TempReceiptInsert(TypedDict):
    group_id: GroupId
    title: NotRequired[str | None]
    paid_by: NotRequired[str | None]
    expense_id: NotRequired[ExpenseId | None]
    last_receipt: MiniappReceiptData


class TempReceiptUpdate(TypedDict, total=False):
    title: str | None
    paid_by: str | None
    expense_id: ExpenseId | None
    last_receipt: MiniappReceiptData

from __future__ import annotations

from decimal import Decimal
from typing import Literal, TypedDict, cast

from telegram.ext import ContextTypes

from src.lib.splizy_repo.model import ExpenseId, ExpenseRow, ReceiptData


class ManageBillsUserData(TypedDict, total=False):
    # View all
    expenses: list[ExpenseRow]
    expense_index: int
    viewall_page: int
    viewall_is_collapsed: bool
    # Add, view, edit
    all_participants: list[str]
    is_equal_split: bool
    split_type: Literal["equal_all", "equal_some", "custom"]
    custom_amounts: list[float | Decimal]
    has_mult: bool
    mult_val: float | Decimal
    expense_id: ExpenseId
    expense_name: str
    amount: float | Decimal
    paid_by: str
    currency: str
    receipt: ReceiptData | None
    receipt_detail_message_ids: list[int]


def get_managebills_user_data(
    context: ContextTypes.DEFAULT_TYPE,
) -> ManageBillsUserData:
    return cast(ManageBillsUserData, context.user_data)

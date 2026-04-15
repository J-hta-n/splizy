from __future__ import annotations

from decimal import Decimal
from typing import TypedDict, cast

from telegram.ext import ContextTypes

from src.lib.splizy_repo.model import ExpenseId, ExpenseRow, ReceiptData


class ManageBillsUserData(TypedDict, total=False):
    expenses: list[ExpenseRow]
    all_participants: list[str]
    expense_index: int
    expense_id: ExpenseId
    expense_name: str
    amount: float | Decimal
    paid_by: str
    currency: str
    is_equal_split: bool
    receipt: ReceiptData | None
    receipt_detail_message_ids: list[int]


def get_managebills_user_data(
    context: ContextTypes.DEFAULT_TYPE,
) -> ManageBillsUserData:
    return cast(ManageBillsUserData, context.user_data)

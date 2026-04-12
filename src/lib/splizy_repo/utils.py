from __future__ import annotations

from typing import Any, Mapping, Sequence, cast

from src.lib.splizy_repo.model import (
    ExpenseInsert,
    GroupId,
    MiniappReceiptData,
    PayeeData,
    ReceiptData,
    SplizyUserRow,
    TempReceiptInsert,
)


def get_usernames(users: Sequence[SplizyUserRow]) -> list[str]:
    return [user["username"] for user in users]


def build_expense_payload(
    group_id: GroupId, data: Mapping[str, Any], payees: Sequence[PayeeData]
) -> ExpenseInsert:
    payload: ExpenseInsert = {
        "group_id": group_id,
        "title": str(data["expense_name"]),
        "amount": str(data["amount"]),
        "paid_by": str(data["paid_by"]),
        "currency": str(data["currency"]),
        "is_equal_split": bool(data["is_equal_split"]),
        "payees": list(payees),
        "multiplier": (
            str(data["mult_val"]) if ("has_mult" in data and data["has_mult"]) else None
        ),
    }
    return payload


def build_temp_receipt_payload(
    group_id: GroupId, usernames: Sequence[str], receipt: ReceiptData
) -> TempReceiptInsert:
    last_receipt: MiniappReceiptData = {
        "users": list(usernames),
        "receipt": cast(ReceiptData, receipt),
    }
    payload: TempReceiptInsert = {
        "group_id": group_id,
        "title": None,
        "paid_by": None,
        "expense_id": None,
        "last_receipt": last_receipt,
    }
    return payload

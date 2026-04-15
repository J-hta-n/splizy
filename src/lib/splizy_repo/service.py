from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.lib.splizy_repo.model import (
    ExpenseRow,
    ExpenseUpdate,
    GroupId,
    PayeeData,
    ReceiptData,
    TempReceiptRow,
    TempReceiptUpdate,
)
from src.lib.splizy_repo.repo import repo
from src.lib.splizy_repo.utils import (
    build_expense_payload,
    build_temp_receipt_payload,
    get_usernames,
)


def get_group_expense_setup(group_id: GroupId) -> tuple[str, list[str]]:
    group = repo.get_group(group_id)
    users = repo.list_group_users(group_id)
    expense_currency = (group.get("expense_currency") if group else None) or "SGD"
    return expense_currency, get_usernames(users)


def save_expense(
    group_id: GroupId, data: Mapping[str, Any], payees: Sequence[PayeeData]
) -> ExpenseRow:
    payload = build_expense_payload(group_id, data, payees)
    expense_id = data.get("expense_id")
    if expense_id:
        update_payload: ExpenseUpdate = {
            key: value for key, value in payload.items() if key != "group_id"
        }
        updated = repo.update_expense(str(expense_id), update_payload)
        if updated is None:
            raise ValueError(f"Updated expense not found for id={expense_id}")
        return updated
    return repo.create_expense(payload)


def prepare_temp_receipt_review(
    group_id: GroupId, receipt: ReceiptData
) -> TempReceiptRow | None:
    users = repo.list_group_users(group_id)
    payload = build_temp_receipt_payload(group_id, get_usernames(users), receipt)
    existing = repo.get_latest_temp_receipt(group_id)
    if existing is None:
        return repo.create_temp_receipt(payload)

    update_payload: TempReceiptUpdate = {
        "title": payload.get("title"),
        "paid_by": payload.get("paid_by"),
        "expense_id": payload.get("expense_id"),
        "last_receipt": payload["last_receipt"],
    }
    return repo.update_temp_receipt(existing["id"], update_payload)


def get_latest_temp_receipt_with_expense(
    group_id: GroupId,
) -> tuple[TempReceiptRow | None, ExpenseRow | None]:
    temp_receipt = repo.get_latest_temp_receipt(group_id)
    if temp_receipt is None:
        return None, None

    expense_id = temp_receipt.get("expense_id")
    if not expense_id:
        return temp_receipt, None

    return temp_receipt, repo.get_expense(expense_id)

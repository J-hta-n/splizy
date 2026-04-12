from __future__ import annotations

from typing import cast

from src.lib.splizy_repo.database import supabase
from src.lib.splizy_repo.model import (
    ExpenseId,
    ExpenseInsert,
    ExpenseRow,
    ExpenseUpdate,
    GroupId,
    GroupRow,
    GroupUpdate,
    GroupUpsert,
    SplizyUserInsert,
    SplizyUserRow,
    TempReceiptId,
    TempReceiptInsert,
    TempReceiptRow,
    TempReceiptUpdate,
)


def _first_or_none(rows: list[object] | None) -> object | None:
    if not rows:
        return None
    return rows[0]


class SplizyRepo:
    def ensure_group(self, payload: GroupUpsert) -> None:
        supabase.table("groups").upsert(payload).execute()

    def get_group(self, group_id: GroupId) -> GroupRow | None:
        response = (
            supabase.table("groups").select("*").eq("id", group_id).limit(1).execute()
        )
        return cast(GroupRow | None, _first_or_none(response.data))

    def update_group(self, group_id: GroupId, payload: GroupUpdate) -> GroupRow | None:
        supabase.table("groups").update(payload).eq("id", group_id).execute()
        return self.get_group(group_id)

    def list_group_users(self, group_id: GroupId) -> list[SplizyUserRow]:
        response = (
            supabase.table("splizy_users")
            .select("*")
            .eq("group_id", group_id)
            .execute()
        )
        return cast(list[SplizyUserRow], response.data or [])

    def insert_group_users(
        self, payload: list[SplizyUserInsert]
    ) -> list[SplizyUserRow]:
        if not payload:
            return []
        response = supabase.table("splizy_users").insert(payload).execute()
        return cast(list[SplizyUserRow], response.data or [])

    def list_expenses(self, group_id: GroupId) -> list[ExpenseRow]:
        response = (
            supabase.table("expenses")
            .select("*")
            .eq("group_id", group_id)
            .order("created_at", desc=True)
            .execute()
        )
        return cast(list[ExpenseRow], response.data or [])

    def get_expense(self, expense_id: ExpenseId) -> ExpenseRow | None:
        response = (
            supabase.table("expenses")
            .select("*")
            .eq("id", expense_id)
            .limit(1)
            .execute()
        )
        return cast(ExpenseRow | None, _first_or_none(response.data))

    def create_expense(self, payload: ExpenseInsert) -> ExpenseRow:
        response = supabase.table("expenses").insert(payload).execute()
        created = cast(ExpenseRow | None, _first_or_none(response.data))
        if created is None:
            raise ValueError("Failed to create expense")
        return created

    def update_expense(
        self, expense_id: ExpenseId, payload: ExpenseUpdate
    ) -> ExpenseRow | None:
        supabase.table("expenses").update(payload).eq("id", expense_id).execute()
        return self.get_expense(expense_id)

    def delete_expense(self, expense_id: ExpenseId) -> None:
        supabase.table("expenses").delete().eq("id", expense_id).execute()

    def get_temp_receipt(self, temp_receipt_id: TempReceiptId) -> TempReceiptRow | None:
        response = (
            supabase.table("temp_receipts")
            .select("*")
            .eq("id", temp_receipt_id)
            .limit(1)
            .execute()
        )
        return cast(TempReceiptRow | None, _first_or_none(response.data))

    def get_latest_temp_receipt(self, group_id: GroupId) -> TempReceiptRow | None:
        response = (
            supabase.table("temp_receipts")
            .select("*")
            .eq("group_id", group_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return cast(TempReceiptRow | None, _first_or_none(response.data))

    def create_temp_receipt(self, payload: TempReceiptInsert) -> TempReceiptRow:
        response = supabase.table("temp_receipts").insert(payload).execute()
        created = cast(TempReceiptRow | None, _first_or_none(response.data))
        if created is None:
            raise ValueError("Failed to create temp receipt")
        return created

    def update_temp_receipt(
        self, temp_receipt_id: TempReceiptId, payload: TempReceiptUpdate
    ) -> TempReceiptRow | None:
        supabase.table("temp_receipts").update(payload).eq(
            "id", temp_receipt_id
        ).execute()
        return self.get_temp_receipt(temp_receipt_id)

    def upsert_latest_temp_receipt(
        self, group_id: GroupId, payload: TempReceiptInsert | TempReceiptUpdate
    ) -> TempReceiptRow | None:
        existing = self.get_latest_temp_receipt(group_id)
        if existing is None:
            return self.create_temp_receipt(cast(TempReceiptInsert, payload))
        return self.update_temp_receipt(
            existing["id"], cast(TempReceiptUpdate, payload)
        )


repo = SplizyRepo()

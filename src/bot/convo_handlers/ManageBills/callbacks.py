from __future__ import annotations

from typing import Final

EDIT_EXPENSE: Final = "edit_expense"
DELETE_EXPENSE: Final = "delete_expense"
GO_BACK: Final = "go_back"
SHOW_RECEIPT: Final = "show_receipt"
HIDE_RECEIPT: Final = "hide_receipt"

CANCEL_DELETE: Final = "cancel_delete"
CONFIRM_DELETE: Final = "confirm_delete"

VIEW_EXPENSE_PATTERN: Final = r"^\d+$"
EDIT_OR_GO_BACK_PATTERN: Final = (
    r"^(edit_expense|delete_expense|go_back|show_receipt|hide_receipt)$"
)
DELETE_EXPENSE_PATTERN: Final = r"^(cancel_delete|confirm_delete)$"

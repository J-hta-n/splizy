from __future__ import annotations

from typing import Final

EDIT_EXPENSE: Final = "edit_expense"
DELETE_EXPENSE: Final = "delete_expense"
GO_BACK: Final = "go_back"
SHOW_RECEIPT: Final = "show_receipt"
HIDE_RECEIPT: Final = "hide_receipt"

VIEW_SELECT_PREFIX: Final = "view_select:"
VIEW_PAGE_PREV: Final = "view_page_prev"
VIEW_PAGE_NEXT: Final = "view_page_next"
VIEW_TOGGLE_HIDE: Final = "view_toggle_hide"
VIEW_TOGGLE_SHOW: Final = "view_toggle_show"
VIEW_ALL_ENTRIES: Final = "view_all_entries"

CANCEL_DELETE: Final = "cancel_delete"
CONFIRM_DELETE: Final = "confirm_delete"

VIEW_EXPENSE_PATTERN: Final = (
    r"^(view_select:\d+|view_page_prev|view_page_next|view_toggle_hide|view_toggle_show|view_all_entries)$"
)
EDIT_OR_GO_BACK_PATTERN: Final = (
    r"^(edit_expense|delete_expense|go_back|show_receipt|hide_receipt)$"
)
DELETE_EXPENSE_PATTERN: Final = r"^(cancel_delete|confirm_delete)$"

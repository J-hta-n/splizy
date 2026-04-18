from decimal import Decimal

from src.bot.convo_handlers.ManageBills.context import ManageBillsUserData
from src.lib.currencies.utils import get_shorthand_currency
from src.lib.splizy_repo.model import ExpenseRow, PayeeData


def build_payees(data: ManageBillsUserData) -> list[PayeeData]:
    if data["split_type"] in ["equal_all", "equal_some"]:
        involved = (
            data["all_participants"]
            if data["split_type"] == "equal_all"
            else data["selected_participants"]
        )
        if not involved:
            return []
        amount_per_pax = data["amount"] / len(involved)
        return [
            {
                "user": username,
                "amount": float(amount_per_pax) if username in involved else 0,
            }
            for username in data["all_participants"]
        ]

    # Custom split
    has_mult = data.get("has_mult", False)
    mult_val = Decimal(str(data.get("mult_val", 1))) if has_mult else Decimal("1")
    payees: list[PayeeData] = []
    for idx, (username, amount) in enumerate(
        zip(data["all_participants"], data["custom_amounts"])
    ):
        final_amount = Decimal(str(amount)) * mult_val
        payees.append(
            {
                "user": username,
                "amount": (
                    float(final_amount) if data["participant_selections"][idx] else 0
                ),
            }
        )
    return payees


def format_saved_expense_summary(
    expense: ExpenseRow,
    source_label: str = "Expense",
) -> str:
    currency_symbol = get_shorthand_currency(expense.get("currency"))
    total_amount = float(expense.get("amount"))
    paid_by = expense.get("paid_by")
    user_spendings = "\n".join(
        [
            f"@{payee['user']} - {currency_symbol}{payee['amount']:.2f}"
            for payee in expense.get("payees")
        ]
    )

    expense_summary = (
        f"{source_label} saved successfully! Details:\n"
        + f"Total: {currency_symbol}{total_amount:.2f}\n"
        + f"Paid by: @{paid_by}\n"
        + f"User spendings:\n{user_spendings}"
    )

    return expense_summary


def populate_context_for_selected_expense_from_viewall(
    data: ManageBillsUserData, expense: ExpenseRow
):
    payees = expense["payees"]
    participants = [entry["user"] for entry in payees]
    amounts = [float(entry["amount"]) for entry in payees]

    data["all_participants"] = participants
    data["is_equal_split"] = expense["is_equal_split"]
    if expense["is_equal_split"]:
        is_all_involved = all([amount > 0 for amount in amounts])
        data["split_type"] = "equal_all" if is_all_involved else "equal_some"
    else:
        data["split_type"] = "custom"
    data["selected_participants"] = [
        entry["user"] for entry in payees if float(entry["amount"]) > 0
    ]
    data["custom_amounts"] = amounts
    data["has_mult"] = expense.get("multiplier") is not None
    data["mult_val"] = expense.get("multiplier")

    data["expense_id"] = expense["id"]
    data["expense_name"] = expense["title"]
    data["amount"] = Decimal(str(expense["amount"]))
    data["paid_by"] = expense["paid_by"]
    data["currency"] = expense["currency"]
    data["receipt"] = expense["receipt"]


def initialise_viewall_context(data: ManageBillsUserData, expenses):
    data["expenses"] = expenses
    data["viewall_page"] = 0
    data["viewall_is_collapsed"] = False

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
    user_amounts: list[tuple[str, float]] | None = None,
) -> str:
    currency_code = expense.get("currency", "")
    currency_symbol = get_shorthand_currency(currency_code)

    try:
        total_amount = float(expense.get("amount") or 0)
    except (TypeError, ValueError):
        total_amount = 0.0

    paid_by = expense.get("paid_by")
    paid_by_label = f"@{paid_by}" if paid_by else "-"

    if user_amounts is None:
        payees = expense.get("payees") or []
        user_amounts = [
            (
                str(entry.get("user") or entry.get("username") or ""),
                float(entry.get("amount") or 0),
            )
            for entry in payees
            if (entry.get("user") or entry.get("username"))
        ]

    lines = [
        f"{source_label} saved successfully! Details:",
        f"Total: {currency_symbol}{total_amount:.2f}",
        f"Paid by: {paid_by_label}",
        "User spendings:",
    ]

    if user_amounts:
        lines.extend(
            [
                f"@{username} - {currency_symbol}{amount:.2f}"
                for username, amount in user_amounts
            ]
        )
    else:
        lines.append("-")

    return "\n".join(lines)


def populate_context_for_selected_expense_from_viewall(context, expense):
    payees = expense["payees"]
    payees_map = {entry["user"]: Decimal(str(entry["amount"])) for entry in payees}
    participants = list(dict.fromkeys(entry["user"] for entry in payees))

    context.user_data["all_participants"] = participants
    context.user_data["is_equal_split"] = expense["is_equal_split"]
    if expense["is_equal_split"]:
        context.user_data["split_type"] = "equal_all"
    else:
        context.user_data["split_type"] = "custom"
    context.user_data["selected_participants"] = [
        entry["user"] for entry in payees if entry["user"] in participants
    ]
    context.user_data["participant_selections"] = [
        username in context.user_data["selected_participants"]
        for username in participants
    ]
    context.user_data["custom_amounts"] = [
        payees_map.get(username, Decimal("0")) for username in participants
    ]
    context.user_data["has_mult"] = expense.get("multiplier") is not None
    context.user_data["mult_val"] = expense.get("multiplier")

    context.user_data["expense_id"] = expense["id"]
    context.user_data["expense_name"] = expense["title"]
    context.user_data["amount"] = Decimal(str(expense["amount"]))
    context.user_data["paid_by"] = expense["paid_by"]
    context.user_data["currency"] = expense["currency"]
    context.user_data["receipt"] = expense["receipt"]

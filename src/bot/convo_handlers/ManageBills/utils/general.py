from decimal import Decimal

from src.bot.convo_utils.formatters import get_2dp_str


def build_payees(data: dict) -> list[dict]:
    if data["split_type"] in ["equal_all", "equal_some"]:
        participants = (
            data["all_participants"]
            if data["split_type"] == "equal_all"
            else data["selected_participants"]
        )
        if not participants:
            return []
        amount_per_pax = data["amount"] / len(participants)
        return [
            {
                "user": username,
                "amount": float(amount_per_pax),
            }
            for username in participants
        ]

    # Custom split
    has_mult = data.get("has_mult", False)
    mult_val = Decimal(str(data.get("mult_val", 1))) if has_mult else Decimal("1")
    payees: list[dict] = []
    for idx, (username, amount) in enumerate(
        zip(data["all_participants"], data["custom_amounts"])
    ):
        if not data["participant_selections"][idx]:
            continue
        final_amount = Decimal(str(amount)) * mult_val
        payees.append(
            {
                "user": username,
                "amount": float(final_amount),
            }
        )
    return payees


def get_bill_summary(data):
    if data["split_type"] == "equal_all":
        split_status = f"equally among everyone ({data['currency']} {get_2dp_str(data['amount']/len(data['all_participants']))} per person)"
    elif data["split_type"] == "equal_some":
        selected_participants = data["selected_participants"]
        split_status = f"equally among {len(selected_participants)} people (@{', @'.join(selected_participants)}, {data['currency']} {get_2dp_str(data['amount']/len(selected_participants))} per person)"
    elif data["split_type"] == "custom":
        mult_val = data["mult_val"] if data["has_mult"] else 1
        custom_split_str = "\n".join(
            f"@{username} - {get_2dp_str(Decimal(str(amount))*Decimal(mult_val))}"
            for idx, (username, amount) in enumerate(
                zip(data["selected_participants"], data["custom_amounts"])
            )
            if data["participant_selections"][idx]
        )
        split_status = f"by custom amounts in {data['currency']}{' (Receipt details available)' if data['receipt'] is not None else ''}\n{custom_split_str}"

    summary = (
        f"---Bill for {data['expense_name']}---\n"
        f"Paid by: @{data['paid_by']}\n"
        f"Currency & Amount: {data['currency']} {get_2dp_str(data['amount'])}\n"
        f"Split: {split_status}\n"
    )
    return summary


def get_bill_summary_with_receipt(data):
    receipt = data["receipt"]
    items = receipt["items"]
    currency = data["currency"]

    participants = data["all_participants"]

    spendings = {username: Decimal("0") for username in participants}
    spending_details = {username: [] for username in participants}

    subtotal = Decimal(str(receipt["subtotal"]))
    total = Decimal(str(receipt["total"]))
    factor = total / subtotal

    for item in items:
        item_name = item["name"]
        quantity = Decimal(str(item["quantity"]))
        item_subtotal = Decimal(str(item["subtotal"]))

        if quantity <= 0:
            continue

        unit_price = (item_subtotal / quantity) * factor

        indiv_qty = Decimal("0")
        for entry in item["indiv"]:
            username = entry["username"]
            entry_qty = Decimal(str(entry["quantity"]))
            if entry_qty <= 0:
                continue

            indiv_qty += entry_qty
            line_subtotal = unit_price * entry_qty
            if username not in spendings:
                spendings[username] = Decimal("0")
                spending_details[username] = []
            spendings[username] += line_subtotal
            spending_details[username].append((entry_qty, item_name, line_subtotal))

        shared_qty = quantity - indiv_qty
        shared_users = item["shared"]
        if shared_qty <= 0 or len(shared_users) < 2:
            continue

        qty_per_user = shared_qty / Decimal(str(len(shared_users)))
        amount_per_user = unit_price * qty_per_user
        for username in shared_users:
            spendings[username] += amount_per_user
            spending_details[username].append(
                (qty_per_user, item_name, amount_per_user)
            )

    def _format_qty(qty: Decimal) -> str:
        rounded = qty.quantize(Decimal("0.01"))
        if rounded == rounded.to_integral_value():
            return str(int(rounded))
        return get_2dp_str(rounded)

    users_for_output = participants
    user_blocks = []
    for username in users_for_output:
        total_spent = spendings[username]
        details = spending_details[username]
        lines = [f"@{username} - ${get_2dp_str(total_spent)}"]
        if details:
            lines.extend(
                f"- {_format_qty(qty)} {name} (${get_2dp_str(amount)})"
                for qty, name, amount in details
            )
        user_blocks.append("\n".join(lines))

    user_spendings = "\n\n".join(user_blocks) if user_blocks else "-"

    summary = (
        f"---Bill for {data['expense_name']}---\n"
        f"Paid by: @{data['paid_by']}\n"
        f"Amount: {currency} {get_2dp_str(data['amount'])}\n"
        f"User spendings (in {currency}):\n\n{user_spendings}"
    )
    return summary


def populate_context_for_selected_expense_from_viewall(context, expense):
    payees = expense["payees"]
    payees_map = {entry["user"]: Decimal(str(entry["amount"])) for entry in payees}
    participants = list(dict.fromkeys(entry["user"] for entry in payees))

    context.user_data["all_participants"] = participants
    context.user_data["has_mult"] = expense.get("multiplier") is not None
    context.user_data["mult_val"] = expense.get("multiplier")
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
    context.user_data["expense_id"] = expense["id"]
    context.user_data["expense_name"] = expense["title"]
    context.user_data["amount"] = Decimal(str(expense["amount"]))
    context.user_data["paid_by"] = expense["paid_by"]
    context.user_data["currency"] = expense["currency"]
    context.user_data["is_equal_split"] = expense["is_equal_split"]
    context.user_data["receipt"] = expense["receipt"]

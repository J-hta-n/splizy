from decimal import Decimal

from src.bot.convo_handlers.ManageBills.context import ManageBillsUserData
from src.bot.convo_utils.formatters import get_2dp_str


def get_bill_summary(data: ManageBillsUserData) -> str:
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
        split_status = f"by custom amounts in {data['currency']}{' (Receipt details available)' if data.get('receipt') else ''}\n{custom_split_str}"

    summary = (
        f"---Bill for {data['expense_name']}---\n"
        f"Paid by: @{data['paid_by']}\n"
        f"Currency & Amount: {data['currency']} {get_2dp_str(data['amount'])}\n"
        f"Split: {split_status}\n"
    )
    return summary


def get_bill_summary_with_receipt(data: ManageBillsUserData) -> str:
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

from decimal import Decimal

from src.bot.convo_utils.formatters import get_2dp_str
from src.lib.splizy_repo.model import ReceiptData


def format_receipt_spendings(
    receipt: ReceiptData, participants: list[str], currency_symbol: str
) -> str:
    spendings = {username: Decimal("0") for username in participants}
    spending_details = {username: [] for username in participants}

    subtotal = Decimal(str(receipt["subtotal"]))
    total = Decimal(str(receipt["total"]))
    factor = total / subtotal if subtotal else Decimal("0")

    for item in receipt["items"]:
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
            if username not in spendings:
                spendings[username] = Decimal("0")
                spending_details[username] = []
            spendings[username] += amount_per_user
            spending_details[username].append(
                (qty_per_user, item_name, amount_per_user)
            )

    def _format_qty(qty: Decimal) -> str:
        rounded = qty.quantize(Decimal("0.01"))
        if rounded == rounded.to_integral_value():
            return str(int(rounded))
        return get_2dp_str(rounded)

    user_blocks: list[str] = []
    for username in participants:
        total_spent = spendings[username]
        details = spending_details[username]
        lines = [f"@{username} - {currency_symbol}{get_2dp_str(total_spent)}"]
        if details:
            lines.extend(
                f"- {_format_qty(qty)} {name} ({currency_symbol}{get_2dp_str(amount)})"
                for qty, name, amount in details
            )
        user_blocks.append("\n".join(lines))

    return "\n\n".join(user_blocks) if user_blocks else "-"
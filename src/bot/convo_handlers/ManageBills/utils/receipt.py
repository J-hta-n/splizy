from src.lib.receipt_parser.model import MiniappReceipt, Receipt


# Deprecated - kept in case needed again in future
def compute_spending_from_last_receipt(last_receipt: MiniappReceipt) -> dict:
    res = {user: 0.0 for user in last_receipt.users}
    receipt = last_receipt.receipt
    for item in receipt.items:
        unit_cost = item.subtotal / item.quantity
        # Update indiv spendings
        indivs_qty = 0
        for user, qty in item.indiv:
            res[user] += unit_cost * qty
            indivs_qty += qty
        # Update shared spendings
        shared_qty = item.quantity - indivs_qty
        shared_cost = unit_cost * shared_qty / len(item.shared)
        for user in item.shared:
            res[user] += shared_cost
    return res


def to_miniapp_receipt(receipt: Receipt) -> dict:
    parsed = receipt.model_dump()
    parsed["subtotal"] = float(parsed.get("subtotal") or 0)
    parsed["service_charge"] = float(parsed.get("service_charge") or 0)
    parsed["gst"] = float(parsed.get("gst") or 0)
    parsed["total"] = float(parsed.get("total") or 0)

    normalized_items = []
    for item in parsed.get("items", []):
        normalized_items.append(
            {
                "name": item.get("name") or "",
                "quantity": int(item.get("quantity") or 0),
                "subtotal": float(item.get("subtotal") or 0),
                "indiv": item.get("indiv") or [],
                "shared": item.get("shared") or [],
            }
        )

    parsed["items"] = normalized_items
    return parsed

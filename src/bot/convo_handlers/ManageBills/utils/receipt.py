from src.lib.receipt_parser.model import MiniappReceipt


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

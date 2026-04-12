from collections import defaultdict

from src.lib.splizy_repo.model import ExpenseRow

AMOUNT_CUTOFF = 0.01


def get_suggested_payments(
    all_expenses: list[ExpenseRow], settleup_currency: str
) -> str:
    # Populate payer and payee maps
    payer_amounts = defaultdict(float)
    payee_amounts = defaultdict(float)
    for expense in all_expenses:
        payer_amounts[expense["paid_by"]] += expense["amount"]
        for payee in expense["payees"]:
            payee_amounts[payee["user"]] += payee["amount"]
    stats = {
        "total_spending": sum([paid for _, paid in payer_amounts.items()]),
        "individual_spending": [
            (user, amount) for user, amount in payee_amounts.items()
        ],
    }
    # Normalise maps
    for payer, paid in payer_amounts.items():
        spent = payee_amounts[payer]
        transfer_amount = min(paid, spent)
        payer_amounts[payer] -= transfer_amount
        payee_amounts[payer] -= transfer_amount
    # Filter out near-zero amounts and sort
    payers = sorted(
        [
            (user, amount)
            for user, amount in payer_amounts.items()
            if amount > AMOUNT_CUTOFF
        ],
        key=lambda x: x[1],
        reverse=True,
    )
    payees = sorted(
        [
            (user, amount)
            for user, amount in payee_amounts.items()
            if amount > AMOUNT_CUTOFF
        ],
        key=lambda x: x[1],
    )
    # Generate suggested payments
    payments = {}
    payee_idx = 0
    for payer, paid in payers:
        amount_left = paid
        while amount_left > AMOUNT_CUTOFF and payee_idx < len(payees):
            payee, spent = payees[payee_idx]
            if spent <= AMOUNT_CUTOFF:
                payee_idx += 1
                continue
            transfer_amount = min(amount_left, spent)
            payments[payee].append((payer, transfer_amount))
            amount_left -= transfer_amount
            payees[payee_idx][1] -= transfer_amount
    return "\n".join(payments)

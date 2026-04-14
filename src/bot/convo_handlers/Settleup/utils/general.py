from collections import defaultdict
from typing import TypeAlias, TypedDict

from src.lib.currencies.config import CURRENCY_SHORTHAND_MAPPING
from src.lib.currencies.utils import convert
from src.lib.splizy_repo.model import CurrencyCode, ExpenseRow

AMOUNT_CUTOFF = 0.01

Payments: TypeAlias = dict[str, list[tuple[str, float]]]


class SettleupStats(TypedDict):
    currency: CurrencyCode
    total_spending: float
    payers: dict[str, float]
    transfers: dict[str, float]
    individual_spending: dict[str, float]


def _get_suggested_payments_str(payments: Payments, settleup_currency) -> str:
    shorthand_currency = CURRENCY_SHORTHAND_MAPPING[settleup_currency]
    res = [
        f"Suggested transfers in {settleup_currency} ({shorthand_currency}):\n---------------------------------"
    ]
    for from_user in sorted(payments, key=str.lower):
        transfers = sorted(payments[from_user], key=lambda x: x[0].lower())
        res.append(
            f"@{from_user} pays "
            + " and ".join(
                [
                    f"@{to_user} {shorthand_currency}{amount:.2f}"
                    for (to_user, amount) in transfers
                ]
            )
        )
    return res[0] + "\n" + "\n\n".join(res[1:])


def get_settleup_details(
    all_expenses: list[ExpenseRow], settleup_currency: str
) -> tuple[SettleupStats, Payments]:
    # Populate payer and payee maps
    payer_amounts = defaultdict(float)
    payee_amounts = defaultdict(float)
    for expense in all_expenses:
        currency = expense["currency"]
        payer_amounts[expense["paid_by"]] += convert(
            expense["amount"], currency, settleup_currency
        )
        for payee in expense["payees"]:
            payee_amounts[payee["user"]] += convert(
                payee["amount"], currency, settleup_currency
            )
    stats: SettleupStats = {
        "currency": settleup_currency,
        "total_spending": sum([paid for _, paid in payer_amounts.items()]),
        "payers": payer_amounts.copy(),
        "transfers": {},
        "individual_spending": payee_amounts.copy(),
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
            (user, amount)  # Read only tuple
            for user, amount in payer_amounts.items()
            if amount > AMOUNT_CUTOFF
        ],
        key=lambda x: x[1],
        reverse=True,
    )
    payees = sorted(
        [
            [user, amount]  # Mutable list for allocation later
            for user, amount in payee_amounts.items()
            if amount > AMOUNT_CUTOFF
        ],
        key=lambda x: x[1],
    )
    # Generate suggested payments
    payments: Payments = defaultdict(list)
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

    transfer_by_user: defaultdict[str, float] = defaultdict(float)
    for sender, transfers in payments.items():
        for receiver, amount in transfers:
            transfer_by_user[sender] -= amount
            transfer_by_user[receiver] += amount
    stats["transfers"] = dict(transfer_by_user)

    return (stats, payments)


def get_suggested_payments(
    all_expenses: list[ExpenseRow], settleup_currency: str
) -> tuple[SettleupStats, str]:
    stats, payments = get_settleup_details(all_expenses, settleup_currency)

    return (stats, _get_suggested_payments_str(payments, settleup_currency))

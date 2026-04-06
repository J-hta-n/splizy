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
        split_status = f"by custom amounts in {data['currency']}\n{custom_split_str}"

    summary = (
        f"---Bill for {data['expense_name']}---\n"
        f"Paid by: @{data['paid_by']}\n"
        f"Currency & Amount: {data['currency']} {get_2dp_str(data['amount'])}\n"
        f"Split: {split_status}\n"
    )
    return summary

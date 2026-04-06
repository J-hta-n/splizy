from decimal import Decimal


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

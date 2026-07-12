from decimal import Decimal

from src.bot.convo_handlers.ManageBills.context import ManageBillsChatData
from src.bot.convo_handlers.ManageBills.utils.receipt_spendings import (
    format_receipt_spendings,
)
from src.bot.convo_utils.formatters import get_2dp_str
from src.lib.currencies.utils import get_shorthand_currency


def get_bill_summary(data: ManageBillsChatData) -> str:
    if data["split_type"] == "equal_all":
        split_status = f"equally among everyone ({data['currency']} {get_2dp_str(data['amount']/len(data['all_participants']))} per person)"
    elif data["split_type"] == "equal_some":
        selected_participants = data["selected_participants"]
        split_status = f"equally among {len(selected_participants)} {'people' if len(selected_participants) > 1 else 'person'} (@{', @'.join(selected_participants)}, {data['currency']} {get_2dp_str(data['amount']/len(selected_participants))} per person)"
    elif data["split_type"] == "custom":
        mult_val = data["mult_val"] if data["has_mult"] else 1
        currency_symbol = get_shorthand_currency(data["currency"])
        custom_split_str = "\n".join(
            f"@{username} - {currency_symbol}{get_2dp_str(Decimal(str(amount))*Decimal(mult_val)) if is_selected else '0.00'}"
            for username, amount, is_selected in zip(
                data["all_participants"],
                data["custom_amounts"],
                data["participant_selections"],
            )
        )
        split_status = f"by custom amounts{' (Receipt details available)' if data.get('receipt') else ''}\n{custom_split_str}"

    summary = (
        f"---Bill for {data['expense_name']}---\n"
        f"Paid by: @{data['paid_by']}\n"
        f"Currency & Amount: {data['currency']} {get_2dp_str(data['amount'])}\n"
        f"Split: {split_status}\n"
    )
    return summary


def get_bill_summary_with_receipt(data: ManageBillsChatData) -> str:
    currency = data["currency"]
    user_spendings = format_receipt_spendings(
        data["receipt"], data["all_participants"], get_shorthand_currency(currency)
    )

    summary = (
        f"---Bill for {data['expense_name']}---\n"
        f"Paid by: @{data['paid_by']}\n"
        f"Amount: {currency} {get_2dp_str(data['amount'])}\n"
        f"User spendings (in {currency}):\n\n{user_spendings}"
    )
    return summary

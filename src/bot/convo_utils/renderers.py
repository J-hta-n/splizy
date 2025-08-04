from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils import get_2dp_str


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


async def send_confirmation_form(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_msg=True
):
    summary = get_bill_summary(context.user_data)
    keyboard = [
        [
            InlineKeyboardButton("Bill name", callback_data="edit_expense_name"),
            InlineKeyboardButton("Currency & Amount", callback_data="edit_amount"),
        ],
        [
            InlineKeyboardButton("Paid by", callback_data="edit_payer"),
            InlineKeyboardButton("Split type", callback_data="edit_split"),
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_form"),
            InlineKeyboardButton("✅ Confirm", callback_data="submit_form"),
        ],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if is_new_msg:
        await update.message.reply_text(summary, reply_markup=markup)
    else:
        await update.callback_query.edit_message_text(summary, reply_markup=markup)


async def send_multiselect_users(
    update: Update, context: ContextTypes.DEFAULT_TYPE, validation_error=None
):
    keyboard = []
    for idx, (is_selected, username) in enumerate(
        zip(
            context.user_data["participant_selections"],
            context.user_data["all_participants"],
        )
    ):
        prefix = "✅" if is_selected else "❌"
        keyboard.append(
            [InlineKeyboardButton(f"{prefix} @{username}", callback_data=idx)]
        )
    keyboard.append([InlineKeyboardButton("Done", callback_data="participants_done")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "👥 Select participants (all selected by default).\n"
        "Tap on a user to toggle selection. Tap 'Done' when finished.\n"
        f"{validation_error if validation_error else ''}",
        reply_markup=reply_markup,
    )


async def send_custom_multiselect_users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_new_msg=False,
    validation_error=None,
):
    data = context.user_data
    keyboard = []
    for idx, (is_selected, username, amount) in enumerate(
        zip(
            data["participant_selections"],
            data["all_participants"],
            data["custom_amounts"],
        )
    ):
        prefix = "✅" if is_selected else "❌"
        toggle_button = InlineKeyboardButton(
            f"{prefix} @{username}", callback_data=f"{idx}_toggle"
        )
        amount_button = (
            InlineKeyboardButton(get_2dp_str(amount), callback_data=f"{idx}_amount")
            if is_selected
            else None
        )
        keyboard.append(
            [toggle_button, amount_button] if is_selected else [toggle_button]
        )

    has_mult, mult_val = data["has_mult"], data["mult_val"]
    mult_toggle_button = InlineKeyboardButton(
        "Tap to remove multiplier:" if has_mult else "Tap to add multiplier",
        callback_data="mult_toggle",
    )
    mult_amount_button = (
        InlineKeyboardButton(mult_val, callback_data="mult_amount")
        if has_mult
        else None
    )
    keyboard.append(
        [mult_toggle_button, mult_amount_button] if has_mult else [mult_toggle_button]
    )
    keyboard.append([InlineKeyboardButton("Done", callback_data="custom_done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    subtotal = sum(
        amount
        for idx, amount in enumerate(data["custom_amounts"])
        if data["participant_selections"][idx]
    )
    text = (
        f"👥 Select participants and specify the custom amount paid in {data['currency']}.\n"
        f"Current total = {data['currency']} {get_2dp_str(subtotal)}{f' (*{mult_val} = {get_2dp_str(subtotal*Decimal(mult_val))})' if has_mult else ''}\n\n"
        "Tap on the left to toggle selection, and on the right to specify the amount. "
        "You can also specify the service charge multiplier at the bottom, eg 1.19.\n\n"
        "NOTE: current total will override initial total if they don't tally.\n"
        "Tap 'Done' when finished.\n"
        f"{validation_error if validation_error else ''}"
    )

    if is_new_msg:
        await update.message.reply_text(text=text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(
            text=text, reply_markup=reply_markup
        )


async def send_all_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_msg=True
):
    keyboard = []
    for idx, expense in enumerate(context.user_data["expenses"]):
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{expense['title']} | @{expense['paid_by']} | {expense['currency']} {expense['amount']}",
                    callback_data=idx,
                )
            ]
        )
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"All logged expenses so far:\n<title | payer | amount>\n\n"
    if is_new_msg:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

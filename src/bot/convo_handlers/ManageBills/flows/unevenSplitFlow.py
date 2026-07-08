from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.convo_handlers.ManageBills.context import ManageBillsChatData
from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_handlers.ManageBills.utils.parsers import parse_amount
from src.bot.convo_handlers.ManageBills.utils.renderers import (
    send_confirmation_form,
    send_custom_multiselect_users,
)
from src.lib.logger import get_logger

logger = get_logger(__name__)


async def expense_custom_split(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    action = query.data

    data: ManageBillsChatData = context.chat_data
    if action != "custom_done":
        entity, field = action.split("_")
        if entity.isdigit():
            index = int(entity)
            if field == "toggle":
                data["participant_selections"][index] = not data[
                    "participant_selections"
                ][index]
                if data["custom_amounts"][index] <= 0:
                    data["custom_amounts"][index] = Decimal("1")
                await send_custom_multiselect_users(update, context)
                return ManageBillStates.EXPENSE_CUSTOM_SPLIT
            elif field == "amount":
                data["index"] = index
                await query.edit_message_text(
                    f"Please enter the amount spent by @{data['all_participants'][index]}:"
                )
                return ManageBillStates.EXPENSE_CUSTOM_AMOUNT
        else:
            if field == "toggle":
                data["has_mult"] = not data["has_mult"]
                await send_custom_multiselect_users(update, context)
                return ManageBillStates.EXPENSE_CUSTOM_SPLIT
            elif field == "amount":
                await query.edit_message_text(
                    "Please enter a multiplier between 1 and 2, eg 1.19"
                )
                return ManageBillStates.EXPENSE_MULTIPLIER

    # Custom split done, validate first
    logger.info("Validating custom split selections...")
    if not any(context.chat_data["participant_selections"]):
        await send_custom_multiselect_users(
            update, context, False, "Please select at least one participant."
        )
        return ManageBillStates.EXPENSE_CUSTOM_SPLIT

    logger.info("Custom selection validated. Preparing confirmation form...")
    has_mult, mult_val = data["has_mult"], data["mult_val"]
    mult_decimal = Decimal(str(mult_val)) if has_mult else Decimal("1")
    data["selected_participants"] = [
        username
        for idx, username in enumerate(data["all_participants"])
        if data["participant_selections"][idx]
    ]
    data["amount"] = sum(
        [
            (Decimal(str(amount)) * mult_decimal)
            for idx, amount in enumerate(data["custom_amounts"])
            if data["participant_selections"][idx]
        ]
    )
    logger.info("Confirmation form prepared, sending...")
    # print(json.dumps(dict(context.chat_data), indent=2, default=str))
    await send_confirmation_form(update, context, False)
    logger.info("Confirmation form sent")

    return ManageBillStates.EXPENSE_CONFIRM


async def expense_custom_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    is_valid, result = parse_amount(update.message.text)
    if not is_valid:
        await update.message.reply_text(result)  # result is error msg if invalid
        return ManageBillStates.EXPENSE_CUSTOM_AMOUNT
    _, amount = result

    index = context.chat_data["index"]
    context.chat_data["custom_amounts"][index] = amount

    await send_custom_multiselect_users(update, context, True)
    return ManageBillStates.EXPENSE_CUSTOM_SPLIT

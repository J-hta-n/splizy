from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.SetCurrency.callbacks import (
    CURRENCY_BACK,
    EDIT_EXPENSE_CURRENCY,
    EDIT_SETTLEUP_CURRENCY,
    CurrencyTargetField,
)
from src.bot.convo_handlers.SetCurrency.context import get_setcurrency_user_data
from src.bot.convo_handlers.SetCurrency.states import SetCurrencyStates
from src.bot.convo_handlers.SetCurrency.utils.renderers import (
    send_current_currencies,
    send_current_currencies_for_query,
    send_select_currency,
)
from src.bot.convo_utils.parsers import parse_currency
from src.bot.convo_utils.wrappers import group_only
from src.lib.currencies.config import ALL_CURRENCY_CODES
from src.lib.splizy_repo.repo import repo

VALID_TARGET_FIELDS: frozenset[CurrencyTargetField] = frozenset(
    {"expense_currency", "settleup_currency"}
)


def _target_label(field: str) -> str:
    if field == "expense_currency":
        return "expenses"
    return "settleup"


@group_only
async def set_currencies_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    data = get_setcurrency_user_data(context)
    group_id = update.message.chat.id
    group = repo.get_group(group_id)
    data["group"] = group
    await send_current_currencies(update, context)
    return SetCurrencyStates.SELECT_CURRENCY


async def select_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = get_setcurrency_user_data(context)
    query = update.callback_query
    await query.answer()
    action = query.data or ""

    if action in {EDIT_EXPENSE_CURRENCY, EDIT_SETTLEUP_CURRENCY}:
        target_field = (
            "expense_currency"
            if action == EDIT_EXPENSE_CURRENCY
            else "settleup_currency"
        )
        data["currency_target_field"] = target_field
        await send_select_currency(
            query,
            f"Select a default {_target_label(target_field)} currency, or input another currency if not found.",
            target_field,
        )
        return SetCurrencyStates.SELECT_CURRENCY

    if action == CURRENCY_BACK:
        group = data.get("group")
        if group is None:
            await query.edit_message_text(
                "No group context found. Please try /set_currencies again."
            )
            return ConversationHandler.END
        await send_current_currencies_for_query(query, group)
        return SetCurrencyStates.SELECT_CURRENCY

    if action.startswith("currency_custom:"):
        _, target_field = action.split(":", 1)
        if target_field not in VALID_TARGET_FIELDS:
            await query.edit_message_text("Invalid currency selection action.")
            return ConversationHandler.END

        data["currency_target_field"] = target_field
        await query.edit_message_text(
            f"Type a 3-letter currency code for {_target_label(target_field)}. Example: USD"
        )
        return SetCurrencyStates.SET_CUSTOM_CURRENCY

    if action.startswith("currency_set:"):
        _, target_field, currency_code = action.split(":", 2)
        currency_code = currency_code.strip().upper()
        if target_field not in VALID_TARGET_FIELDS:
            await query.edit_message_text("Invalid currency selection action.")
            return ConversationHandler.END
        if currency_code not in ALL_CURRENCY_CODES:
            await query.edit_message_text("Currency code may be out of scope")
            return SetCurrencyStates.SELECT_CURRENCY

        group_id = update.effective_chat.id
        repo.update_group(group_id, {target_field: currency_code})
        updated_group = repo.get_group(group_id)
        if updated_group is None:
            await query.edit_message_text("Failed to update group currency settings.")
            return ConversationHandler.END

        data["group"] = updated_group
        await send_current_currencies_for_query(
            query,
            updated_group,
            f"Updated {_target_label(target_field)} currency to {currency_code}",
        )
        return SetCurrencyStates.SELECT_CURRENCY

    await query.edit_message_text("Unknown action.")
    return ConversationHandler.END


async def set_custom_currency(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    data = get_setcurrency_user_data(context)
    target_field = data.get("currency_target_field")
    if target_field not in VALID_TARGET_FIELDS:
        await update.message.reply_text(
            "No currency target selected. Please try /set_currencies again."
        )
        return ConversationHandler.END

    is_valid, parsed = parse_currency(update.message.text or "")
    if not is_valid:
        await update.message.reply_text("Currency code may be out of scope")
        return SetCurrencyStates.SET_CUSTOM_CURRENCY

    currency_code = parsed
    group_id = update.effective_chat.id
    repo.update_group(group_id, {target_field: currency_code})
    updated_group = repo.get_group(group_id)
    if updated_group is None:
        await update.message.reply_text("Failed to update group currency settings.")
        return ConversationHandler.END

    data["group"] = updated_group
    await send_current_currencies(
        update,
        context,
        f"Updated {_target_label(target_field)} currency to {currency_code}",
    )
    return SetCurrencyStates.SELECT_CURRENCY

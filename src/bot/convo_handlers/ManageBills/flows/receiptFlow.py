import json

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.bot.convo_handlers.ManageBills.utils.general import (
    populate_context_for_selected_expense_from_viewall,
)
from src.bot.convo_handlers.ManageBills.utils.receipt import (
    compute_spending_from_last_receipt,
    to_miniapp_receipt,
)
from src.bot.convo_handlers.ManageBills.utils.renderers import (
    open_miniapp,
    send_expense_view,
)
from src.bot.convo_utils.wrappers import group_only
from src.lib.logger import get_logger
from src.lib.receipt_parser import Receipt, parse_receipt
from src.lib.splizy_repo.repo import repo
from src.lib.splizy_repo.service import (
    get_latest_temp_receipt_with_expense,
    prepare_temp_receipt_review,
)

logger = get_logger(__name__)


@group_only
async def add_receipt_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.clear()
    context.user_data["receipt"] = parse_receipt(bytes())
    # logger.info(context.user_data["receipt"].model_dump_json(indent=2))
    await update.message.reply_text(
        "Please upload a picture of your receipt! (the clearer the better!)"
    )
    return ManageBillStates.EXPENSE_RECEIPT_UPLOAD


async def expense_receipt_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    # Telegram photo comes in a list sorted by size; pick the highest resolution
    photo_sizes = update.message.photo
    if not photo_sizes:
        await update.message.reply_text(
            "Please send a receipt photo (not a text message)."
        )
        return ManageBillStates.EXPENSE_RECEIPT_UPLOAD

    largest_photo = photo_sizes[-1]
    try:
        photo_file = await largest_photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()
    except Exception as e:
        logger.error(f"Failed to download receipt photo: {e}")
        await update.message.reply_text(
            "Could not download receipt photo. Please try again."
        )
        return ManageBillStates.EXPENSE_RECEIPT_UPLOAD

    logger.info("Photo received. Parsing...")
    wait_msg = await update.message.reply_text(
        "Photo received, please wait a few seconds for parsing..."
    )
    try:
        receipt: Receipt = parse_receipt(bytes(image_bytes))
    except Exception as e:
        logger.error(f"Receipt parsing failed: {e}")
        await update.message.reply_text(
            "Could not parse the receipt image as service might be down. Please try again later or ping the admin at @jhtzz."
        )
        return ConversationHandler.END

    context.user_data["receipt"] = receipt
    logger.info(
        f"Photo receipt parsed successfully:\n {json.dumps(dict(context.user_data['receipt']), indent=2, default=str)}"
    )

    if receipt.total is None:
        await update.message.reply_text(
            "Receipt's total amount could not be detected. Please try again with a clearer photo"
        )
        return ManageBillStates.EXPENSE_RECEIPT_UPLOAD

    group_id = update.effective_chat.id

    try:
        prepare_temp_receipt_review(
            group_id,
            to_miniapp_receipt(receipt),
        )
    except Exception as e:
        logger.error(f"Failed to create temp receipt row: {e}")
        await update.message.reply_text(
            "Failed to prepare receipt for miniapp review due to a db error. Please try again later or ping the admin at @jhtzz."
        )
        return ConversationHandler.END

    await open_miniapp(update, group_id, message=wait_msg)
    return ManageBillStates.EXPENSE_RECEIPT_CONFIRM


async def expense_receipt_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    # If editing, update the expense context and go back to expense view
    is_editing = "expense_id" in context.user_data
    if is_editing:
        expense = repo.get_expense(context.user_data["expense_id"])
        if expense is None:
            await query.edit_message_text(
                "Updated expense could not be loaded, service might be down."
            )
            return ConversationHandler.END
        index = context.user_data["expense_index"]
        context.user_data["expenses"][index] = expense
        populate_context_for_selected_expense_from_viewall(context, expense)
        await send_expense_view(update, context)
        return ManageBillStates.EDIT_OR_GO_BACK

    group_id = query.message.chat.id
    temp_receipt, expense = get_latest_temp_receipt_with_expense(group_id)

    if temp_receipt is None:
        await query.edit_message_text(
            "No temporary receipt session found for this group, service might be down."
        )
        return ConversationHandler.END

    expense_id = temp_receipt.get("expense_id")
    if not expense_id:
        await open_miniapp(update, group_id, is_error_msg=True)
        return ManageBillStates.EXPENSE_RECEIPT_CONFIRM

    if expense is None:
        await query.edit_message_text(
            "Receipt was submitted but expense details could not be loaded, service might be down."
        )
        return ConversationHandler.END

    payees = expense.get("payees") or []
    user_spending_lines = [
        f"{(entry.get('user') or entry.get('username') or '-')} - {expense.get('currency', '')} {float(entry.get('amount') or 0):.2f}"
        for entry in payees
        if (entry.get("user") or entry.get("username"))
    ]

    if not user_spending_lines:
        last_receipt = temp_receipt.get("last_receipt") or {}
        computed = compute_spending_from_last_receipt(last_receipt)
        user_spending_lines = [
            f"{username} - {expense.get('currency', '')} {amount:.2f}"
            for username, amount in sorted(computed.items())
        ]

    try:
        total_amount = float(expense.get("amount") or 0)
    except (TypeError, ValueError):
        total_amount = 0.0

    lines = [
        "Receipt saved successfully! Details:",
        f"Total: {expense.get('currency', '')} {total_amount:.2f}",
        f"Paid by: {expense.get('paid_by', '-')}",
        "User spending:",
    ]
    lines.extend(user_spending_lines)

    await query.edit_message_text("\n".join(lines))
    context.user_data.clear()
    return ConversationHandler.END

import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_utils.miniapp import open_miniapp
from src.bot.convo_utils.wrappers import group_only
from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.lib.logger import get_logger
from src.lib.receipt_parser import Receipt, parse_receipt
from src.lib.splizy_repo.database import supabase

logger = get_logger(__name__)


def _to_miniapp_receipt(receipt: Receipt) -> dict:
    parsed = receipt.model_dump()
    parsed["subtotal"] = float(parsed.get("subtotal") or 0)
    parsed["service_charge"] = float(parsed.get("service_charge") or 0)
    parsed["gst"] = float(parsed.get("gst") or 0)
    parsed["total"] = float(parsed.get("total") or 0)

    normalized_items = []
    for item in parsed.get("items", []):
        normalized_items.append(
            {
                "name": item.get("name") or "",
                "quantity": int(item.get("quantity") or 0),
                "subtotal": float(item.get("subtotal") or 0),
                "indiv": item.get("indiv") or [],
                "shared": item.get("shared") or [],
            }
        )

    parsed["items"] = normalized_items
    return parsed


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
    try:
        receipt: Receipt = parse_receipt(bytes(image_bytes))
    except Exception as e:
        logger.error(f"Receipt parsing failed: {e}")
        await update.message.reply_text(
            "Could not parse the receipt image. Please upload a clearer receipt photo."
        )
        return ManageBillStates.EXPENSE_RECEIPT_UPLOAD

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
    users_data = (
        supabase.table("splizy_users")
        .select("username")
        .eq("group_id", group_id)
        .execute()
        .data
    )
    users = [entry["username"] for entry in users_data]

    temp_entry = {
        "group_id": group_id,
        "title": None,
        "paid_by": None,
        "expense_id": None,
        "last_receipt": {
            "users": users,
            "receipt": _to_miniapp_receipt(receipt),
        },
    }

    try:
        existing_rows = (
            supabase.table("temp_receipts")
            .select("id")
            .eq("group_id", group_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
        )

        if existing_rows:
            supabase.table("temp_receipts").update(temp_entry).eq(
                "id", existing_rows[0]["id"]
            ).execute()
        else:
            supabase.table("temp_receipts").insert(temp_entry).execute()
    except Exception as e:
        logger.error(f"Failed to create temp receipt row: {e}")
        await update.message.reply_text(
            "Failed to prepare receipt for miniapp review. Please try again."
        )
        return ConversationHandler.END

    await open_miniapp(update, group_id)

    done_keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("I'm done", callback_data="receipt_done")]]
    )
    await update.message.reply_text(
        "After submitting in the miniapp, tap this button:",
        reply_markup=done_keyboard,
    )

    return ManageBillStates.EXPENSE_RECEIPT_CONFIRM


async def expense_receipt_done(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    group_id = query.message.chat.id
    temp_rows = (
        supabase.table("temp_receipts")
        .select("id, expense_id")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )

    if not temp_rows:
        await query.edit_message_text(
            "No temporary receipt session found for this group."
        )
        return ManageBillStates.EXPENSE_RECEIPT_CONFIRM

    expense_id = temp_rows[0].get("expense_id")
    if not expense_id:
        await query.edit_message_text(
            "Submission not detected yet. Please submit in the miniapp first, then tap I'm done."
        )
        return ManageBillStates.EXPENSE_RECEIPT_CONFIRM

    expense_rows = (
        supabase.table("expenses")
        .select("title, amount, paid_by, currency")
        .eq("id", expense_id)
        .limit(1)
        .execute()
        .data
    )
    if not expense_rows:
        await query.edit_message_text(
            "Receipt was submitted but expense details could not be loaded."
        )
        return ConversationHandler.END

    expense = expense_rows[0]
    user_expenses = (
        supabase.table("user_expenses")
        .select("username, amount")
        .eq("expense_id", expense_id)
        .order("username")
        .execute()
        .data
    )

    lines = [
        "Receipt saved successfully! Details:",
        f"Total: {expense.get('currency', '')} {expense.get('amount', '0')}",
        f"Paid by: {expense.get('paid_by', '-')}",
        "User spending:",
    ]
    lines.extend(
        [
            f"{entry.get('username', '-')} - {expense.get('currency', '')} {entry.get('amount', '0')}"
            for entry in user_expenses
        ]
    )

    await query.edit_message_text("\n".join(lines))
    context.user_data.clear()
    return ConversationHandler.END


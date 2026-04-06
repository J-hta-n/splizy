from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from config import MINIAPP_URL
from src.lib.receipt_parser.model import Receipt


def to_miniapp_receipt(receipt: Receipt) -> dict:
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


async def open_miniapp(update: Update, group_id: int, is_error_msg=False) -> None:
    url = f"{MINIAPP_URL}/?group_id={group_id}"

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Open miniapp", url=url)],
            [InlineKeyboardButton("I'm done", callback_data="receipt_done")],
        ]
    )

    text = (
        "Receipt parsed. Open the miniapp to review and confirm the split, then tap I'm done after submitting the expense via the miniapp."
        if not is_error_msg
        else "Submission not detected. Please submit in the miniapp first, then tap I'm done."
    )

    if is_error_msg:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

import json

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.convo_handlers.ManageBills.states import ManageBillStates
from src.lib.logger import get_logger
from src.lib.receipt_parser import ParsedReceipt, parse_receipt

logger = get_logger(__name__)


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
        receipt: ParsedReceipt = parse_receipt(bytes(image_bytes))
    except Exception as e:
        logger.error(f"Receipt parsing failed: {e}")
        await update.message.reply_text(
            "Could not parse the receipt image. Please upload a clearer receipt photo."
        )
        return ManageBillStates.EXPENSE_RECEIPT_UPLOAD

    context.user_data["parsed_receipt"] = receipt
    logger.info(
        f"Photo receipt: ParsedReceipt! Info:\n {json.dumps(dict(context.user_data['parsed_receipt']), indent=2, default=str)}"
    )

    if receipt.total is not None:
        await update.message.reply_text(
            f"Receipt receipt: ParsedReceipt successfully! Total detected: {receipt.total}."
            "\nWho paid for this expense? Please enter the Telegram handle, eg @user1"
        )
        return ManageBillStates.EXPENSE_PAID_BY

    await update.message.reply_text(
        "Receipt receipt: ParsedReceipt, but total could not be detected automatically. "
        "Please enter the amount manually (e.g., 50.10)."
    )
    return ManageBillStates.EXPENSE_RECEIPT_UPLOAD

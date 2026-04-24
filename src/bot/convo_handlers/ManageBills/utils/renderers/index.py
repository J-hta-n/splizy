from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from config import MINIAPP_URL
from src.bot.convo_handlers.ManageBills.callbacks import (
    DELETE_EXPENSE,
    EDIT_EXPENSE,
    GO_BACK,
    HIDE_RECEIPT,
    SHOW_RECEIPT,
    VIEW_ALL_ENTRIES,
    VIEW_PAGE_NEXT,
    VIEW_PAGE_PREV,
    VIEW_SELECT_PREFIX,
    VIEW_TOGGLE_HIDE,
    VIEW_TOGGLE_SHOW,
)
from src.bot.convo_handlers.ManageBills.context import ManageBillsChatData
from src.bot.convo_handlers.ManageBills.utils.renderers.bill_summary import (
    get_bill_summary,
    get_bill_summary_with_receipt,
)
from src.bot.convo_utils.formatters import get_2dp_str, truncate_label
from src.bot.convo_utils.pagination import get_page_window
from src.lib.currencies.utils import get_shorthand_currency

MAX_TELEGRAM_TEXT_LEN = 3800
RECEIPT_DETAIL_MESSAGE_IDS_KEY = "receipt_detail_message_ids"
VIEWALL_PAGE_SIZE = 10


def get_view_all_entries_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "View all entries so far", callback_data=VIEW_ALL_ENTRIES
                )
            ]
        ]
    )


def _chunk_text_by_blocks(text: str, max_len: int = MAX_TELEGRAM_TEXT_LEN) -> list[str]:
    if len(text) <= max_len:
        return [text]

    blocks = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for block in blocks:
        candidate = block if not current else f"{current}\n\n{block}"
        if len(candidate) <= max_len:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        while len(block) > max_len:
            chunks.append(block[:max_len])
            block = block[max_len:]

        current = block

    if current:
        chunks.append(current)

    return chunks


async def _delete_receipt_detail_messages(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message_ids = context.chat_data.get(RECEIPT_DETAIL_MESSAGE_IDS_KEY, [])
    if not message_ids:
        return

    chat_id = update.effective_chat.id
    for message_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except BadRequest:
            # Ignore messages that are already deleted or no longer deletable.
            continue

    context.chat_data[RECEIPT_DETAIL_MESSAGE_IDS_KEY] = []


async def send_confirmation_form(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_msg=True
):
    summary = get_bill_summary(context.chat_data)
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


async def send_select_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE, new_msg=True
):
    keyboard = []
    for username in context.chat_data["all_participants"]:
        keyboard.append([InlineKeyboardButton(username, callback_data=username)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if new_msg:
        await update.message.reply_text(
            f"Who paid for this expense of {context.chat_data['currency']} {context.chat_data['amount']}?",
            reply_markup=reply_markup,
        )
    else:
        await update.callback_query.edit_message_text(
            f"Who paid for this expense of {context.chat_data['currency']} {context.chat_data['amount']}?",
            reply_markup=reply_markup,
        )


async def send_multiselect_users(
    update: Update, context: ContextTypes.DEFAULT_TYPE, validation_error=None
):
    keyboard = []
    for idx, (is_selected, username) in enumerate(
        zip(
            context.chat_data["participant_selections"],
            context.chat_data["all_participants"],
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
    data: ManageBillsChatData = context.chat_data
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
    await _delete_receipt_detail_messages(update, context)

    data: ManageBillsChatData = context.chat_data
    expenses = data["expenses"]
    total_expenses = len(expenses)
    current_page, total_pages, start_idx, end_idx = get_page_window(
        total_items=total_expenses,
        page_size=VIEWALL_PAGE_SIZE,
        requested_page=int(data.get("viewall_page", 0)),
    )
    data["viewall_page"] = current_page
    is_collapsed = bool(data.get("viewall_is_collapsed", False))

    keyboard = []

    if not is_collapsed:
        for idx in range(start_idx, end_idx):
            expense = expenses[idx]
            title_label = truncate_label(expense["title"], width=20)
            payer_label = truncate_label(f"@{expense['paid_by']}", width=7)
            keyboard.append(
                [
                    InlineKeyboardButton(
                        (
                            f"{title_label} | "
                            f"{payer_label} | "
                            f"{get_shorthand_currency(expense['currency'])}{expense['amount']:.2f}"
                        ),
                        callback_data=f"{VIEW_SELECT_PREFIX}{idx}",
                    )
                ]
            )
        nav_row = []
        if current_page > 0:
            nav_row.append(
                InlineKeyboardButton("<- Prev page", callback_data=VIEW_PAGE_PREV)
            )
        if current_page < total_pages - 1:
            nav_row.append(
                InlineKeyboardButton("Next page ->", callback_data=VIEW_PAGE_NEXT)
            )
        if nav_row:
            keyboard.append(nav_row)

    toggle_label = "Show entries" if is_collapsed else "Hide entries"
    toggle_callback = VIEW_TOGGLE_SHOW if is_collapsed else VIEW_TOGGLE_HIDE
    keyboard.append([InlineKeyboardButton(toggle_label, callback_data=toggle_callback)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    total_expenses_text = (
        f"{total_expenses} expense{'s' if total_expenses > 1 else ''} so far"
    )
    page_text = f"(Page {current_page + 1}/{total_pages})" if total_pages > 1 else ""
    text = f"{total_expenses_text} {page_text}\n" "Format: (title | payer | amount)\n"

    if is_new_msg:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def open_miniapp(
    update: Update, group_id=None, expense_id=None, is_error_msg=False, message=None
) -> None:
    url = f"{MINIAPP_URL}/?group_id={group_id}"
    # expense_id signals edit
    url += f"&expense_id={expense_id}" if expense_id else ""

    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Open miniapp", url=url)],
            [InlineKeyboardButton("I'm done", callback_data="receipt_done")],
        ]
    )

    text = (
        "Please open the miniapp to edit the receipt bill split, then tap I'm done after submitting via the miniapp."
        if expense_id
        else (
            "Receipt parsed. Open the miniapp to review and confirm the split, then tap I'm done after submitting the expense via the miniapp."
            if not is_error_msg
            else "Submission not detected. Please submit in the miniapp first, then tap I'm done."
        )
    )

    if message is not None:
        await message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def send_expense_view(
    update: Update, context: ContextTypes.DEFAULT_TYPE, remarks=None
):
    await _delete_receipt_detail_messages(update, context)

    summary = get_bill_summary(context.chat_data)
    has_receipt = context.chat_data["receipt"] is not None
    text = summary if not remarks else f"{summary}\n{remarks}"
    keyboard = [
        [
            InlineKeyboardButton("Edit", callback_data=EDIT_EXPENSE),
            InlineKeyboardButton("Delete", callback_data=DELETE_EXPENSE),
        ]
    ]
    if has_receipt:
        keyboard.append(
            [InlineKeyboardButton("Show receipt details", callback_data=SHOW_RECEIPT)]
        )
    keyboard.append([InlineKeyboardButton("Go back", callback_data=GO_BACK)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def send_expense_with_receipt_view(
    update: Update, context: ContextTypes.DEFAULT_TYPE, remarks=None
):
    await _delete_receipt_detail_messages(update, context)

    summary = get_bill_summary_with_receipt(context.chat_data)
    chunks = _chunk_text_by_blocks(summary)
    first_text = chunks[0] if not remarks else f"{chunks[0]}\n{remarks}"

    keyboard = [
        [
            InlineKeyboardButton("Edit", callback_data=EDIT_EXPENSE),
            InlineKeyboardButton("Delete", callback_data=DELETE_EXPENSE),
        ],
        [InlineKeyboardButton("Hide receipt details", callback_data=HIDE_RECEIPT)],
        [InlineKeyboardButton("Go back", callback_data=GO_BACK)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(first_text, reply_markup=reply_markup)

    detail_message_ids: list[int] = []
    for chunk in chunks[1:]:
        sent = await context.bot.send_message(
            chat_id=update.effective_chat.id, text=chunk
        )
        detail_message_ids.append(sent.message_id)

    context.chat_data[RECEIPT_DETAIL_MESSAGE_IDS_KEY] = detail_message_ids

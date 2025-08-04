import datetime
import json
import logging
import os
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for the conversation handler
(
    EXPENSE_NAME,
    EXPENSE_AMOUNT,
    EXPENSE_CURRENCY,
    EXPENSE_PAID_BY,
    EXPENSE_SPLIT_TYPE,
    EXPENSE_PARTICIPANTS,
    EXPENSE_REMARKS,
    EXPENSE_CONFIRM,
    EDIT_SELECT_EXPENSE,
    EDIT_FIELD,
    EDIT_VALUE,
    DELETE_CONFIRM,
) = range(12)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the current status of all expenses."""
    chat_id = update.effective_chat.id
    data = load_user_data(chat_id)

    if not data["expenses"]:
        await update.message.reply_text("No expenses found.")
        return

    # Create a summary of all expenses
    message = "📊 Expense Summary:\n\n"

    for expense in data["expenses"]:
        payer = data["users"].get(expense["paid_by"], {}).get("username", "Unknown")

        message += (
            f"ID: {expense['id']}\n"
            f"Description: {expense['name']}\n"
            f"Amount: {expense['currency']} {expense['amount']}\n"
            f"Paid by: {payer}\n"
            f"Date: {expense['date']}\n\n"
        )

    await update.message.reply_text(message)


async def settle_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Calculate and display settlement recommendations."""
    chat_id = update.effective_chat.id
    data = load_user_data(chat_id)

    if not data["expenses"]:
        await update.message.reply_text("No expenses found.")
        return

    if not data["users"]:
        await update.message.reply_text("No users registered.")
        return

    # Initialize balance dictionary
    balances = {user_id: {} for user_id in data["users"]}

    # Calculate balances
    for expense in data["expenses"]:
        payer_id = expense["paid_by"]
        amount = Decimal(expense["amount"])
        currency = expense["currency"]
        participants = expense["participants"]

        if not participants:
            continue

        # Handle different split types
        if expense["split_type"] == "equal":
            share = amount / len(participants)

            for participant_id in participants:
                if participant_id == payer_id:
                    continue

                # Initialize currency if not exists
                if currency not in balances[participant_id]:
                    balances[participant_id][currency] = Decimal("0")
                if currency not in balances[payer_id]:
                    balances[payer_id][currency] = Decimal("0")

                # Update balances
                balances[participant_id][currency] -= share
                balances[payer_id][currency] += share

    # Generate settlement recommendations
    settlements = []

    # For each currency, find who owes whom
    for currency in set(
        curr for user_balances in balances.values() for curr in user_balances
    ):
        # Create a list of (user_id, balance) for this currency
        currency_balances = [
            (user_id, user_balances.get(currency, Decimal("0")))
            for user_id, user_balances in balances.items()
        ]

        # Sort by balance (ascending)
        currency_balances.sort(key=lambda x: x[1])

        # Perform settlements
        i, j = 0, len(currency_balances) - 1

        while i < j:
            debtor_id, debtor_bal = currency_balances[i]
            creditor_id, creditor_bal = currency_balances[j]

            if abs(debtor_bal) < 0.01 and abs(creditor_bal) < 0.01:
                i += 1
                j -= 1
                continue

            # Calculate settlement amount
            settle_amount = min(abs(debtor_bal), creditor_bal)

            if settle_amount > 0.01:  # Only include non-trivial settlements
                debtor_name = (
                    data["users"].get(debtor_id, {}).get("username", "Unknown")
                )
                creditor_name = (
                    data["users"].get(creditor_id, {}).get("username", "Unknown")
                )
                settlements.append(
                    (debtor_name, creditor_name, currency, settle_amount)
                )

            # Update balances
            currency_balances[i] = (debtor_id, debtor_bal + settle_amount)
            currency_balances[j] = (creditor_id, creditor_bal - settle_amount)

            # Move indices if balance is zeroed
            if abs(currency_balances[i][1]) < 0.01:
                i += 1
            if abs(currency_balances[j][1]) < 0.01:
                j -= 1

    # Create the message
    if settlements:
        message = "💰 Settlement Recommendations:\n\n"
        for debtor, creditor, currency, amount in settlements:
            message += f"{debtor} pays {creditor} {currency} {amount:.2f}\n"
    else:
        message = "✅ All balances are settled!"

    # Save settlements to a CSV file
    csv_file_path = os.path.join(DATA_DIR, f"{chat_id}_settlements.csv")
    with open(csv_file_path, "w") as f:
        f.write("Debtor,Creditor,Currency,Amount\n")
        for debtor, creditor, currency, amount in settlements:
            f.write(f"{debtor},{creditor},{currency},{amount:.2f}\n")

    await update.message.reply_text(message)

    # Send the CSV file
    if settlements:
        await update.message.reply_document(
            document=open(csv_file_path, "rb"), filename="settlements.csv"
        )


async def edit_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the expense editing process."""
    chat_id = update.effective_chat.id
    data = load_user_data(chat_id)

    if not data["expenses"]:
        await update.message.reply_text("No expenses found to edit.")
        return ConversationHandler.END

    # Create keyboard with expense options
    keyboard = []
    for expense in data["expenses"]:
        expense_desc = f"{expense['name']} ({expense['currency']} {expense['amount']})"
        keyboard.append(
            [InlineKeyboardButton(expense_desc, callback_data=f"edit_{expense['id']}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select an expense to edit:", reply_markup=reply_markup
    )

    return EDIT_SELECT_EXPENSE


async def edit_select_expense(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the selection of an expense to edit."""
    query = update.callback_query
    await query.answer()

    expense_id = query.data.split("_")[1]
    context.user_data["edit_expense_id"] = expense_id

    # Get the expense details
    chat_id = update.effective_chat.id
    data = load_user_data(chat_id)
    expense = next((exp for exp in data["expenses"] if exp["id"] == expense_id), None)

    if not expense:
        await query.edit_message_text("Expense not found.")
        return ConversationHandler.END

    # Store the original expense data for reference
    context.user_data["original_expense"] = expense.copy()

    # Create keyboard with fields to edit
    keyboard = [
        [InlineKeyboardButton("Name", callback_data="edit_field_name")],
        [InlineKeyboardButton("Amount", callback_data="edit_field_amount")],
        [InlineKeyboardButton("Currency", callback_data="edit_field_currency")],
        [InlineKeyboardButton("Paid by", callback_data="edit_field_paid_by")],
        [InlineKeyboardButton("Participants", callback_data="edit_field_participants")],
        [InlineKeyboardButton("Remarks", callback_data="edit_field_remarks")],
        [InlineKeyboardButton("Cancel", callback_data="edit_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Editing: {expense['name']}\n" f"Select a field to edit:",
        reply_markup=reply_markup,
    )

    return EDIT_FIELD


async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the expense deletion process."""
    chat_id = update.effective_chat.id
    data = load_user_data(chat_id)

    if not data["expenses"]:
        await update.message.reply_text("No expenses found to delete.")
        return ConversationHandler.END

    # Create keyboard with expense options
    keyboard = []
    for expense in data["expenses"]:
        expense_desc = f"{expense['name']} ({expense['currency']} {expense['amount']})"
        keyboard.append(
            [
                InlineKeyboardButton(
                    expense_desc, callback_data=f"delete_{expense['id']}"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select an expense to delete:", reply_markup=reply_markup
    )

    return DELETE_CONFIRM


async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the confirmation of expense deletion."""
    query = update.callback_query
    await query.answer()

    expense_id = query.data.split("_")[1]

    # Get the expense details
    chat_id = update.effective_chat.id
    data = load_user_data(chat_id)
    expense = next((exp for exp in data["expenses"] if exp["id"] == expense_id), None)

    if not expense:
        await query.edit_message_text("Expense not found.")
        return ConversationHandler.END

    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Yes, delete", callback_data=f"confirm_delete_{expense_id}"
            ),
            InlineKeyboardButton("❌ No, cancel", callback_data="cancel_delete"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Are you sure you want to delete '{expense['name']}' "
        f"({expense['currency']} {expense['amount']})?",
        reply_markup=reply_markup,
    )

    return DELETE_CONFIRM


async def perform_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Perform the actual deletion of an expense."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_delete":
        await query.edit_message_text("Deletion cancelled.")
        return ConversationHandler.END

    expense_id = query.data.split("_")[2]

    # Delete the expense
    chat_id = update.effective_chat.id
    data = load_user_data(chat_id)

    # Find and remove the expense
    data["expenses"] = [exp for exp in data["expenses"] if exp["id"] != expense_id]

    # Save to file
    save_user_data(chat_id, data)

    await query.edit_message_text("✅ Expense deleted successfully!")

    return ConversationHandler.END


async def addwithocr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add an expense using OCR from a receipt photo."""
    await update.message.reply_text(
        "📸 Please send a photo of your receipt.\n\n"
        "Note: OCR functionality is not implemented in this template. "
        "You would need to integrate with an OCR service."
    )


def main() -> None:
    """Start the bot."""
    # Create the application and pass it your bot's token
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Add conversation handler for adding expenses
    add_expense_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_expense)],
        states={
            EXPENSE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_name)
            ],
            EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)
            ],
            EXPENSE_CURRENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_currency)
            ],
            EXPENSE_PAID_BY: [CallbackQueryHandler(expense_paid_by, pattern=r"^paid_")],
            EXPENSE_SPLIT_TYPE: [
                CallbackQueryHandler(expense_split_type, pattern=r"^split_")
            ],
            EXPENSE_PARTICIPANTS: [
                CallbackQueryHandler(
                    expense_participants, pattern=r"^participant_|^participants_"
                )
            ],
            EXPENSE_REMARKS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_remarks)
            ],
            EXPENSE_CONFIRM: [
                CallbackQueryHandler(expense_confirm, pattern=r"^expense_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add conversation handler for editing expenses
    edit_expense_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_expense)],
        states={
            EDIT_SELECT_EXPENSE: [
                CallbackQueryHandler(edit_select_expense, pattern=r"^edit_")
            ],
            EDIT_FIELD: [
                CallbackQueryHandler(cancel, pattern=r"^edit_field_")
            ],  # Placeholder
            EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)
            ],  # Placeholder
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add conversation handler for deleting expenses
    delete_expense_conv = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_expense)],
        states={
            DELETE_CONFIRM: [
                CallbackQueryHandler(delete_confirm, pattern=r"^delete_"),
                CallbackQueryHandler(
                    perform_delete, pattern=r"^confirm_delete_|^cancel_delete"
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("settleup", settle_up))
    application.add_handler(CommandHandler("addwithocr", addwithocr))

    # Add conversation handlers
    application.add_handler(add_expense_conv)
    application.add_handler(edit_expense_conv)
    application.add_handler(delete_expense_conv)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

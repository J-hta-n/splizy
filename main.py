import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from currencies import COMMON_CURRENCY_CODES_STRING
from database import supabase
from parsers import parse_amount, parse_username

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
TELEBOT_TOKEN = os.environ.get("TELEBOT_TOKEN")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")
PORT = int(os.environ.get("PORT", "8000"))

# States for the conversation handler
(
    REGISTER_USERS,
    EXPENSE_NAME,
    EXPENSE_AMOUNT,
    EXPENSE_PAID_BY,
    EXPENSE_SPLIT_TYPE,
    EXPENSE_PARTICIPANTS,
    EXPENSE_CONFIRM,
    VIEW_EXPENSE,
    EDIT_OR_GO_BACK,
    DELETE_EXPENSE,
) = range(10)


#################### BASIC COMMANDS ####################
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    username = user.username or user.first_name

    # Register group chat id if not already registered
    group_id = update.message.chat.id
    supabase.table("groups").upsert({"id": group_id}).execute()

    await update.message.reply_text(
        f"Hello {username}! I help make splitting bills easier for you and your friends with the convenience of telegram groups!\n\n"
        "Please refer to /help for the available commands to get started."
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "📋 Here's what Splizy can do!\n\n"
        "/register - Register the telegram handles of all participants\n"
        "/add - Add a new expense\n"
        "/addreceipt - Add expense from a receipt photo (coming soon)\n"
        "/view - View all expenses (Can edit and delete from here as well)\n"
        "/settleup - Get settlement recommendations\n"
    )
    await update.message.reply_text(message)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


#################### REGISTER USERS FLOW ####################
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Register group chat id if not already registered
    group_id = update.message.chat.id
    supabase.table("groups").upsert({"id": group_id}).execute()

    msg = "Please enter a list of user telegram handles separated by a space, eg `@user1 @user2 @user3`"
    cur_users = (
        supabase.table("splizy_users")
        .select("*")
        .eq("group_id", group_id)
        .execute()
        .data
    )
    if cur_users:
        usernames = [f"@{user['username']}" for user in cur_users]
        msg += f"\n\nNote: the following users ({', '.join(usernames)}) are already registered and will not be overwritten."
    await update.message.reply_text(msg)
    return REGISTER_USERS


async def register_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        response = update.message.text
        usernames = [username.split("@")[1] for username in response.split(" ")]
        if not usernames:
            await update.message.reply_text(
                "List cannot be empty, please try again, eg `@user1 @user2 @user3`"
            )
            return
        usernames.append(update.effective_user.username)  # Add sender too
        usernames = list(set(usernames))  # Remove duplicates
    except IndexError as e:
        await update.message.reply_text(
            f"Invalid format; please remember to include '@' for each handle, eg `@user1 @user2 @user3`"
        )
        return REGISTER_USERS

    # Only add users that are not already registered
    existing_users = (
        supabase.table("splizy_users")
        .select("*")
        .eq("group_id", update.message.chat.id)
        .execute()
        .data
    )
    existing_usernames = [user["username"] for user in existing_users]
    new_usernames = [
        username for username in usernames if username not in existing_usernames
    ]
    if new_usernames:
        supabase.table("splizy_users").insert(
            [
                {"group_id": update.message.chat.id, "username": username}
                for username in new_usernames
            ]
        ).execute()
        msg = f"Registered the new users: @{', @'.join(new_usernames)}"
    else:
        msg = f"All users are already registered: @{', @'.join(usernames)}"
    await update.message.reply_text(msg)
    return ConversationHandler.END


#################### ADD NEW BILL FLOW ####################
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Let's add a new expense! Tell me what this is for? Eg 'Hotpot dinner'"
    )

    return EXPENSE_NAME


async def expense_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.text:
        await update.message.reply_text("Name cannot be empty, please try again.")
        return EXPENSE_NAME
    context.user_data["expense_name"] = update.message.text

    if "edit_field" in context.user_data:
        await send_confirmation_form(update, context)
        return EXPENSE_CONFIRM

    expense_currency = (
        supabase.table("groups")
        .select("expense_currency")
        .eq("id", update.message.chat.id)
        .execute()
        .data[0]["expense_currency"]
    )
    context.user_data["currency"] = expense_currency
    await update.message.reply_text(
        "How much is it? Enter just the numeric value, eg '50.10'\n\n"
        f"(Expense currency is in {expense_currency}, override by adding currency code in front, eg 'MYR 100')"
    )
    return EXPENSE_AMOUNT


async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    is_valid, result = parse_amount(update.message.text)
    if not is_valid:
        await update.message.reply_text(result)  # result is error msg if invalid
        return EXPENSE_AMOUNT
    currency, amount = result
    if currency:
        context.user_data["currency"] = currency
    context.user_data["amount"] = amount

    if "edit_field" in context.user_data:
        await send_confirmation_form(update, context)
        return EXPENSE_CONFIRM

    await update.message.reply_text(
        f"Who paid for this expense of {context.user_data['currency']} {context.user_data['amount']}? "
        "Please enter the telegram handle, eg `@user1`"
    )
    return EXPENSE_PAID_BY


async def expense_paid_by(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    users = (
        supabase.table("splizy_users")
        .select("username")
        .eq("group_id", update.message.chat.id)
        .execute()
        .data
    )
    usernames = [user["username"] for user in users]
    context.user_data["all_participants"] = usernames
    is_valid, result = parse_username(update.message.text, usernames)
    if not is_valid:
        await update.message.reply_text(result)
        return EXPENSE_PAID_BY
    context.user_data["paid_by"] = result

    if "edit_field" in context.user_data:
        await send_confirmation_form(update, context)
        return EXPENSE_CONFIRM

    keyboard = [
        [
            InlineKeyboardButton(
                "Split equally among all", callback_data="split_equal_all"
            )
        ],
        [
            InlineKeyboardButton(
                "Split equally only among some", callback_data="split_equal_some"
            )
        ],
        [InlineKeyboardButton("Split by custom amounts", callback_data="split_custom")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👥 How do you want to split this expense?", reply_markup=reply_markup
    )
    return EXPENSE_SPLIT_TYPE


async def expense_split_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    split_type = query.data
    if split_type == "split_equal_all":
        context.user_data["is_equal_split"] = True
        context.user_data["split_type"] = "equal_all"

        await send_confirmation_form(update, context, False)
        return EXPENSE_CONFIRM
    elif split_type == "split_equal_some":
        context.user_data["is_equal_split"] = True
        context.user_data["split_type"] = "equal_some"

        # Since entire keyboard has to be rebuilt on every callback, state is managed with a bool array to minimise latency
        # and to preserve ordering of the inline buttons, as opposed to using a adding/removing strings in a string array
        context.user_data["participant_selections"] = [True] * len(
            context.user_data["all_participants"]
        )
        await send_multiselect_users(update, context)
        return EXPENSE_PARTICIPANTS
    elif split_type == "split_custom":
        context.user_data["is_equal_split"] = False
        context.user_data["split_type"] = "custom"
        pass


async def expense_participants(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the selection of participants."""
    query = update.callback_query
    await query.answer()

    if query.data != "participants_done":
        # Toggle participant selection
        index = int(query.data)
        context.user_data["participant_selections"][index] = not context.user_data[
            "participant_selections"
        ][index]

        # Recreate keyboard with updated selection
        await send_multiselect_users(update, context)
        return EXPENSE_PARTICIPANTS

    if not any(context.user_data["participant_selections"]):
        # Recreate keyboard with validation error
        await send_multiselect_users(
            update, context, "Please select at least one participant."
        )
        return EXPENSE_PARTICIPANTS

    # Check if all participants were selected anyway
    selected_participants = [
        username
        for idx, username in enumerate(context.user_data["all_participants"])
        if context.user_data["participant_selections"][idx]
    ]
    if len(selected_participants) == len(context.user_data["all_participants"]):
        context.user_data["split_type"] = "equal_all"
    else:
        context.user_data["selected_participants"] = selected_participants
    await send_confirmation_form(update, context, False)
    return EXPENSE_CONFIRM


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
        "Click on a user to toggle selection. Click 'Done' when finished.\n"
        f"{validation_error if validation_error else ''}",
        reply_markup=reply_markup,
    )


#################### CONFIRM ADD NEW BILL / EDIT EXISTING BILL FLOW  ####################
def get_bill_summary(data):
    if data["split_type"] == "equal_all":
        split_status = f"equally among everyone ({data['currency']} {round(float(data['amount']/len(data['all_participants'])), 2)} per person))"
    elif data["split_type"] == "equal_some":
        selected_participants = data["selected_participants"]
        split_status = f"equally among {len(selected_participants)} people (@{', @'.join(selected_participants)}, {data['currency']} {round(float(data['amount']/len(selected_participants)), 2)} per person)"
    elif data["split_type"] == "custom":
        split_status = "BOOM"

    summary = (
        f"**Bill for {data['expense_name']}**\n"
        f"Paid by: @{data['paid_by']}\n"
        f"Currency & Amount: {data['currency']} {data['amount']}\n"
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
        await update.message.reply_text(
            summary, reply_markup=markup, parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            summary, reply_markup=markup, parse_mode="Markdown"
        )


async def expense_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action != "submit_form" and action != "cancel_form":
        context.user_data["edit_field"] = action

    if action == "edit_expense_name":
        await query.edit_message_text("What is the new name for this expense?")
        return EXPENSE_NAME
    elif action == "edit_amount":
        await query.edit_message_text(
            "Please send the new amount in raw numeric form, or with a currency code in front to override current setting."
        )
        return EXPENSE_AMOUNT
    elif action == "edit_payer":
        await query.edit_message_text(
            "Please enter the telegram handle of the new payer, eg `@user1`"
        )
        return EXPENSE_PAID_BY
    elif action == "edit_split":
        # Ask how to split the expense
        keyboard = [
            [
                InlineKeyboardButton(
                    "Split equally among all", callback_data="split_equal_all"
                )
            ],
            [
                InlineKeyboardButton(
                    "Split equally only among some", callback_data="split_equal_some"
                )
            ],
            [
                InlineKeyboardButton(
                    "Split by custom amounts", callback_data="split_custom"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"👥 How do you want to split this expense?", reply_markup=reply_markup
        )
        return EXPENSE_SPLIT_TYPE
    elif action == "cancel_form":
        if "expenses" not in context.user_data:
            await query.edit_message_text("Operation cancelled.")
            return ConversationHandler.END
        await send_all_expenses(update, context, False)
        return VIEW_EXPENSE

    elif action == "submit_form":
        data = context.user_data
        entry = {
            "group_id": query.message.chat.id,
            "title": data["expense_name"],
            "amount": float(data["amount"]),  # Decimal is not JSON serializable
            "paid_by": data["paid_by"],
            "currency": data["currency"],
            "is_equal_split": data["is_equal_split"],
        }
        # NOTE: look into implementing transactions with supabase.table().rpc() in future if needed; for now
        # things are simple enough that failures are unlikely / manual rollbacks are manageable, so no need
        # to overengineer at the moment
        try:
            if "expense_id" in data:
                # If editing existing expense, delete all outdated user_expenses firstm and update expense
                supabase.table("user_expenses").delete().eq(
                    "expense_id", data["expense_id"]
                ).execute()
                supabase.table("expenses").update(entry).eq(
                    "id", data["expense_id"]
                ).execute()
            else:
                # Else create new expense and record its expense_id
                new_expense_id = (
                    supabase.table("expenses").insert(entry).execute().data[0]["id"]
                )
                data["expense_id"] = new_expense_id
            # Then create new user_expenses
            if data["split_type"] == "equal_all" or data["split_type"] == "equal_some":
                participants = (
                    data["all_participants"]
                    if data["split_type"] == "equal_all"
                    else data["selected_participants"]
                )
                amount_per_pax = float(data["amount"] / len(participants))
                supabase.table("user_expenses").insert(
                    [
                        {
                            "username": username,
                            "group_id": query.message.chat.id,
                            "expense_id": data["expense_id"],
                            "amount": amount_per_pax,
                        }
                        for username in participants
                    ]
                ).execute()
            await query.edit_message_text(
                f"Expense for {data['expense_name']} saved successfully!"
            )
            context.user_data.clear()
            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Failed to add / edit expense: {e}")
            await query.edit_message_text(
                "Failed to add / edit expense, please check logs."
            )
            context.user_data.clear()
            return ConversationHandler.END

    return EXPENSE_CONFIRM


#################### VIEW BILLS FLOW  ####################
async def view_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_id = update.message.chat.id
    expenses = (
        supabase.table("expenses")
        .select("*")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    if not expenses:
        await update.message.reply_text("No expenses logged yet.")
        return ConversationHandler.END
    context.user_data["expenses"] = expenses

    await send_all_expenses(update, context)
    return VIEW_EXPENSE


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
    text = f"All logged expenses so far\n(title | payer | amount):\n\n"
    if is_new_msg:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def view_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    index = int(query.data)
    expense = context.user_data["expenses"][index]
    group_id = query.message.chat.id

    if expense["is_equal_split"]:
        user_expenses = (
            supabase.table("user_expenses")
            .select("*")
            .eq("expense_id", expense["id"])
            .execute()
            .data
        )
        users = (
            supabase.table("splizy_users")
            .select("username")
            .eq("group_id", group_id)
            .execute()
            .data
        )
        context.user_data["split_type"] = (
            "equal_some" if len(user_expenses) < len(users) else "equal_all"
        )
        context.user_data["all_participants"] = [user["username"] for user in users]
        context.user_data["selected_participants"] = [
            ue["username"] for ue in user_expenses
        ]
    else:
        context.user_data["split_type"] = "custom"

    context.user_data["expense_id"] = expense[
        "id"
    ]  # Signals an edit flow in expense_confirm
    context.user_data["expense_name"] = expense["title"]
    context.user_data["amount"] = expense["amount"]
    context.user_data["paid_by"] = expense["paid_by"]
    context.user_data["currency"] = expense["currency"]
    context.user_data["is_equal_split"] = expense["is_equal_split"]

    summary = get_bill_summary(context.user_data)
    keyboard = [
        [
            InlineKeyboardButton("Edit", callback_data="edit_expense"),
            InlineKeyboardButton("Delete", callback_data="delete_expense"),
        ],
        [InlineKeyboardButton("Go back", callback_data="go_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        summary, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return EDIT_OR_GO_BACK


async def edit_or_go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "edit_expense":
        await send_confirmation_form(update, context, False)
        return EXPENSE_CONFIRM
    elif action == "delete_expense":
        data = context.user_data
        keyboard = [
            [
                InlineKeyboardButton("❌ No", callback_data="cancel_delete"),
                InlineKeyboardButton("✅ Yes", callback_data="confirm_delete"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=(
                f"Are you sure you want to delete this expense?\n({data['expense_name']} | {data['paid_by']} | {data['currency']} {data['amount']})\n"
                "This action cannot be undone."
            ),
            reply_markup=reply_markup,
        )
        return DELETE_EXPENSE
    else:
        await send_all_expenses(update, context, False)
        return VIEW_EXPENSE


#################### DELETE BILLS FLOW  ####################
async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "confirm_delete":
        expense_id = context.user_data["expense_id"]
        supabase.table("expenses").delete().eq(
            "id", expense_id
        ).execute()  # Cascade deletes user_expenses
        await query.edit_message_text("Expense deleted successfully.")
        context.user_data.clear()
        return ConversationHandler.END
    elif action == "cancel_delete":
        await send_all_expenses(update, context, False)
        return VIEW_EXPENSE

    return ConversationHandler.END


######################################################################


def main() -> None:
    """Start the bot."""
    # Initialize the bot
    app = ApplicationBuilder().token(TELEBOT_TOKEN).build()

    # Define conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            CommandHandler("register", register_command),
            CommandHandler("add", add_command),
            CommandHandler("view", view_all_command),
        ],
        states={
            REGISTER_USERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_users)
            ],
            EXPENSE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_name)
            ],
            EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)
            ],
            EXPENSE_PAID_BY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_paid_by)
            ],
            EXPENSE_SPLIT_TYPE: [CallbackQueryHandler(expense_split_type)],
            EXPENSE_PARTICIPANTS: [CallbackQueryHandler(expense_participants)],
            EXPENSE_SPLIT_TYPE: [CallbackQueryHandler(expense_split_type)],
            EXPENSE_CONFIRM: [CallbackQueryHandler(expense_confirm)],
            VIEW_EXPENSE: [CallbackQueryHandler(view_expense)],
            EDIT_OR_GO_BACK: [CallbackQueryHandler(edit_or_go_back)],
            DELETE_EXPENSE: [CallbackQueryHandler(delete_expense)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    # Start the webhook
    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
            secret_token=SECRET_TOKEN,
        )
    else:
        # Fallback to polling
        app.run_polling()


if __name__ == "__main__":
    main()
